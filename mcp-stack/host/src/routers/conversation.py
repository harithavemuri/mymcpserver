"""
Conversation router for handling dynamic client routing based on conversation context.
"""
import asyncio
import re
from fastapi import APIRouter, HTTPException, Depends, Body, Query
from typing import Dict, Any, Optional, List, Union, Set, Coroutine, Awaitable
import json
import logging
import uuid
from pydantic import BaseModel, Field
import sys
import os

# Add the client source directory to the path
client_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'client', 'src'))
if client_src_dir not in sys.path:
    sys.path.insert(0, client_src_dir)

# Now import the client
from client import MCPClient

from ..text_transform import text_transform_client

router = APIRouter(prefix="/conversation", tags=["conversation"])
logger = logging.getLogger(__name__)

class ConversationMessage(BaseModel):
    """A message in the conversation."""
    role: str = Field(..., description="The role of the message sender (user, assistant, system)")
    content: str = Field(..., description="The content of the message")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

class ConversationRequest(BaseModel):
    """Request model for processing a conversation message."""
    messages: List[ConversationMessage] = Field(..., description="List of messages in the conversation")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context for the conversation")

class ConversationResponse(BaseModel):
    """Response model for conversation processing."""
    response: str = Field(..., description="The generated response")
    client_used: str = Field(..., description="The client that processed the request")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the processing")
    data: Optional[List[Dict[str, Any]]] = Field(default=None, description="Raw data from the operation, if available")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context data for the conversation")

# Map of intents to client handlers
INTENT_HANDLERS = {
    "customer": {
        "keywords": ["customer", "client", "show customers", "list customers", "find customer", "search customer"],
        "handler": "handle_customer_request"
    },
    "text_transform": {
        "keywords": ["uppercase", "lowercase", "capitalize", "reverse", "title case", "transform", "convert"],
        "handler": "handle_text_transform"
    },
}

# Initialize MCP client with explicit configuration to avoid environment variable conflicts
mcp_client = MCPClient(
    server_url="http://localhost:8005",
    timeout=30,
    max_retries=3
)

async def detect_intents(text: str) -> List[Dict[str, Any]]:
    """
    Detect all possible intents from the user's message.

    Returns:
        List of dicts with 'intent' and 'confidence' for each detected intent
    """
    text_lower = text.lower()
    detected_intents = []

    for intent, config in INTENT_HANDLERS.items():
        # Count how many keywords match for this intent
        matches = sum(1 for keyword in config["keywords"] if keyword in text_lower)
        if matches > 0:
            # Calculate confidence based on number of keyword matches
            confidence = min(0.3 + (matches * 0.2), 0.9)  # Cap at 0.9 to allow for manual override
            detected_intents.append({
                "intent": intent,
                "confidence": confidence,
                "handler": config["handler"]
            })

    # Sort by confidence (highest first)
    return sorted(detected_intents, key=lambda x: x["confidence"], reverse=True)

async def handle_text_transform(message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle text transformation requests with support for chained operations.

    Args:
        message: The user's message
        context: Dictionary containing context, including 'customer_emails' if available

    Returns:
        Dictionary with the transformed text and metadata
    """
    try:
        # Check if we have customer emails in the context
        if context and "customer_emails" in context and context["customer_emails"]:
            # If we have multiple emails, join them with newlines for better formatting
            if isinstance(context["customer_emails"], list):
                text_to_transform = "\n".join(context["customer_emails"])
            else:
                text_to_transform = str(context["customer_emails"])
            is_customer_emails = True
        else:
            # Extract the text to transform (remove the command part)
            text_to_transform = message
            is_customer_emails = False

        # Remove common phrases to isolate the text to transform
        remove_phrases = INTENT_HANDLERS["text_transform"]["keywords"] + [
            "please", "can you", "could you", "make this", "convert this",
            "to", "and then", "and", "the", "it", "text", "transform", "change"
        ]

        for phrase in remove_phrases:
            text_to_transform = text_to_transform.replace(phrase, "")

        # Clean up the text
        text_to_transform = ' '.join(word for word in text_to_transform.split() if word not in ['', ' '])

        # If no text remains, try to extract the text after the last colon
        if not text_to_transform and ":" in message:
            text_to_transform = message.split(":", 1)[1].strip()

        if not text_to_transform:
            return {
                "response": "I need some text to transform. Please provide the text you'd like to transform.",
                "client_used": "text_transform",
                "metadata": {"status": "no_text_provided"}
            }

        # Determine operations to perform
        operations = []
        message_lower = message.lower()

        # Check for multiple operations
        if "and" in message_lower or "then" in message_lower:
            if "uppercase" in message_lower or "upper case" in message_lower:
                operations.append("uppercase")
            if "lowercase" in message_lower or "lower case" in message_lower:
                operations.append("lowercase")
            if "title" in message_lower or "title case" in message_lower:
                operations.append("title")
            if "reverse" in message_lower:
                operations.append("reverse")
            if "strip" in message_lower:
                operations.append("strip")

        # If no operations detected, try to determine from the message
        if not operations:
            if any(op in message_lower for op in ["lowercase", "lower case"]):
                operations.append("lowercase")
            elif any(op in message_lower for op in ["title", "title case"]):
                operations.append("title")
            elif "reverse" in message_lower:
                operations.append("reverse")
            elif "strip" in message_lower:
                operations.append("strip")
            else:
                # Default to uppercase if no specific operation is mentioned
                operations.append("uppercase")

        # Apply transformations in sequence
        current_text = text_to_transform
        applied_operations = []

        for operation in operations:
            result = await text_transform_client.transform(current_text, operation=operation)
            current_text = result.transformed
            applied_operations.append(operation)

        # Prepare the response
        if len(applied_operations) > 1:
            ops_text = ", ".join(applied_operations[:-1]) + f" and {applied_operations[-1]}"
            response = f"Here's your text after applying {ops_text}: {current_text}"
        else:
            response = f"Here's your {applied_operations[0]} text: {current_text}"

        return {
            "response": response,
            "client_used": "text_transform",
            "metadata": {
                "operations": applied_operations,
                "original_text": text_to_transform,
                "transformed_text": current_text
            }
        }
    except Exception as e:
        logger.error(f"Error in text transform handler: {e}")
        return {
            "response": "I encountered an error processing your text transformation request.",
            "client_used": "text_transform",
            "metadata": {"error": str(e), "status": "error"}
        }

async def format_customer_response(
    customers: List[Dict[str, Any]],
    message: str,
    requested_fields: set = None,
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Format customer data based on the requested fields.

    This is an async function that may perform I/O operations.

    Args:
        customers: List of customer dictionaries
        message: Original message from the user
        requested_fields: Set of fields to include in the response
        context: Additional context including detected intents and other metadata

    Returns:
        Dict containing:
        - response: Formatted string response
        - client_used: Client identifier
        - metadata: Response metadata
        - data: Raw customer data with transformations applied
    """
    if not customers:
        return {
            "response": "No customers found.",
            "client_used": "customer",
            "metadata": {"count": 0},
            "data": []
        }

    # Initialize context if not provided
    context = context or {}

    # If no specific fields requested, use all available fields from the first customer
    if not requested_fields and customers:
        requested_fields = set(customers[0].keys())

    # Ensure we have a set
    requested_fields = set(requested_fields) if requested_fields else set()

    # Always include ID for reference if available in the data
    if customers and ('id' in customers[0] or 'customerId' in customers[0]):
        requested_fields.update(['id', 'customerId'])

    # Create a copy of customers to avoid modifying the original data
    processed_customers = []

    response_lines = []
    customer_ids = []

    for i, customer in enumerate(customers, 1):
        # Create a copy of the customer data to modify
        processed_customer = customer.copy()

        # Always include ID if available
        customer_id = processed_customer.get('id') or processed_customer.get('customerId')
        if customer_id:
            customer_ids.append(str(customer_id))

        # Build customer info line
        info_parts = []

        # Add ID if available
        if customer_id:
            info_parts.append(f"[ID: {customer_id}]")

        # Process name field
        if 'name' in requested_fields:
            name = processed_customer.get('name')
            if not name and ('firstName' in processed_customer or 'lastName' in processed_customer):
                name = f"{processed_customer.get('firstName', '')} {processed_customer.get('lastName', '')}".strip()
                processed_customer['name'] = name
            if name:
                info_parts.append(f"Name: {name}")

        # Process email field
        if 'email' in requested_fields and 'email' in processed_customer and processed_customer['email']:
            email = processed_customer['email']
            info_parts.append(f"Email: {email}")

        # Process phone field (with uppercase conversion)
        if 'phone' in requested_fields and 'phone' in processed_customer and processed_customer['phone']:
            phone = processed_customer['phone']
            if isinstance(phone, str):
                phone = phone.upper()
                processed_customer['phone'] = phone  # Apply transformation to the data
            info_parts.append(f"Phone: {phone}")

        # Process other requested fields
        other_fields = requested_fields - {'name', 'email', 'phone', 'id', 'customerId', 'firstName', 'lastName'}
        for field in sorted(other_fields):
            if field in processed_customer and processed_customer[field] is not None:
                value = processed_customer[field]
                if isinstance(value, (str, list, dict)) and not value:
                    continue

                display_name = ' '.join(word.capitalize() for word in field.replace('_', ' ').split())
                if isinstance(value, (list, dict)):
                    value_str = json.dumps(value, indent=2) if value else str(value)
                    info_parts.append(f"{display_name}: {value_str}")
                else:
                    info_parts.append(f"{display_name}: {value}")

        # Add customer number and join info parts for the response line
        if info_parts:
            response_lines.append(f"{i}. {' - '.join(info_parts)}")
        else:
            response_lines.append(f"{i}. No information available")

        # Add the processed customer to our list
        processed_customers.append(processed_customer)

    # Prepare the response
    response = f"Found {len(processed_customers)} customers:"
    response += "\n" + "\n".join(response_lines) if response_lines else " (no details available)"

    # Prepare metadata
    metadata = {
        "count": len(processed_customers),
        "customer_ids": customer_ids,
        "requested_fields": list(requested_fields) if requested_fields else []
    }

    # Add detected intents if available in context
    if 'detected_intents' in context:
        metadata['detected_intents'] = context['detected_intents']

    # Initialize response_format
    response_format = context.get('response_format', {}) if context else {}

    # Check if we have a custom response format in context
    if isinstance(response_format, dict) and 'template' in response_format:
        try:
            # Format the response using the provided template
            response = response_format['template'].format(
                response=response,
                count=len(processed_customers),
                customer_ids=metadata['customer_ids'],
                **context
            )
        except (KeyError, IndexError) as e:
            logger.error(f"Error formatting response with template: {e}")
            logger.warning("Failed to format response with template", exc_info=True)
            response = '\n'.join(response_lines)
    else:
        response = '\n'.join(response_lines)

    # Apply style if specified
    style = response_format.get('style')
    if style == 'list' and isinstance(response, str):
        response = '\n'.join(f"- {line}" for line in response.split('\n') if line.strip())
    elif style == 'json':
        response = json.dumps({"response": response, "metadata": metadata, "data": processed_customers}, indent=2)

    # Add any additional context to metadata
    if context:
        metadata.update({k: v for k, v in context.items() if k != 'response_format'})

    # Filter each customer to only include requested fields in the data element
    filtered_customers = []
    transform_operations = context.get('transform_operations', [])
    transform_fields = context.get('transform_fields', [])

    for customer in processed_customers:
        filtered_customer = {}
        for field in requested_fields:
            if field in customer and customer[field] is not None:
                value = customer[field]

                # Apply transformations if this is a text field and has transform operations
                if field in transform_fields and transform_operations and isinstance(value, str):
                    try:
                        current_value = value
                        # Apply each transformation in sequence
                        for operation in transform_operations:
                            result = await text_transform_client.transform(current_value, operation=operation)
                            current_value = result.transformed
                            logger.debug(f"Applied {operation} to {field}: {value[:20]}... -> {current_value[:20]}...")
                        filtered_customer[field] = current_value
                    except Exception as e:
                        logger.error(f"Error transforming {field}: {e}")
                        filtered_customer[field] = value
                else:
                    filtered_customer[field] = value
            # Handle special field mappings
            elif field == 'id' and 'customerId' in customer:
                filtered_customer['id'] = customer['customerId']
            elif field == 'customerId' and 'id' in customer:
                filtered_customer['customerId'] = customer['id']


        filtered_customers.append(filtered_customer)

    # Return both the formatted response and the filtered raw data
    return {
        "context": context,
        "response": response,
        "client_used": "customer",
        "metadata": metadata,
        "data": filtered_customers
    }

async def get_available_fields() -> Dict[str, List[Dict[str, Any]]]:
    """Fetch available fields from the GraphQL schema."""
    # These are the fields we know about from the search_customers method
    known_fields = {
        'id': [
            {'match': 'exact', 'terms': ['customer id']},
            {'match': 'word', 'terms': ['id']}
        ],
        'firstName': [
            {'match': 'exact', 'terms': ['first name']},
            {'match': 'word', 'terms': ['first', 'firstname']}
        ],
        'lastName': [
            {'match': 'exact', 'terms': ['last name']},
            {'match': 'word', 'terms': ['last', 'lastname', 'surname']}
        ],
        'email': [
            {'match': 'exact', 'terms': ['email', 'e-mail', 'mail']},
            {'match': 'word', 'terms': ['email']}
        ],
        'phone': [
            {'match': 'exact', 'terms': ['contact number', 'phone number', 'phone numbers', 'contact info', 'phone no', 'phone #']},
            {'match': 'word', 'terms': ['phone', 'telephone', 'mobile', 'cell', 'cellphone', 'contact']},
            {'match': 'partial', 'terms': ['phone', 'mobile', 'cell']}
        ],
        'address': [
            {'match': 'word', 'terms': ['address', 'location', 'street']}
        ],
        'city': [
            {'match': 'word', 'terms': ['city', 'town']}
        ],
        'state': [
            {'match': 'exact', 'terms': ['state code', 'province code']},
            {'match': 'word', 'terms': ['state', 'province', 'region']}
        ],
        'zipCode': [
            {'match': 'exact', 'terms': ['postal code', 'zip code']},
            {'match': 'word', 'terms': ['zip', 'postal']}
        ],
        'country': [
            {'match': 'word', 'terms': ['country', 'nation']}
        ]
    }

    # Add name as a combination of first and last name
    known_fields['name'] = [
        {'match': 'exact', 'terms': ['customer name', 'full name']},
        {'match': 'word', 'terms': ['name']}
    ]

    # Add transcripts as a special field
    known_fields['transcripts'] = [
        {'match': 'exact', 'terms': ['call transcripts', 'conversation history']},
        {'match': 'word', 'terms': ['transcript', 'conversation', 'chat', 'call', 'calls']}
    ]
    logger.debug(f"Known Fields: {known_fields}")
    return known_fields

async def get_requested_fields(message: str) -> set:
    """Determine which fields are being requested in the message."""
    message_lower = message.lower()
    fields = set()

    # Get the field mapping with all known fields
    field_mapping = await get_available_fields()

    # Add debug logging for the field mapping
    logger.debug(f"Available fields in schema: {list(field_mapping.keys())}")

    logger.debug(f"Original message: {message}")
    logger.debug(f"Message lower: {message_lower}")

    # Split message into words and n-grams for better matching
    words = message_lower.split()
    ngrams = []
    for n in range(1, 4):  # 1-3 word n-grams
        ngrams.extend([' '.join(words[i:i+n]) for i in range(len(words)-n+1)])

    # Look for field names in the message
    logger.debug(f"All n-grams: {ngrams}")
    logger.debug(f"All words: {words}")

    for field, match_rules in field_mapping.items():
        field_found = False
        logger.debug(f"Checking field: {field} with rules: {match_rules}")

        for rule in match_rules:
            match_type = rule['match']
            terms = rule['terms']
            logger.debug(f"  Checking rule: {match_type} with terms: {terms}")

            for term in terms:
                if match_type == 'exact':
                    # Check for exact match in n-grams
                    if term in ngrams:
                        logger.debug(f"    Exact match for field '{field}' with term: '{term}'")
                        fields.add(field)
                        field_found = True
                        break
                elif match_type == 'word':
                    # Check for whole word match
                    if term in words:
                        logger.debug(f"    Word match for field '{field}' with term: '{term}'")
                        fields.add(field)
                        field_found = True
                        break
                elif match_type == 'partial':
                    # Check for partial match in any word
                    matched_words = [word for word in words if term in word]
                    if matched_words:
                        logger.debug(f"    Partial match for field '{field}' with term: '{term}' in words: {matched_words}")
                        fields.add(field)
                        field_found = True
                        break

                if field_found:
                    break
            if field_found:
                break

    logger.debug(f"Final fields before defaults: {fields}")

    # Special case: if 'transcripts' is explicitly requested, don't add other fields
    if 'transcripts' in fields:
        logger.debug("Transcripts explicitly requested, returning only transcripts")
        return {'transcripts'}

    # Always include 'id' if we have any fields
    if fields and 'id' not in fields:
        fields.add('id')
        logger.debug("Added 'id' to requested fields")

    # If we have specific fields but no name/email, add them if they were explicitly requested
    if fields:
        # Check if 'email' or 'state' were in the original message
        if 'email' not in fields and any(word in message_lower for word in ['email', 'e-mail', 'mail']):
            fields.add('email')
            logger.debug("Added 'email' based on message content")

        if 'state' not in fields and any(word in message_lower for word in ['state', 'province', 'region']):
            fields.add('state')
            logger.debug("Added 'state' based on message content")

    # If still no fields, use defaults
    if not fields:
        logger.debug("No specific fields found, using defaults: name, email")
        return {'name', 'email'}

    logger.debug(f"Returning fields: {fields}")
    return fields

async def handle_customer_request(
    message: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Handle customer-related requests, fetching only necessary columns.

    Args:
        message: The user's message
        context: Additional context including detected intents and other metadata
        requested_fields: Optional set of fields to include in the response
    """
    try:
        logger.debug(f"Handling customer request. Message: '{message}'")
        logger.debug(f"Context keys: {list(context.keys()) if context else 'No context'}")


        # If still not available, parse from message
        requested_fields = await get_requested_fields(message)

        logger.debug(f"Final requested fields: {requested_fields}")

        # Check if this is a follow-up request to transform emails
        if any(word in message.lower() for word in ["uppercase", "lowercase", "title", "reverse", "transform"]):
            logger.debug("Detected text transformation request")
            # If we have emails in context, use them for transformation
            if context and "customer_emails" in context:
                logger.debug(f"Found {len(context['customer_emails'])} emails in context for transformation")
                # Pass the context to handle_text_transform
                return await handle_text_transform(message, context)

        # Determine which fields are needed
        requested_fields = await get_requested_fields(message)

        # Check if this is a search query
        if any(word in message.lower() for word in ["find", "search", "look up"]):
            logger.debug("Processing search query")
            # Extract search query (everything after the search term)
            search_terms = ["find", "search", "look up", "for", "show", "list"]
            query = message.lower()
            for term in search_terms:
                if term in query:
                    query = query.split(term, 1)[-1].strip()
                    break
            logger.debug(f"Extracted search query: '{query}'")

            # Map requested fields to match the GraphQL schema
            field_mapping = {
                'id': 'id',
                'customerId': 'id',  # Alias for id
                'name': 'firstName',  # Will combine with lastName
                'email': 'email',
                'phone': 'phone',
                'address': 'address',
                'city': 'city',
                'state': 'state',
                'state_code': 'state',  # Alias for state
                'zip': 'zipCode',
                'zip_code': 'zipCode',  # Alias for zip
                'postal_code': 'zipCode',  # Alias for zip
                'country': 'country',
                'transcripts': 'transcripts',  # Will handle separately
                'transcript': 'transcripts',   # Alias for transcripts
                'calls': 'transcripts'         # Another common alias
            }

            # Define which fields are part of the transcript
            transcript_fields = {
                'transcript_id', 'call_id', 'call_timestamp', 'duration',
                'summary', 'sentiment', 'key_points', 'action_items',
                'call_type', 'agent_id', 'customer_id', 'transcript_text'
            }

            # Separate transcript fields from customer fields
            requested_transcript_fields = [f for f in requested_fields if f in transcript_fields]

            # Only include transcript fields if explicitly requested or if 'transcripts' is requested
            include_transcripts = any(f in requested_fields for f in ['transcripts', 'transcript', 'calls'])

            # Get the fields to request from the API for customer data
            logger.debug(f"Original requested fields: {requested_fields}")
            logger.debug(f"Transcript fields: {transcript_fields}")

            api_fields = []
            for f in requested_fields:
                if f in field_mapping and f not in transcript_fields and f not in ['transcripts', 'transcript', 'calls']:
                    mapped = field_mapping.get(f, f)
                    api_fields.append(mapped)
                    logger.debug(f"Mapped field '{f}' -> '{mapped}' for API request")

            logger.debug(f"Final API fields to request: {api_fields}")

            # If we need name, make sure we have both first and last name
            if 'name' in requested_fields:
                if 'firstName' not in api_fields:
                    api_fields.append('firstName')
                if 'lastName' not in api_fields:
                    api_fields.append('lastName')

            # Remove duplicates
            api_fields = list(dict.fromkeys(api_fields))

            # Get customers with only the requested fields
            customers = []
            try:
                logger.debug(f"Requesting fields from API: {api_fields}")
                if not query or query in ["customers", "customer"]:
                    # If no specific query, get all customers
                    customers = await mcp_client.search_customers(
                        name=None,
                        fields=api_fields,
                        limit=100  # Adjust limit as needed
                    )
                else:
                    # Perform the search with the query
                    customers = await mcp_client.search_customers(
                        name=query,
                        fields=api_fields,
                        limit=100  # Adjust limit as needed
                    )

                # Log the first customer to verify fields
                if customers:
                    logger.debug(f"First customer data received: {customers[0].keys()}")
                    if 'state' in customers[0]:
                        logger.debug(f"State value in first customer: {customers[0]['state']}")
                    else:
                        logger.debug("State field not found in customer data")
                else:
                    logger.debug("No customer data received")

            except Exception as e:
                logger.error(f"Error fetching customers: {str(e)}")
                raise

            # Process the results to combine first and last name if name was requested
            for customer in customers:
                if 'firstName' in customer or 'lastName' in customer:
                    first_name = customer.pop('firstName', '')
                    last_name = customer.pop('lastName', '')
                    customer['name'] = f"{first_name} {last_name}".strip()

            # If transcripts or specific transcript fields are requested, fetch them
            if (include_transcripts or requested_transcript_fields) and customers:
                customer_ids = [str(c.get('id')) for c in customers if c.get('id')]
                if customer_ids:
                    # Get transcripts in batches if needed
                    batch_size = 50  # Adjust based on your API limits
                    for i in range(0, len(customer_ids), batch_size):
                        batch_ids = customer_ids[i:i + batch_size]

                        # Only request specific transcript fields if specified
                        transcript_params = {}
                        if requested_transcript_fields:
                            transcript_params['fields'] = requested_transcript_fields

                        # Fetch transcripts with optional field filtering
                        transcripts_data = await mcp_client.get_customer_transcripts(
                            customer_ids=batch_ids,
                            **transcript_params
                        )

                        # Merge transcripts into the customers data
                        for customer in customers:
                            customer_id = str(customer.get('id'))
                            if customer_id in transcripts_data:
                                # If specific fields were requested, filter the transcript data
                                if requested_transcript_fields:
                                    filtered_transcripts = []
                                    for transcript in transcripts_data[customer_id]:
                                        filtered = {}
                                        for field in requested_transcript_fields:
                                            if field in transcript:
                                                filtered[field] = transcript[field]
                                        if filtered:  # Only include if there's data
                                            filtered_transcripts.append(filtered)
                                    customer['transcripts'] = filtered_transcripts
                                else:
                                    customer['transcripts'] = transcripts_data[customer_id]

            # Format the response
            response = await format_customer_response(
                customers,
                message,
                requested_fields=requested_fields,
                context=context
            )

            # If raw_data is requested, include only the requested fields in the response
            if context.get('raw_data', False):
                response['data'] = []
                for customer in customers:
                    # Create a new dictionary with only the requested fields
                    customer_data = {}

                    # Add only the requested fields to the response
                    for field in requested_fields:
                        # Map between different field name variations
                        if field == 'id' and 'id' not in customer and 'customerId' in customer:
                            customer_data['id'] = customer['customerId']
                        elif field == 'customerId' and 'customerId' not in customer and 'id' in customer:
                            customer_data['customerId'] = customer['id']
                        else:
                            customer_data[field] = customer.get(field)

                    response['data'].append(customer_data)

            response['metadata'].update({
                "operation": "list_customers",
                "count": len(customers) if customers else 0
            })
            return response

        # Default response for customer-related queries
        requested_fields = await get_requested_fields(message)
        if not isinstance(requested_fields, set):
            requested_fields = set()

        try:
            # Try to get customers with search_customers first
            logger.info("Fetching customers using search_customers...")
            try:
                customers = await mcp_client.search_customers()
                logger.debug(f"search_customers response: {customers}")

                if customers is None:
                    logger.warning("search_customers returned None, trying get_customers_with_transcripts...")
                    raise ValueError("search_customers returned None")

                if not isinstance(customers, list):
                    logger.warning(f"search_customers returned non-list type: {type(customers)}")
                    customers = []

            except Exception as e:
                logger.warning(f"Error in search_customers: {str(e)}")
                customers = []

            if not customers:
                logger.info("No customers from search_customers, trying get_customers_with_transcripts...")
                try:
                    customers_with_transcripts = await mcp_client.get_customers_with_transcripts()
                    logger.debug(f"get_customers_with_transcripts response: {customers_with_transcripts}")

                    customers = []
                    if customers_with_transcripts:
                        for cust in customers_with_transcripts:
                            try:
                                # Create a customer dictionary with all available fields
                                customer = {}
                                # Ensure we have the name field for backward compatibility
                                customer['name'] = f"{cust.get('firstName', '')} {cust.get('lastName', '')}".strip()
                                                    # Add only the requested fields to the response
                                for field in requested_fields:
                                    # Map between different field name variations
                                    if field == 'id' and 'id' not in cust and 'customerId' in cust:
                                        customer['id'] = cust['customerId']
                                    elif field == 'customerId' and 'customerId' not in cust and 'id' in cust:
                                        customer['customerId'] = cust['id']
                                    else:
                                        customer[field] = cust.get(field)
                                # Ensure we have transcripts, defaulting to empty list if not present
                                if 'transcripts' not in cust:
                                    customer['transcripts'] = []
                                customers.append(cust)
                            except Exception as cust_err:
                                logger.error(f"Error processing customer data: {cust_err}")

                    if not customers:
                        return {
                            "response": "No customer data available.",
                            "client_used": "customer",
                            "metadata": {"count": 0}
                        }
                except Exception as e:
                    logger.error(f"Error fetching customers: {str(e)}")
                    raise

                # If transcripts are specifically requested but not yet loaded
                if 'transcripts' in requested_fields and not any('transcripts' in cust for cust in customers):
                    logger.info("Fetching transcripts separately...")
                    try:
                        customers_with_transcripts = await mcp_client.get_customers_with_transcripts()
                        if customers_with_transcripts:
                            # Create a mapping of customer emails to transcripts
                            transcripts_map = {
                                cust.get('email'): cust.get('transcripts', [])
                                for cust in customers_with_transcripts
                                if cust.get('email')
                            }
                            # Add transcripts to customers by matching emails
                            for customer in customers:
                                customer_email = customer.get('email')
                                if customer_email in transcripts_map:
                                    customer['transcripts'] = transcripts_map[customer_email]
                    except Exception as e:
                        logger.error(f"Error fetching transcripts: {str(e)}")
                        raise

                return await format_customer_response(customers, message, requested_fields)

        except Exception as e:
            logger.error(f"Error in customer data retrieval: {str(e)}", exc_info=True)
            raise
    except Exception as e:
        logger.error(f"Error in customer request handler: {e}")
        return {
            "response": "I encountered an error processing your customer request. Please try again later.",
            "client_used": "customer",
            "metadata": {"error": str(e), "status": "error"}
        }

class ProcessRequest(BaseModel):
    """Request model for processing a conversation message."""
    messages: List[Dict[str, Any]] = Field(..., description="List of messages in the conversation")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context for the conversation")

@router.post("/process", response_model=ConversationResponse)
@router.get("/process", response_model=ConversationResponse)
async def process_conversation(
    request: Optional[Dict[str, Any]] = Body(None),
    message: Optional[str] = Query(None, description="The message to process (for GET requests)"),
    role: str = Query("user", description="The role of the message sender (for GET requests)")
):
    """
    Process a conversation message and route it to the appropriate client.

    For POST requests, send a JSON body with 'messages' and optional 'context':
    {
        "messages": [{"role": "user", "content": "your message"}],
        "context": {}
    }

    For GET requests, use query parameters:
    /process?message=your+message&role=user
    """
    try:
        # If message parameter is provided, treat as GET request
        if message is not None:
            request_data = {
                "messages": [{"role": role, "content": message}],
                "context": {}
            }
            request_model = ConversationRequest(**request_data)
        # Otherwise, treat as POST request with JSON body
        elif request is not None:
            request_data = request.dict()
            request_model = ConversationRequest(**request_data)
        else:
            raise HTTPException(
                status_code=400,
                detail="Either provide a message parameter (for GET) or a request body (for POST)"
            )

        # Validate the request model
        if not request_model.messages:
            raise HTTPException(status_code=400, detail="No messages provided in the conversation")

        # Get the last user message
        last_message = next(
            (msg for msg in reversed(request_model.messages)
             if isinstance(msg, dict) and msg.get("role") == "user" or
                hasattr(msg, "role") and msg.role == "user"),
            None
        )

        if not last_message:
            raise HTTPException(status_code=400, detail="No user message found in the conversation")

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    # Get the message and context
    message = last_message.content
    context = request_model.context if hasattr(request_model, 'context') else {}

    # First, detect all intents from the original message
    intents = await detect_intents(message)
    logger.debug(f"Detected intents: {intents}")

    # Check for transformation operations in the original message
    transform_operations = []
    transform_fields = []

    message_lower = message.lower()

    # Define common customer fields that can be transformed
    common_fields = [
        'email', 'name', 'phone', 'address', 'city', 'state', 'zip', 'country',
        'first_name', 'last_name', 'company', 'job_title', 'department'
    ]

    # Find which fields are mentioned in the message and might need transformation
    for field in common_fields:
        # Check for field name in message (with word boundaries to avoid partial matches)
        if re.search(r'\b' + re.escape(field) + r'\b', message_lower):
            transform_fields.append(field)

    # If no fields were found but we have transform operations, default to email
    if not transform_fields and ('transform' in message_lower or 'convert' in message_lower):
        transform_fields = ['email']

    # First, check for specific transformation patterns
    if 'uppercase and reverse' in message_lower or 'upper case and reverse' in message_lower:
        transform_operations = ['uppercase', 'reverse']
    elif 'reverse and uppercase' in message_lower or 'reverse and upper case' in message_lower:
        transform_operations = ['reverse', 'uppercase']
    else:
        # Check for individual operations
        if any(word in message_lower for word in ['uppercase', 'upper case', 'all caps', 'capital letters']):
            transform_operations.append('uppercase')
        if any(word in message_lower for word in ['lowercase', 'lower case']):
            transform_operations.append('lowercase')
        if any(word in message_lower for word in ['capitalize', 'title case']):
            transform_operations.append('capitalize')
        if 'reverse' in message_lower:
            transform_operations.append('reverse')
        if 'strip' in message_lower:
            transform_operations.append('strip')

    logger.debug(f"Detected transform operations: {transform_operations}")

    # If no intents detected, use fallback
    if not intents:
        return ConversationResponse(
            response="I'm not sure how to process that request. I can help with customer queries or text transformations.",
            client_used="fallback",
            metadata={"status": "no_intent_detected"},
            context=context
        )

    # If we have both customer and text_transform intents, prioritize customer intent
    has_customer = any(i["intent"] == "customer" for i in intents)
    has_text_transform = any(i["intent"] == "text_transform" for i in intents)

    if has_customer and has_text_transform:
        # If we have both, prioritize customer intent and add transform_operations to context
        primary_intent = next(i for i in intents if i["intent"] == "customer")
        context['transform_operations'] = transform_operations
        context['transform_fields'] = transform_fields
    elif has_customer and transform_operations:
        # If we only have customer intent but have transform operations
        primary_intent = next(i for i in intents if i["intent"] == "customer")
        context['transform_operations'] = transform_operations
        context['transform_fields'] = transform_fields
    elif has_text_transform and transform_operations:
        # If we only have text transform intent
        primary_intent = next(i for i in intents if i["intent"] == "text_transform")
    else:
        # Default to highest confidence intent
        primary_intent = intents[0]

    # Determine client type from primary intent
    client_type = primary_intent["intent"]

    # Initialize result variable
    result = None

    # Handle the primary intent
    if client_type == "customer":
        # Check if raw data is requested from query params or request body
        raw_data = False
        if hasattr(request_model, 'context'):
            raw_data = request_model.context.get('raw', False)
        elif isinstance(request, dict) and 'context' in request:
            raw_data = request['context'].get('raw', False)

        # Check if we have transform operations to apply
        transform_operations = context.get('transform_operations', [])

        # Build the request message based on whether we're doing transformations
        request_message = message

        # Get requested fields and ensure it's a set
        requested_fields_coro = get_requested_fields(message)
        requested_fields = await requested_fields_coro if asyncio.iscoroutine(requested_fields_coro) else requested_fields_coro

        # Process the message with the appropriate handler
        response = await handle_customer_request(
            request_message,
            context={
                **context,
                "raw_data": raw_data
            }
        )

        # If raw data is requested, include it in the response
        if raw_data and isinstance(response, dict):
            return {
                "response": "Data retrieved successfully",
                "client_used": "customer",
                "metadata": response.get("metadata", {}),
                "data": response.get("data", []),
                "context": context
            }

        # Set result to the response
        result = response

        # Debug log the requested fields
        if 'metadata' in response and 'requested_fields' in response['metadata']:
            logger.debug(f"Requested fields in response: {response['metadata']['requested_fields']}")
        else:
            logger.debug("No requested_fields in response metadata")

        # Initialize result_dict with the response
        result_dict = response

        # Check if we have emails to transform
        if result_dict.get('metadata', {}).get('emails'):
            try:
                # Transform each email individually
                transformed_emails = []
                original_emails = result_dict['metadata']['emails']

                for email in original_emails:
                    # Skip if email is None or not a string
                    if not isinstance(email, str):
                        continue

                    # Clean up the email (in case it's in the format "email [ID: ...]")
                    clean_email = email.split(' [ID:')[0].strip()

                    # Apply transformations in sequence
                    current_text = clean_email

                    try:
                        # Apply each operation one by one to ensure proper chaining
                        for operation in transform_operations:
                            transform_result = await text_transform_client.transform(
                                current_text,
                                operation=operation
                            )
                            current_text = transform_result.transformed
                            logger.debug(f"Applied {operation} to {clean_email[:10]}...: {current_text[:20]}...")

                        transformed_emails.append(current_text)

                    except Exception as e:
                        logger.error(f"Error transforming email {clean_email}: {e}")
                        # If transformation fails, keep the original email
                        transformed_emails.append(clean_email)

                # Update the response with transformed emails
                if transformed_emails:
                    response = "\n".join(transformed_emails)

                    # Update metadata
                    if isinstance(result_dict, dict):
                        result_dict['metadata'] = result_dict.get('metadata', {})
                        result_dict['metadata']['transformed_emails'] = transformed_emails
                        result_dict['metadata']['operations'] = transform_operations
                        result_dict['metadata']['applied_intents'] = [i["intent"] for i in intents]
                        result_dict['metadata']['original_emails'] = original_emails
                        result_dict['metadata']['emails'] = transformed_emails

                    return ConversationResponse(
                        response=response,
                        client_used="customer",
                        metadata=result_dict.get('metadata', {}),
                        context=context
                    )

            except Exception as e:
                logger.error(f"Error in email transformation: {e}")
                # Fall through to return original result if transformation fails

        # Add detected intents to metadata
        if isinstance(result_dict, dict):
            result_dict['metadata'] = result_dict.get('metadata', {})
            result_dict['metadata']['detected_intents'] = [i["intent"] for i in intents]

        if hasattr(result, 'dict'):
            return result
        result_dict['context'] = context
        return ConversationResponse(**result_dict)

    elif primary_intent["intent"] == "text_transform":
        # Handle standalone text transformation
        result = await handle_text_transform(message, context)
        result_dict = result if isinstance(result, dict) else result.dict()
        result_dict['metadata'] = result_dict.get('metadata', {})
        result_dict['metadata']['detected_intents'] = [i["intent"] for i in intents]
        result_dict['context'] = context
        return ConversationResponse(**result_dict)

    # Default response if no specific intent is detected
    return ConversationResponse(
        response="I'm not sure how to process that request. I can help with customer queries or text transformations.",
        client_used="fallback",
        metadata={"intent": primary_intent["intent"] if intents else "unknown"},
        context=context
    )

# Example usage in FastAPI app:
# from .routers import conversation
# app.include_router(conversation.router)
