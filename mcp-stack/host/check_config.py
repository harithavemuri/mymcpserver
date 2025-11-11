"""Check the host server's configuration."""
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('check_config.log')
    ]
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check environment variables and configuration."""
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Check MCP_SERVER_URL
    mcp_server_url = os.getenv('MCP_SERVER_URL', 'http://localhost:8005')
    logger.info(f"MCP_SERVER_URL: {mcp_server_url}")
    
    # Check other important environment variables
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8000'))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Debug: {debug}")
    
    # Check if required environment variables are set
    required_vars = ['MCP_SERVER_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"Missing required environment variables: {', '.join(missing_vars)}")
    else:
        logger.info("All required environment variables are set.")
    
    return {
        'mcp_server_url': mcp_server_url,
        'host': host,
        'port': port,
        'debug': debug,
        'missing_vars': missing_vars
    }

if __name__ == "__main__":
    logger.info("Checking host server configuration...")
    config = check_environment()
    logger.info("Configuration check completed.")
    
    # Print a summary
    print("\nConfiguration Summary:")
    print("-" * 40)
    for key, value in config.items():
        print(f"{key}: {value}")
    print("-" * 40)
