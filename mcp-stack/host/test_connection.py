"""Test connection to MCP server and check its health."""
import asyncio
import httpx
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_connection.log')
    ]
)
logger = logging.getLogger(__name__)

async def test_mcp_connection():
    """Test connection to MCP server."""
    mcp_url = "http://localhost:8005/health"
    logger.info(f"Testing connection to MCP server at {mcp_url}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test basic connection
            response = await client.get(mcp_url)
            logger.info(f"MCP server response: {response.status_code} - {response.text}")
            
            # Check if response is JSON
            try:
                data = response.json()
                logger.info(f"MCP server health: {data}")
                return True
            except Exception as e:
                logger.error(f"Failed to parse MCP server response: {e}")
                return False
                
    except Exception as e:
        logger.error(f"Error connecting to MCP server: {e}", exc_info=True)
        return False

async def test_host_connection():
    """Test connection to host server."""
    host_url = "http://localhost:8000/api/health"
    logger.info(f"Testing connection to host server at {host_url}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test basic connection
            response = await client.get(host_url)
            logger.info(f"Host server response: {response.status_code} - {response.text}")
            
            # Check if response is JSON
            try:
                data = response.json()
                logger.info(f"Host server health: {data}")
                return True
            except Exception as e:
                logger.error(f"Failed to parse host server response: {e}")
                return False
                
    except Exception as e:
        logger.error(f"Error connecting to host server: {e}", exc_info=True)
        return False

async def main():
    """Run connection tests."""
    logger.info("Starting connection tests...")
    
    # Test MCP server connection
    mcp_ok = await test_mcp_connection()
    logger.info(f"MCP server connection test: {'SUCCESS' if mcp_ok else 'FAILED'}")
    
    # Test host server connection
    host_ok = await test_host_connection()
    logger.info(f"Host server connection test: {'SUCCESS' if host_ok else 'FAILED'}")
    
    logger.info("Connection tests completed.")

if __name__ == "__main__":
    asyncio.run(main())
