"""Debug test for the /converse endpoint."""
import httpx
import asyncio
import json

async def test_converse():
    """Test the /converse endpoint with detailed error output."""
    url = "http://localhost:8000/api/converse"
    headers = {"Content-Type": "application/json"}

    test_queries = [
        "Check server status",
        "Is the server up?",
        "Show me all customers",
        "List call transcripts"
    ]

    async with httpx.AsyncClient() as client:
        for query in test_queries:
            print(f"\n{'='*50}")
            print(f"Testing query: {query}")
            try:
                # First, make the request
                response = await client.post(
                    url,
                    json={"query": query},
                    headers=headers,
                    timeout=10.0
                )

                print(f"Status: {response.status_code}")

                # Try to parse the response as JSON
                try:
                    response_data = response.json()
                    print("Response:", json.dumps(response_data, indent=2))
                except Exception as e:
                    print(f"Failed to parse JSON response: {e}")
                    print(f"Raw response: {response.text}")

                # Print response headers for debugging
                print("\nResponse headers:")
                for header, value in response.headers.items():
                    print(f"  {header}: {value}")

            except httpx.HTTPStatusError as e:
                print(f"HTTP error: {e}")
                if hasattr(e, 'response'):
                    print(f"Response status: {e.response.status_code}")
                    print(f"Response text: {e.response.text}")
            except Exception as e:
                print(f"Error: {str(e)}")
                import traceback
                print("Traceback:")
                print(traceback.format_exc())

if __name__ == "__main__":
    print("Starting test...")
    asyncio.run(test_converse())
    print("\nTest completed.")
