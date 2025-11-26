import asyncio
import httpx
import json
from typing import Dict, Any, List

async def test_post_conversation():
    """Test the POST /conversation/process endpoint."""
    url = "http://localhost:8000/conversation/process"

    # Test cases with different payloads
    test_cases = [
        # Basic request
        {
            "name": "Basic request",
            "payload": {
                "messages": [{"role": "user", "content": "Show me all customers"}],
                "context": {}
            },
            "expected_status": 200
        },
        # Request with multiple messages
        {
            "name": "Multiple messages",
            "payload": {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": "Show me all customers"}
                ],
                "context": {"user_id": "test123"}
            },
            "expected_status": 200
        },
        # Invalid request (missing messages)
        {
            "name": "Invalid request - missing messages",
            "payload": {"context": {}},
            "expected_status": 422
        }
    ]

    for test_case in test_cases:
        print(f"\n{'='*50}")
        print(f"Test Case: {test_case['name']}")
        print("-" * 50)

        try:
            async with httpx.AsyncClient() as client:
                print("Sending POST request to:", url)
                print("Request payload:", json.dumps(test_case['payload'], indent=2))

                response = await client.post(
                    url,
                    json=test_case['payload'],
                    timeout=10.0
                )

                print("\nResponse Status Code:", response.status_code)
                print("Response Headers:", dict(response.headers))

                try:
                    response_data = response.json()
                    print("Response Body:", json.dumps(response_data, indent=2))

                    # Additional validation for successful responses
                    if response.status_code == 200:
                        assert "response" in response_data, "Response missing 'response' field"
                        assert "client_used" in response_data, "Response missing 'client_used' field"
                        print("✅ Test passed!")

                except json.JSONDecodeError:
                    print("Response Body (raw):", response.text)

                assert response.status_code == test_case['expected_status'], \
                    f"Expected status {test_case['expected_status']}, got {response.status_code}"

        except Exception as e:
            print(f"❌ Test failed: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(test_post_conversation())
