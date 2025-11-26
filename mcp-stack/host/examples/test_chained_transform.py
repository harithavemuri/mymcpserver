"""
Test script for chained text transformations.
"""
import asyncio
import httpx
import json

# Configuration
BASE_URL = "http://localhost:8000"  # Default FastAPI port
CONVERSATION_ENDPOINT = f"{BASE_URL}/conversation/process"

async def test_chained_transform():
    """Test chained text transformations."""
    test_cases = [
        {
            "description": "Uppercase and reverse",
            "message": "Convert this to uppercase and reverse it: hello world"
        },
        {
            "description": "Title case and reverse",
            "message": "Make this title case and then reverse it: the quick brown fox"
        },
        {
            "description": "Multiple operations",
            "message": "Please transform this text to uppercase, then reverse it, and then make it lowercase: Test 123"
        }
    ]

    async with httpx.AsyncClient() as client:
        for test_case in test_cases:
            print(f"\n{'='*50}")
            print(f"Test: {test_case['description']}")
            print(f"Input: {test_case['message']}")
            
            try:
                response = await client.post(
                    CONVERSATION_ENDPOINT,
                    json={
                        "messages": [{"role": "user", "content": test_case['message']}],
                        "context": {}
                    },
                    timeout=30.0
                )
                
                print(f"Status: {response.status_code}")
                print("Response:")
                print(json.dumps(response.json(), indent=2))
                
            except Exception as e:
                print(f"Error: {str(e)}")
            
            print("="*50)

if __name__ == "__main__":
    print("Testing Chained Text Transformations")
    print(f"Endpoint: {CONVERSATION_ENDPOINT}")
    print("-" * 50)
    
    asyncio.run(test_chained_transform())
