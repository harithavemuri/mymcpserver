"""Test script for the MCP Host conversation endpoint."""
import asyncio
import httpx
import json
import traceback
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_conversation():
    """Test the conversation endpoint with various queries."""
    base_url = "http://localhost:8000"

    test_queries = [
        "Show me all customers",
        "Get details for customer CUST1000",
        "List recent call transcripts",
        "Find customer with email hguerrero@example.net"
    ]

    async with httpx.AsyncClient() as client:
        for query in test_queries:
            print(f"\nTesting query: {query}")
            print("-" * 50)

            try:
                logger.info(f"Sending request to {base_url}/api/converse with query: {query}")
                response = await client.post(
                    f"{base_url}/api/converse",
                    json={"query": query},
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )

                logger.info(f"Response status: {response.status_code}")

                try:
                    result = response.json()
                    if response.status_code == 200:
                        print(f"\n✅ Success!")
                        print(f"Response: {result.get('response')}")
                        if 'data' in result:
                            print("\n📊 Raw data:")
                            print(json.dumps(result.get('data'), indent=2))
                    else:
                        print(f"\n❌ Error {response.status_code}:")
                        print(f"Detail: {result.get('detail', 'No details provided')}")
                        print(f"Type: {result.get('type', 'Unknown error type')}")
                        if 'traceback' in result:
                            print("\n🔍 Stack trace:")
                            print(result['traceback'])
                except json.JSONDecodeError:
                    print(f"\n⚠️ Could not parse JSON response. Raw response:")
                    print(response.text)

            except httpx.HTTPStatusError as e:
                print(f"\n⚠️ HTTP error occurred: {str(e)}")
                if e.response is not None:
                    print(f"Response status: {e.response.status_code}")
                    print(f"Response text: {e.response.text}")
            except Exception as e:
                print(f"\n❌ Unexpected error: {str(e)}")
                print("\n🔍 Stack trace:")
                traceback.print_exc()

            print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_conversation())
