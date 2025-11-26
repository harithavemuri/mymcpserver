"""AI-based intent classification for natural language queries.

This module provides a rule-based intent classifier that can be used to classify
natural language queries into predefined intents. It includes a fallback mechanism
that can use a machine learning model if available, but defaults to a rule-based
approach for reliability.
"""
from typing import Dict, List, Tuple
from enum import Enum

class QueryIntent(str, Enum):
    """Supported query intents."""
    LIST_CUSTOMERS = "list_customers"
    GET_CUSTOMER = "get_customer"
    LIST_TRANSCRIPTS = "list_transcripts"
    GET_TRANSCRIPT = "get_transcript"
    SEARCH = "search"
    HEALTH_CHECK = "health_check"
    UNKNOWN = "unknown"

class AIIntentClassifier:
    """AI-based intent classifier using sentence transformers."""

    def __init__(self):
        """Initialize the intent classifier with the rule-based approach."""
        self.intent_examples = self._get_intent_examples()

    def _get_intent_examples(self) -> Dict[str, List[str]]:
        """Get example queries for each intent."""
        return {
            QueryIntent.HEALTH_CHECK: [
                "check server status",
                "is the server up",
                "verify server health",
                "is the server running",
                "server status",
                "how's the server doing",
                "how are you?",
                "is the server healthy"
            ],
            QueryIntent.LIST_CUSTOMERS: [
                "show me all customers",
                "list customers",
                "who are the customers",
                "get customer list",
                "show customer directory"
            ],
            QueryIntent.GET_CUSTOMER: [
                "show me customer CUST123",
                "get details for customer CUST456",
                "who is customer CUST789",
                "customer CUST101 info"
            ],
            QueryIntent.LIST_TRANSCRIPTS: [
                "show me all transcripts",
                "list call transcripts",
                "get transcript history",
                "show previous calls"
            ],
            QueryIntent.GET_TRANSCRIPT: [
                "show me transcript CALL123",
                "get call CALL456",
                "what was said in call CALL789",
                "transcript for CALL101"
            ],
            QueryIntent.SEARCH: [
                "find customer John",
                "search for customers in New York",
                "who is john@example.com",
                "find calls about billing"
            ]
        }


    def classify_intent(self, query: str, threshold: float = 0.6) -> Tuple[QueryIntent, float]:
        """Classify the intent of a natural language query using a rule-based approach.

        Args:
            query: The natural language query to classify
            threshold: Minimum confidence score (unused in rule-based approach, kept for compatibility)

        Returns:
            A tuple of (intent, confidence_score) where confidence_score is always 1.0 for rule-based
            Returns (None, 0.0) if no intent can be determined
        """

        # Rule-based approach
        query = query.lower()

        # Check for health check queries
        health_terms = ['health', 'status', 'alive', 'running', 'up', 'down', 'server']
        if any(term in query for term in health_terms):
            return QueryIntent.HEALTH_CHECK, 1.0

        # Check for customer-related queries
        customer_terms = ['customer', 'client', 'buyer', 'purchaser']
        if any(term in query for term in customer_terms):
            if 'list' in query or 'all' in query or 'show' in query:
                return QueryIntent.LIST_CUSTOMERS, 1.0
            else:
                return QueryIntent.GET_CUSTOMER, 1.0

        # Check for transcript-related queries
        transcript_terms = ['transcript', 'call', 'recording', 'conversation']
        if any(term in query for term in transcript_terms):
            if 'list' in query or 'all' in query or 'show' in query:
                return QueryIntent.LIST_TRANSCRIPTS, 1.0
            else:
                return QueryIntent.GET_TRANSCRIPT, 1.0

        # Check for search queries
        search_terms = ['find', 'search', 'look for', 'who is', 'show me']
        if any(term in query for term in search_terms):
            return QueryIntent.SEARCH, 0.9

        # No intent matched
        return None, 0.0

# Singleton instance
intent_classifier = AIIntentClassifier()
