"""Tests for the FastAPI application endpoints."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status, HTTPException
from fastapi.testclient import TestClient

from src.models import ModelConfig, ModelInfo, PredictionRequest, PredictionResponse
from src.main import app, MCPClient, mcp_host


class TestAPIEndpoints:
    """Test cases for the FastAPI endpoints."""

    def test_health_check(self, test_client, test_settings):
        """Test the health check endpoint."""
        from src.main import app
        
        # Ensure the app is using the test settings
        app.state.settings = test_settings
        
        # Test the health check endpoint
        response = test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check the response data
        assert "status" in data
        assert data["status"] == "healthy"
        assert "version" in data
        assert data["version"] == test_settings.VERSION
        assert "name" in data
        assert data["name"] == test_settings.HOST_NAME
    
    @pytest.mark.asyncio
    async def test_register_model_success(self, test_client, sample_model_config):
        """Test successful model registration."""
        from src.models import ModelConfig, ModelInfo, ModelStatus
        
        # Create a valid model config dictionary
        model_config_data = {
            "model_id": "test-model-1",
            "model_type": "test-type",
            "model_path": "/path/to/model",
            "framework": "test-framework",
            "input_shape": [1, 10],
            "output_shape": [1, 2],
            "metadata": {"test": "test"}
        }
        
        # Create a model config object for the mock return value
        model_config = ModelConfig(**model_config_data)
        
        # Mock the MCP host
        mock_host = AsyncMock()
        mock_host.register_model.return_value = ModelInfo(
            model_id="test-model-1",
            status=ModelStatus.READY,
            config=model_config,
            metrics={"accuracy": 0.95},
            metadata={"test": "test"}
        )
        
        # Patch the mcp_host in the main module
        with patch('src.main.mcp_host', mock_host):
            # Test successful registration
            response = test_client.post(
                "/mcp/register",
                json=model_config_data,
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "model_id" in data
            assert data["model_id"] == "test-model-1"
            assert "status" in data
            assert data["status"] == "ready"
            mock_host.register_model.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_register_model_validation_error(self, test_client):
        """Test model registration with invalid data."""
        # Mock the MCP host
        mock_host = AsyncMock()
        
        # Patch the mcp_host in the main module
        with patch('src.main.mcp_host', mock_host):
            response = test_client.post(
                "/mcp/register",
                json={"invalid": "config"},
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_predict_success(self, test_client):
        """Test successful prediction."""
        from src.models import PredictionResponse, PredictionRequest
        from src.protocol import MCPHost
        
        # Create a valid prediction request
        prediction_request = {
            "model_id": "test-model-1",
            "input_data": {"text": "This is a test input"},
            "parameters": {}
        }
        
        # Create a mock prediction response
        mock_prediction = PredictionResponse(
            model_id="test-model-1",
            request_id="test-request-123",
            output_data={"label": "positive"},
            metadata={"inference_time": 0.1}
        )
        
        # Mock the MCP host's predict method
        mock_host = AsyncMock()
        mock_host.predict.return_value = mock_prediction
        
        # Patch the mcp_host in the main module
        with patch('src.main.mcp_host', mock_host):
            # Test successful prediction
            response = test_client.post(
                "/mcp/predict",
                json=prediction_request,
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "model_id" in data
            assert data["model_id"] == "test-model-1"
            assert "request_id" in data
            assert data["request_id"] == "test-request-123"
            assert "output_data" in data
            assert data["output_data"]["label"] == "positive"
    
    @pytest.mark.asyncio
    async def test_predict_invalid_request(self, test_client):
        """Test prediction with invalid request data."""
        response = test_client.post(
            "/mcp/predict",
            json={"invalid": "request"},
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestDataEndpoints:
    """Test cases for the data access endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_data_sources(self, test_client):
        """Test getting data sources."""
        from src.main import mcp_client
        
        # Mock the get_data_sources method
        mock_data = [
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
        
        with patch.object(mcp_client, 'get_data_sources', new_callable=AsyncMock, return_value=mock_data) as mock_get_data_sources:
            response = test_client.get("/api/data/sources")
            
            # Check the response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert isinstance(data, list)
            if data:
                assert "id" in data[0]
                assert "name" in data[0]
            
            # Verify the mock was called
            mock_get_data_sources.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_get_data_items(self, test_client):
        """Test getting data items."""
        from src.main import mcp_client
        
        # Mock the query_data_items method
        mock_response = {
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
        
        with patch.object(mcp_client, 'query_data_items', new_callable=AsyncMock, return_value=mock_response) as mock_query_data_items:
            response = test_client.get(
                "/api/data/items",
                params={
                    "source_id": "test-source",
                    "limit": 10,
                    "offset": 0,
                },
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert isinstance(data["items"], list)
            
            if data["items"]:
                item = data["items"][0]
                assert "id" in item
                assert "sourceId" in item
                assert "data" in item
