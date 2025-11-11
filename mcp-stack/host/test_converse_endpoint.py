"""Test the /converse endpoint with detailed logging."""
import asyncio
import httpx
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_converse.log')
    ]
)
logger = logging.getLogger(__name__)

async def test_converse():
    """Test the /converse endpoint with detailed error handling."""
    url = "http://localhost:8000/api/converse"
    headers = {"Content-Type": "application/json"}
    
    test_queries = [
        "Check server status",
        "Is the server up?",
        "Show me all customers",
        "List call transcripts"
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for query in test_queries:
            logger.info(f"\n{'='*80}")
            logger.info(f"Testing query: {query}")
            
            try:
                # Make the request
                response = await client.post(
                    url,
                    json={"query": query},
                    headers=headers
                )
                logger.info(f"Status: {response.status_code}")
                
                try:
                    response_data = response.json()
                    logger.info(f"Response: {response_data}")
                    
                    # If there's an error in the response, log it
                    if "error" in response_data:
                        logger.error(f"Error in response: {response_data['error']}")
                    
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
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting test...")
    asyncio.run(test_converse())
    logger.info("Test completed.")
