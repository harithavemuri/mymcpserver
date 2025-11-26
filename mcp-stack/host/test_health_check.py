"""Test the health check functionality of the /api/converse endpoint."""
import asyncio
import httpx
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_health_check.log')
    ]
)
logger = logging.getLogger(__name__)

async def test_health_check():
    """Test the health check functionality."""
    url = "http://localhost:8000/api/converse"
    headers = {"Content-Type": "application/json"}

    test_queries = [
        "Check server status",
        "Is the server up?",
        "What's the server status?",
        "Is the server healthy?"
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for query in test_queries:
            logger.info(f"\n{'='*80}")
            logger.info(f"Testing query: {query}")

            try:
                # Make the POST request
                response = await client.post(
                    url,
                    json={"query": query},
                    headers=headers
                )

                logger.info(f"Status: {response.status_code}")

                try:
                    response_data = response.json()
                    logger.info(f"Response: {response_data}")

                    # Check if the response contains an error
                    if "error" in response_data.get("data", {}):
                        logger.error(f"Error in response: {response_data['data']['error']}")
                    else:
                        logger.info("Health check successful!")
                        logger.info(f"Response text: {response_data.get('response')}")
                except Exception as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.info(f"Raw response: {response.text}")

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e}")
                if hasattr(e, 'response'):
                    logger.error(f"Response status: {e.response.status_code}")
                    logger.error(f"Response text: {e.response.text}")
            except Exception as e:
                logger.error(f"Error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting health check test...")
    asyncio.run(test_health_check())
    logger.info("Test completed.")
