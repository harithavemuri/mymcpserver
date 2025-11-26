"""
Test script for the conversation endpoint.
"""
import asyncio
import httpx
import json
from typing import Dict, Any, List

# Configuration
BASE_URL = "http://localhost:8000"  # Default FastAPI port
CONVERSATION_ENDPOINT = f"{BASE_URL}/conversation/process"

async def test_conversation():
    """Test the conversation endpoint with different types of requests."""
    test_cases = [
        {
            "description": "Uppercase transformation",
            "messages": [
                {"role": "user", "content": "Convert this to uppercase: hello world"}
            ]
        },
        {
            "description": "Title case transformation",
            "messages": [
                {"role": "user", "content": "Make this a title: the quick brown fox"}
            ]
        },
        {
            "description": "Reverse transformation",
            "messages": [
                {"role": "user", "content": "Reverse this text: hello"}
            ]
        },
        {
            "description": "Chained transformations",
            "messages": [
                {"role": "user", "content": "Make this uppercase and then reverse it: test"}
            ]
        },
        {
            "description": "Unknown command",
            "messages": [
                {"role": "user", "content": "This is a test message"}
            ]
        }
    ]

    async with httpx.AsyncClient() as client:
        for test_case in test_cases:
            print(f"\n{'='*50}")
            print(f"Test: {test_case['description']}")
            print(f"Request: {json.dumps(test_case, indent=2)}")

            try:
                response = await client.post(
                    CONVERSATION_ENDPOINT,
                    json=test_case,
                    timeout=30.0
                )

                print(f"Status: {response.status_code}")
                print("Response:")
                print(json.dumps(response.json(), indent=2))

            except Exception as e:
                print(f"Error: {str(e)}")

            print("="*50)

if __name__ == "__main__":
    print("Testing MCP Host Conversation Endpoint")
    print(f"Endpoint: {CONVERSATION_ENDPOINT}")
    print("-" * 50)

    asyncio.run(test_conversation())
