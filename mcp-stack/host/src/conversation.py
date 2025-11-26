"""Conversation handling for MCP Host with rule-based intent classification.

This module provides a conversation handler that converts natural language queries
into structured MCP queries using rule-based intent classification.
"""
import re
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from .intent_classifier import QueryIntent, intent_classifier

class QueryParameters(BaseModel):
    """Parameters extracted from user query."""
    intent: Optional[QueryIntent] = None
    customer_id: Optional[str] = None
    search_terms: List[str] = []
    limit: int = 10
    offset: int = 0
    filters: Dict[str, Any] = {}

class ConversationHandler:
    """Handles natural language conversations and converts them to MCP queries."""

    def __init__(self):
        # Templates for different intents
        self.intent_templates = {
            QueryIntent.HEALTH_CHECK: {
                "intent": "health_check"
            },
            QueryIntent.LIST_CUSTOMERS: {
                "source_id": "customers",
                "limit": 10,
                "filters": {}
            },
            QueryIntent.GET_CUSTOMER: {
                "source_id": "customers",
                "filters": {"customerId": "{customer_id}"}
            },
            QueryIntent.LIST_TRANSCRIPTS: {
                "source_id": "transcripts",
                "limit": 10,
                "filters": {}
            },
            QueryIntent.GET_TRANSCRIPT: {
                "source_id": "transcripts",
                "filters": {"callId": "{call_id}"}
            },
            QueryIntent.SEARCH: {
                "source_id": "customers",
                "filters": {"search": "{search_term}"}
            }
        }

    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a natural language query and return query parameters.

        Args:
            query: The natural language query to process

        Returns:
            A dictionary containing the structured query parameters or None if no intent matched

        Raises:
            ValueError: If required parameters are missing from the query
        """
        # Classify the intent of the query
        intent, confidence = intent_classifier.classify_intent(query)

        # If no intent matched or confidence is too low
        if intent is None or confidence < 0.5:
            return None

        # Extract parameters based on intent
        if intent == QueryIntent.HEALTH_CHECK:
            return self._create_health_check_query()

        elif intent == QueryIntent.LIST_CUSTOMERS:
            return self._create_list_query("customers")

        elif intent == QueryIntent.GET_CUSTOMER:
            # Try to extract customer ID from query
            customer_id = self._extract_customer_id(query)
            if not customer_id:
                raise ValueError("No customer ID found in query")
            return self._create_get_customer_query(customer_id)

        elif intent == QueryIntent.LIST_TRANSCRIPTS:
            return self._create_list_query("transcripts")

        elif intent == QueryIntent.GET_TRANSCRIPT:
            # Try to extract call ID from query
            call_id = self._extract_call_id(query)
            if not call_id:
                raise ValueError("No call ID found in query")
            return self._create_get_transcript_query(call_id)

        elif intent == QueryIntent.SEARCH:
            search_terms = self._extract_search_terms(query)
            if not search_terms:
                raise ValueError("No search terms found in query")
            return self._create_search_query(search_terms)

        return None

    def _extract_entities(self, query: str, intent: QueryIntent) -> Dict[str, str]:
        """Extract entities from the query based on the detected intent."""
        entities = {}

        # Extract customer IDs (e.g., CUST123)
        if intent == QueryIntent.GET_CUSTOMER:
            customer_match = re.search(r'CUST\d+', query, re.IGNORECASE)
            if customer_match:
                entities['customer_id'] = customer_match.group(0)

        # Extract call IDs (e.g., CALL123)
        elif intent == QueryIntent.GET_TRANSCRIPT:
            call_match = re.search(r'CALL\d+', query, re.IGNORECASE)
            if call_match:
                entities['call_id'] = call_match.group(0)

        # Extract search terms
        elif intent == QueryIntent.SEARCH:
            # Remove common search terms to get the actual search query
            search_query = query
            for term in ['search', 'find', 'for', 'customer', 'customers', 'named', 'called', 'with', 'email', 'phone']:
                search_query = re.sub(rf'\b{re.escape(term)}\b', '', search_query, flags=re.IGNORECASE)
            search_query = search_query.strip()
            if search_query:
                entities['search_term'] = search_query

        return entities

    def parse_query(self, query: str) -> QueryParameters:
        """
        Parse a natural language query into structured parameters using AI.

        Args:
            query: The user's natural language query

        Returns:
            QueryParameters object with the detected intent and extracted parameters
        """
        query = query.strip()
        if not query:
            return QueryParameters(intent=QueryIntent.UNKNOWN)

        # Use AI to classify the intent
        intent, confidence = intent_classifier.classify_intent(query)

        # Initialize parameters with default values
        params = QueryParameters(
            intent=intent,
            search_terms=query.split()
        )

        # If we have a valid intent, extract entities and apply template
        if intent != QueryIntent.UNKNOWN and intent in self.intent_templates:
            # Extract entities based on intent
            entities = self._extract_entities(query, intent)

            # Get the template for this intent
            template = self.intent_templates[intent].copy()

            # Apply template values
            if "source_id" in template:
                params.filters["source_id"] = template["source_id"]
            if "limit" in template:
                params.limit = template["limit"]

            # Format filters with extracted entities
            if "filters" in template:
                for key, value in template["filters"].items():
                    try:
                        params.filters[key] = value.format(**entities)
                    except (KeyError, AttributeError):
                        # If we can't format the value, use it as-is
                        params.filters[key] = value

            # Set additional parameters from entities
            if 'customer_id' in entities:
                params.customer_id = entities['customer_id']
            if 'search_term' in entities:
                params.search_terms = [entities['search_term']]

        return params

    async def format_response(self, intent: QueryIntent, data: Dict) -> str:
        """Format the response based on the intent and data."""
        try:
            # Handle case when no intent is matched
            if intent is None:
                return (
                    "I'm sorry, I couldn't identify your intent. "
                    "Here are some examples of what I can help with:\n"
                    "- 'Show me all customers'\n"
                    "- 'Get details for customer CUST1000'\n"
                    "- 'List recent call transcripts'\n"
                    "- 'Find customer with email example@domain.com'\n"
                    "- 'Is the server healthy?'"
                )

            if intent == QueryIntent.HEALTH_CHECK:
                if data and (data.get("status") == "ok" or data.get("status") == "healthy"):
                    return "The server is up and running! 🟢"
                else:
                    return "I'm having trouble reaching the server. It might be down. 🔴"

            elif intent == QueryIntent.LIST_CUSTOMERS:
                if not data:
                    return "I couldn't retrieve any customer data."

                items = data.get("items", [])
                if not items:
                    return "I couldn't find any matching customer records."

                customer_list = "\n".join(
                    f"- {item.get('data', {}).get('firstName', 'Unknown')} "
                    f"{item.get('data', {}).get('lastName', '')} "
                    f"({item.get('data', {}).get('email', 'no email')})"
                    for item in items if isinstance(item, dict)
                )
                return f"Here are the customers I found:\n{customer_list}"

            elif intent == QueryIntent.GET_CUSTOMER:
                if not data or not isinstance(data, dict):
                    return "I couldn't retrieve the customer data."

                if "items" in data:
                    items = data["items"]
                    if not items:
                        return "I couldn't find a customer with that ID."
                    customer = items[0].get("data", {})
                    return (
                        f"Customer {customer.get('customerId', 'N/A')}:\n"
                        f"Name: {customer.get('firstName', '')} {customer.get('lastName', '')}\n"
                        f"Email: {customer.get('email', 'N/A')}\n"
                        f"Phone: {customer.get('phone', 'N/A')}"
                    )
                return "I couldn't find the customer data in the response."

            elif intent == QueryIntent.LIST_TRANSCRIPTS:
                if not data or not isinstance(data, dict) or not data.get("items"):
                    return "I couldn't retrieve any call transcripts."

                items = data.get("items", [])
                if not items:
                    return "I couldn't find any call transcripts."

                transcript_list = "\n".join(
                    f"- Call {item.get('data', {}).get('callId', 'unknown')} "
                    f"({item.get('data', {}).get('callTimestamp', 'no date')}): "
                    f"{item.get('data', {}).get('callSummary', 'No summary')}"
                    for item in items if isinstance(item, dict)
                )
                return f"Here are the call transcripts I found:\n{transcript_list}"

            elif intent == QueryIntent.SEARCH:
                if not data or not isinstance(data, dict) or not data.get("items"):
                    return "I couldn't find any matching results for your search."

                items = data.get("items", [])
                if not items:
                    return "I couldn't find any matching results for your search."

                # Check if this is customer data or transcript data
                if items and isinstance(items[0], dict) and "data" in items[0] and "customerId" in items[0]["data"]:
                    return await self.format_response(QueryIntent.LIST_CUSTOMERS, data)
                return await self.format_response(QueryIntent.LIST_TRANSCRIPTS, data)

            return f"Here's what I found: {data}"
        except Exception as e:
            return f"I'm sorry, I encountered an error formatting the response: {str(e)}"
