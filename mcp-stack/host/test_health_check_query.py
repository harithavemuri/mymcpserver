"""Test the health check query functionality."""
import asyncio
from src.conversation import ConversationHandler, QueryIntent

async def test_health_check_queries():
    """Test various health check queries."""
    handler = ConversationHandler()
    
    test_queries = [
        "Check server status",
        "What's the status of the server?",
        "Is the server up?",
        "Verify server health",
        "Is the server healthy?",
        "How's the server doing?"
    ]
    
    print("\n=== Testing Health Check Queries ===\n")
    
    for query in test_queries:
        params = handler.parse_query(query)
        print(f"Query: {query}")
        print(f"  Detected Intent: {params.intent}")
        print(f"  Is Health Check: {params.intent == QueryIntent.HEALTH_CHECK}")
        print()
    
    print("=== Test Complete ===\n")

if __name__ == "__main__":
    asyncio.run(test_health_check_queries())
