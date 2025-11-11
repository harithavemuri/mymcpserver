"""Debug the /api/converse endpoint with detailed error handling."""
import asyncio
import httpx
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_converse.log')
    ]
)
logger = logging.getLogger(__name__)

async def test_converse():
    """Test the /api/converse endpoint with detailed error handling."""
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
                logger.debug(f"Sending request to {url} with query: {query}")
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
                        logger.info("Request successful!")
                        logger.info(f"Response text: {response_data.get('response')}")
                except Exception as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.info(f"Raw response: {response.text}")
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e}")
                if hasattr(e, 'response'):
                    logger.error(f"Response status: {e.response.status_code}")
                    logger.error(f"Response text: {e.response.text}")
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                logger.error(f"Request URL: {e.request.url}")
                logger.error(f"Request method: {e.request.method}")
                logger.error(f"Request headers: {e.request.headers}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                logger.error(traceback.format_exc())

if __name__ == "__main__":
    logger.info("Starting debug test...")
    asyncio.run(test_converse())
    logger.info("Debug test completed.")
