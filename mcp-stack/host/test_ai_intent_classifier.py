"""Test the AI-based intent classifier."""
import asyncio
from src.conversation import ConversationHandler
from src.intent_classifier import QueryIntent

async def test_ai_intent_classifier():
    """Test the AI-based intent classifier with various queries."""
    handler = ConversationHandler()

    test_cases = [
        # Health check queries
        ("Check server status", QueryIntent.HEALTH_CHECK),
        ("Is the server up?", QueryIntent.HEALTH_CHECK),
        ("How's the server doing?", QueryIntent.HEALTH_CHECK),
        ("Is the server healthy?", QueryIntent.HEALTH_CHECK),
        ("Verify server health", QueryIntent.HEALTH_CHECK),

        # List customers queries
        ("Show me all customers", QueryIntent.LIST_CUSTOMERS),
        ("List customers", QueryIntent.LIST_CUSTOMERS),
        ("Who are the customers?", QueryIntent.LIST_CUSTOMERS),

        # Get customer queries
        ("Show me customer CUST123", QueryIntent.GET_CUSTOMER),
        ("Get details for customer CUST456", QueryIntent.GET_CUSTOMER),
        ("Who is customer CUST789", QueryIntent.GET_CUSTOMER),

        # List transcripts queries
        ("Show me all transcripts", QueryIntent.LIST_TRANSCRIPTS),
        ("List call transcripts", QueryIntent.LIST_TRANSCRIPTS),
        ("Get transcript history", QueryIntent.LIST_TRANSCRIPTS),

        # Get transcript queries
        ("Show me transcript CALL123", QueryIntent.GET_TRANSCRIPT),
        ("Get call CALL456", QueryIntent.GET_TRANSCRIPT),
        ("What was in call CALL789", QueryIntent.GET_TRANSCRIPT),

        # Search queries
        ("Find customer John", QueryIntent.SEARCH),
        ("Search for customers in New York", QueryIntent.SEARCH),
        ("Who is john@example.com", QueryIntent.SEARCH)
    ]

    print("=== Testing AI Intent Classifier ===\n")

    for query, expected_intent in test_cases:
        params = handler.parse_query(query)
        result = "✅" if params.intent == expected_intent else "❌"
        print(f"{result} Query: {query}")
        print(f"   Detected: {params.intent.name} (Expected: {expected_intent.name})")
        confidence = getattr(params, 'confidence', None)
        if confidence is not None:
            print(f"   Confidence: {confidence:.2f}")
        else:
            print("   Confidence: N/A")
        if params.intent in [QueryIntent.GET_CUSTOMER, QueryIntent.GET_TRANSCRIPT, QueryIntent.SEARCH]:
            print(f"   Extracted: {params.filters}")
        print()

if __name__ == "__main__":
    asyncio.run(test_ai_intent_classifier())
