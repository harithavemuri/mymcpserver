"""Test the /converse endpoint."""
import httpx
import asyncio

async def test_converse():
    """Test the /converse endpoint with a health check query."""
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
            print(f"\nTesting query: {query}")
            try:
                response = await client.post(
                    url,
                    json={"query": query},
                    headers=headers,
                    timeout=10.0
                )
                print(f"Status: {response.status_code}")
                print(f"Response: {response.json()}")
            except Exception as e:
                print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_converse())
