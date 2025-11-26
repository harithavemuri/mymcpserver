"""Test the host server's endpoints."""
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
        logging.FileHandler('test_host_endpoints.log')
    ]
)
logger = logging.getLogger(__name__)

async def test_endpoint(url, method="GET", json_data=None):
    """Test a single endpoint."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "GET":
                response = await client.get(url)
            elif method.upper() == "POST":
                response = await client.post(url, json=json_data)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return False, None

            logger.info(f"{method} {url} - Status: {response.status_code}")
            logger.debug(f"Response: {response.text}")
            return response.status_code == 200, response.text
    except Exception as e:
        logger.error(f"Error testing {method} {url}: {e}")
        return False, str(e)

async def test_all_endpoints():
    """Test all known endpoints on the host server."""
    base_url = "http://localhost:8000"
    endpoints = [
        {"path": "/health", "method": "GET"},
        {"path": "/api/health", "method": "GET"},
        {"path": "/api/converse", "method": "POST", "json": {"query": "Check server status"}},
        {"path": "/api/converse", "method": "POST", "json": {"query": "List all customers"}},
        {"path": "/api/endpoints", "method": "GET"}
    ]

    results = {}
    for endpoint in endpoints:
        url = urljoin(base_url, endpoint["path"])
        method = endpoint.get("method", "GET")
        json_data = endpoint.get("json")

        logger.info(f"\n{'='*80}")
        logger.info(f"Testing {method} {url}")
        if json_data:
            logger.debug(f"Request data: {json_data}")

        success, response = await test_endpoint(url, method, json_data)
        results[url] = {"success": success, "response": response}

    return results

if __name__ == "__main__":
    logger.info("Testing host server endpoints...")
    results = asyncio.run(test_all_endpoints())

    # Print summary
    logger.info("\n" + "="*80)
    logger.info("Test Summary:")
    logger.info("="*80)
    for url, result in results.items():
        status = "SUCCESS" if result["success"] else "FAILED"
        logger.info(f"{url}: {status}")
        if not result["success"]:
            logger.error(f"  Error: {result['response']}")

    logger.info("\nTesting completed.")
