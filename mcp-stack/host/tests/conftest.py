"""Pytest configuration and fixtures."""
import asyncio
import json
import shutil
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import test settings first to set up environment variables
from tests.test_settings import TEST_SETTINGS, TEST_MODEL_DIR, TEST_DATA_DIR

# Now import the app and other components with the environment variables already set
from src.config import Settings, get_settings
from src.main import app, mcp_client, mcp_host

# Sample model configuration
SAMPLE_MODEL_CONFIG = {
    "name": "test-model",
    "version": "1.0.0",
    "description": "Test model for unit tests",
    "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}},
    "output_schema": {"type": "object", "properties": {"label": {"type": "string"}}},
}

# Sample prediction request
SAMPLE_PREDICTION_REQUEST = {
    "model_name": "test-model",
    "model_version": "1.0.0",
    "inputs": {"text": "Test input"},
}


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Override settings for testing."""
    # Clear any existing settings instance
    from src.config import _settings_instance, Settings
    _settings_instance = None

    # Create a new settings instance with test values
    settings = Settings()

    # Update the settings with test values, converting paths to Path objects
    for key, value in TEST_SETTINGS.items():
        if key in ['MODEL_DIR', 'DATA_DIR'] and isinstance(value, str):
            value = Path(value).resolve()
            value.mkdir(parents=True, exist_ok=True)
        setattr(settings, key, value)

    # Ensure required directories exist
    if hasattr(settings, 'MODEL_DIR') and isinstance(settings.MODEL_DIR, (str, Path)):
        model_dir = Path(settings.MODEL_DIR).resolve()
        model_dir.mkdir(parents=True, exist_ok=True)
        settings.MODEL_DIR = model_dir

    if hasattr(settings, 'DATA_DIR') and isinstance(settings.DATA_DIR, (str, Path)):
        data_dir = Path(settings.DATA_DIR).resolve()
        data_dir.mkdir(parents=True, exist_ok=True)
        settings.DATA_DIR = data_dir

    # Add required attributes that might be missing
    if not hasattr(settings, 'VERSION'):
        settings.VERSION = '0.1.0'
    if not hasattr(settings, 'HOST_NAME'):
        settings.HOST_NAME = 'test-host'

    # Update the singleton
    from src.config import get_settings
    _settings = get_settings()
    for key, value in settings.dict().items():
        setattr(_settings, key, value)

    return _settings


@pytest.fixture(autouse=True)
def setup_test_environment(test_settings):
    """Set up test environment before each test."""
    # Create test directories
    TEST_MODEL_DIR.mkdir(exist_ok=True)
    TEST_DATA_DIR.mkdir(exist_ok=True)

    # Override settings
    app.state.settings = test_settings

    yield  # Test runs here

    # Clean up after tests
    shutil.rmtree(TEST_MODEL_DIR, ignore_errors=True)
    shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)


@pytest.fixture
def test_client(test_settings):
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient
    from src.main import app

    # Ensure the app is using the test settings
    app.state.settings = test_settings

    # Initialize the TestClient with the app
    client = TestClient(app)

    try:
        yield client
    finally:
        # Clean up resources if needed
        pass


@pytest_asyncio.fixture
async def async_client(test_settings) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    from src.main import app

    # Ensure the app is using the test settings
    app.state.settings = test_settings

    # Create an AsyncClient with the app and base_url
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_model_config() -> Dict:
    """Return a sample model configuration."""
    return SAMPLE_MODEL_CONFIG.copy()


@pytest.fixture
def sample_prediction_request() -> Dict:
    """Return a sample prediction request."""
    return SAMPLE_PREDICTION_REQUEST.copy()


@pytest.fixture
def mock_mcp_server(httpx_mock):
    """Mock the MCP server responses."""
    # Mock data sources response
    httpx_mock.add_response(
        method="POST",
        url="http://testserver/graphql",
        json={
            "data": {
                "dataSources": [
                    {
                        "id": "test-source",
                        "name": "Test Source",
                        "description": "Test data source",
                        "path": "/data/test",
                        "sourceType": "JSON",
                        "metadata": {},
                        "createdAt": "2023-01-01T00:00:00",
                        "updatedAt": "2023-01-01T00:00:00",
                    }
                ]
            }
        },
    )

    # Mock data items response
    httpx_mock.add_response(
        method="POST",
        url="http://testserver/graphql",
        json={
            "data": {
                "dataItems": {
                    "items": [
                        {
                            "id": "item-1",
                            "sourceId": "test-source",
                            "data": {"text": "Test data"},
                            "metadata": {},
                            "createdAt": "2023-01-01T00:00:00",
                            "updatedAt": "2023-01-01T00:00:00",
                        }
                    ],
                    "total": 1,
                    "page": 1,
                    "size": 1,
                    "hasMore": False,
                }
            }
        },
    )

    return httpx_mock
