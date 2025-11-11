"""List all available API endpoints on the host server."""
import httpx
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('list_endpoints.log')
    ]
)
logger = logging.getLogger(__name__)

async def list_endpoints():
    """List all available API endpoints on the host server."""
    base_url = "http://localhost:8000"
    endpoints = [
        "/",
        "/health",
        "/api/health",
        "/api/converse",
        "/docs",
        "/redoc",
        "/openapi.json"
    ]
    
    logger.info("Testing available endpoints on the host server...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for endpoint in endpoints:
            url = f"{base_url}{endpoint}"
            try:
                response = await client.get(url, follow_redirects=True)
                logger.info(f"{endpoint}: {response.status_code} - {response.text[:100]}...")
            except Exception as e:
                logger.error(f"Error accessing {url}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(list_endpoints())
