"""Test the MCP server's health endpoint directly."""
import asyncio
import httpx
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_mcp_health.log')
    ]
)
logger = logging.getLogger(__name__)

async def test_mcp_health():
    """Test the MCP server's health endpoint."""
    url = "http://localhost:8005/health"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info(f"Testing MCP server health at {url}")
            response = await client.get(url)
            logger.info(f"Status: {response.status_code}")
            logger.info(f"Response: {response.text}")
            return response.status_code == 200
        except httpx.RequestError as e:
            logger.error(f"Error connecting to MCP server: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False

if __name__ == "__main__":
    logger.info("Starting MCP server health test...")
    result = asyncio.run(test_mcp_health())
    if result:
        logger.info("MCP server health check passed!")
    else:
        logger.error("MCP server health check failed!")
    logger.info("Test completed.")
