"""Test settings for the MCP Host."""
import os
from pathlib import Path
from typing import List

# Test directories
TEST_MODEL_DIR = Path("test_models").resolve()
TEST_DATA_DIR = Path("test_data").resolve()

# Ensure test directories exist
TEST_MODEL_DIR.mkdir(parents=True, exist_ok=True)
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Test settings with all required fields
TEST_SETTINGS = {
    # Server settings
    "HOST": "0.0.0.0",
    "PORT": 8001,
    "DEBUG": True,
    "ENVIRONMENT": "testing",
    "HOST_NAME": "mcp-host-test",
    "VERSION": "0.1.0",
    
    # MCP Server settings
    "MCP_SERVER_URL": "http://localhost:8005",
    "API_KEY": "test-api-key",
    
    # Path settings
    "MODEL_DIR": str(TEST_MODEL_DIR),
    "DATA_DIR": str(TEST_DATA_DIR),
    
    # CORS settings
    "CORS_ORIGINS": ["*"],
    
    # Feature flags
    "AUTO_REGISTER_MODELS": False,
    
    # Health check settings
    "HEALTH_CHECK_INTERVAL": 30,
    
    # Logging settings
    "LOG_LEVEL": "DEBUG",
    "LOG_FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}

# Set environment variables for the test
for key, value in TEST_SETTINGS.items():
    if isinstance(value, (list, dict)):
        import json
        os.environ[key] = json.dumps(value)
    elif isinstance(value, bool):
        os.environ[key] = str(value).lower()
    else:
        os.environ[key] = str(value)
