"""Tests for the MCP Client with conversation support."""
import asyncio
import json
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock

import httpx
import pytest
import pytest_asyncio
from pydantic import ValidationError

# Mock spacy before importing client
sys.modules['spacy'] = Mock()
sys.modules['spacy.language'] = Mock()

# Apply asyncio marker to all async tests
def pytest_collection_modifyitems(items):
    for item in items:
        if "async" in getattr(item, "__name__", "").lower() or "test_" in getattr(item, "__name__", ""):
            item.add_marker(pytest.mark.asyncio)

from src.client import MCPClient, MCPError, ModelInfo

# Sample test data
SAMPLE_MODEL = {
    "id": "model-123",
    "name": "test-model",
    "description": "A test model",
    "version": "1.0.0",
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00"
}

@pytest.fixture
def mock_httpx_client():
    """Create a mock HTTPX client."""
    with patch('httpx.AsyncClient') as mock_client:
        yield mock_client

@pytest.fixture
def client(mock_httpx_client):
    """Create a test MCP client with mocked HTTP client."""
    # Create a mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": {"models": [SAMPLE_MODEL]}}
    mock_response.raise_for_status.return_value = None

    # Configure the mock client
    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_response
    mock_httpx_client.return_value = mock_client_instance

    # Create the client
    return MCPClient(server_url="http://testserver")

@pytest.fixture
def mock_spacy():
    """Mock spacy and its components."""
    with patch('spacy.load') as mock_load:
        # Create a mock nlp object
        mock_nlp = MagicMock()

        # Mock entities
        class MockEnt:
            def __init__(self, text, label_):
                self.text = text
                self.label_ = label_

        # Mock doc with entities
        mock_doc = MagicMock()
        mock_doc.ents = [
            MockEnt("sentiment-analysis", "PRODUCT"),
            MockEnt("1.0.0", "CARDINAL")
        ]
        mock_doc.text = "Register a new model named sentiment-analysis version 1.0.0"

        mock_nlp.return_value = mock_doc
        mock_load.return_value = mock_nlp

        yield mock_load

@pytest.fixture
def mock_spacy():
    """Mock spacy and its components."""
    with patch('spacy.load') as mock_load:
        # Create a mock nlp object
        mock_nlp = MagicMock()

        # Mock entities
        class MockEnt:
            def __init__(self, text, label_):
                self.text = text
                self.label_ = label_

        # Mock doc with entities
        mock_doc = MagicMock()
        mock_doc.ents = [
            MockEnt("sentiment-analysis", "PRODUCT"),
            MockEnt("1.0.0", "CARDINAL")
        ]
        mock_doc.text = "Register a new model named sentiment-analysis version 1.0.0"

        mock_nlp.return_value = mock_doc
        mock_load.return_value = mock_nlp

        yield mock_load

@pytest.mark.asyncio
async def test_register_model(client, mock_httpx_client):
    """Test model registration."""
    # Test data
    model_config = {
        "name": "sentiment-analysis",
        "version": "1.0.0",
        "description": "A test model"
    }

    # Expected response
    expected_response = {"id": "model-123", "status": "registered"}

    # Patch the _make_request method
    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_make_request:
        mock_make_request.return_value = expected_response

        # Call the method under test
        response = await client.register_model(model_config)

        # Verify the response
        assert response == expected_response

        # Verify _make_request was called correctly
        mock_make_request.assert_awaited_once_with("POST", "/models/register", data=model_config)

@pytest.mark.asyncio
async def test_list_models(client, mock_httpx_client):
    """Test listing models."""
    # Test data
    test_data = [{
        "id": "model-123",
        "name": "test-model",
        "description": "A test model",
        "version": "1.0.0",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }]

    # Patch the _make_request method
    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_make_request:
        mock_make_request.return_value = test_data

        # Call the method under test
        models = await client.list_models()

        # Verify the response
        assert len(models) == 1
        assert isinstance(models[0], ModelInfo)
        assert models[0].name == "test-model"

        # Verify _make_request was called correctly
        mock_make_request.assert_awaited_once_with("GET", "/models")

@pytest.mark.asyncio
async def test_chat_predict(client, mock_spacy):
    """Test chat with predict intent."""
    # Mock the predict method
    mock_predict = AsyncMock(return_value={"result": "positive", "confidence": 0.95})
    client.predict = mock_predict

    # Mock the conversation handler and context creation
    mock_conv = MagicMock()
    mock_conv.classify_intent.return_value = "predict"
    mock_conv.extract_entities.return_value = {
        "model_id": "sentiment-model",
        "input_data": "I love this product!"
    }

    # Mock the context creation
    context_mock = MagicMock()
    context_mock.id = "test-context-id"

    # Mock the create_context method
    create_context_mock = AsyncMock(return_value=context_mock)
    client.create_context = create_context_mock

    # Create a proper async side effect
    async def process_query_side_effect(query):
        return await client._handle_predict(mock_conv.extract_entities.return_value)

    mock_conv.process_query.side_effect = process_query_side_effect
    client.conversation = mock_conv

    # Test the chat method
    response = await client.chat("Predict sentiment for: I love this product!")

    # Verify the response and that predict was called correctly
    assert response == {"result": "positive", "confidence": 0.95}
    mock_predict.assert_awaited_once()

@pytest.mark.asyncio
async def test_predict(client, mock_httpx_client):
    """Test making a prediction."""
    # Test data
    model_id = "sentiment-model"
    context_id = "test-context"
    input_data = {"text": "I love this product!"}

    # Expected response
    expected_response = {
        "result": "positive",
        "confidence": 0.95,
        "model_id": model_id,
        "context_id": context_id
    }

    # Patch the _make_request method
    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_make_request:
        mock_make_request.return_value = expected_response

        # Call the method under test
        response = await client.predict(
            model_id=model_id,
            context_id=context_id,
            input_data=input_data
        )

        # Verify the response
        assert response == expected_response

        # Verify _make_request was called correctly
        mock_make_request.assert_awaited_once_with(
            "POST",
            "/predict",
            {
                "model_id": model_id,
                "context_id": context_id,
                "input_data": input_data
            }
        )

@pytest.mark.asyncio
async def test_register_model(client, mock_httpx_client):
    """Test model registration."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "model-123", "status": "registered"}
    mock_response.raise_for_status.return_value = None

    # Configure the mock client
    mock_client_instance = AsyncMock()

@pytest.mark.asyncio
async def test_list_models(client, mock_httpx_client):
    """Test listing models."""
    # Test data
    test_data = [{
        "id": "model-123",
        "name": "test-model",
        "description": "A test model",
        "version": "1.0.0",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }]

    # Patch the _make_request method to return our test data
    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_make_request:
        mock_make_request.return_value = test_data

        # Call the method under test
        models = await client.list_models()

        # Verify the response
        assert len(models) == 1
        assert isinstance(models[0], ModelInfo)
        assert models[0].name == "test-model"

        # Verify _make_request was called correctly
        mock_make_request.assert_awaited_once_with("GET", "/models")

@pytest.mark.asyncio
async def test_http_error_handling(client, mock_httpx_client):
    """Test HTTP error handling."""
    # Patch the _make_request method to raise an HTTP error
    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_make_request:
        # Setup the mock to raise an HTTP error
        mock_make_request.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404)
        )

        # Test that the error is properly propagated
        with pytest.raises(MCPError) as exc_info:
            await client.list_models()

        # Verify the error message contains the status code and error
        error_msg = str(exc_info.value)
        assert "404" in error_msg
        assert "Not Found" in error_msg

        # Verify _make_request was called
        mock_make_request.assert_awaited_once_with("GET", "/models")
