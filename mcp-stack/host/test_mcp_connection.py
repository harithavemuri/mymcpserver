"""Test the connection to the MCP server."""
import asyncio
import httpx
import logging
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_mcp_connection.log')
    ]
)
logger = logging.getLogger(__name__)

async def test_mcp_connection():
    """Test the connection to the MCP server."""
    base_url = "http://localhost:8005"
    endpoints = [
        "/health",
        "/api/health",
        "/api/v1/health"
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for endpoint in endpoints:
            url = urljoin(base_url, endpoint)
            try:
                logger.info(f"Testing connection to {url}")
                response = await client.get(url)
                logger.info(f"Status: {response.status_code}")
                logger.info(f"Response: {response.text}")
                if response.status_code == 200:
                    return True, url
            except httpx.RequestError as e:
                logger.error(f"Error connecting to {url}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
    
    return False, None

if __name__ == "__main__":
    logger.info("Testing connection to MCP server...")
    success, url = asyncio.run(test_mcp_connection())
    if success:
        logger.info(f"Successfully connected to MCP server at {url}")
    else:
        logger.error("Failed to connect to MCP server. Please check if the server is running and accessible.")
    logger.info("Test completed.")
