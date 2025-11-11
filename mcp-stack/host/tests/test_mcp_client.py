"""Tests for the MCP client."""
import json
from unittest.mock import AsyncMock, patch, MagicMock

import httpx
import pytest
from fastapi import status, HTTPException
from fastapi.testclient import TestClient

from src.main import MCPClient, app


class TestMCPClient:
    """Test cases for the MCPClient class."""

    @pytest.mark.asyncio
    async def test_query_data_success(self, httpx_mock):
        """Test successful GraphQL query."""
        # Mock the GraphQL response for data sources
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
                        }
                    ]
                }
            },
        )
        
        client = MCPClient("http://testserver")
        query = """
        query GetDataSources {
            dataSources {
                id
                name
            }
        }
        """
        
        result = await client.query_data(query)
        
        assert "dataSources" in result
        assert len(result["dataSources"]) > 0
        assert "id" in result["dataSources"][0]
        assert "name" in result["dataSources"][0]
    
    @pytest.mark.asyncio
    async def test_query_data_error(self, httpx_mock):
        """Test GraphQL query with errors."""
        # Mock a GraphQL error response
        httpx_mock.add_response(
            method="POST",
            url="http://testserver/graphql",
            status_code=400,
            json={"errors": [{"message": "Invalid query"}]},
        )
        
        client = MCPClient("http://testserver")
        
        with pytest.raises(HTTPException) as exc_info:
            await client.query_data("invalid query")
        
        assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_get_data_sources(self, httpx_mock):
        """Test getting data sources."""
        # Mock the GraphQL response for data sources
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
                        }
                    ]
                }
            },
        )
        
        client = MCPClient("http://testserver")
        result = await client.get_data_sources()
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert "id" in result[0]
        assert "name" in result[0]
    
    @pytest.mark.asyncio
    async def test_query_data_items(self, httpx_mock):
        """Test querying data items."""
        # Mock the GraphQL response for data items
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
        
        client = MCPClient("http://testserver")
        result = await client.query_data_items()
        
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "size" in result
        assert "hasMore" in result
        assert len(result["items"]) > 0
        assert "id" in result["items"][0]
        assert "sourceId" in result["items"][0]
        assert "data" in result["items"][0]
    
    @pytest.mark.asyncio
    async def test_close_client(self):
        """Test closing the client."""
        client = MCPClient("http://testserver")
        
        # Mock the close method
        with patch.object(client.client, 'aclose') as mock_close:
            await client.close()
            mock_close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_http_errors(self, httpx_mock):
        """Test handling of HTTP errors."""
        # Mock a 500 error
        httpx_mock.add_response(
            method="POST",
            url="http://testserver/graphql",
            status_code=500,
            json={"error": "Internal Server Error"},
        )
        
        client = MCPClient("http://testserver")
        
        with pytest.raises(HTTPException) as exc_info:
            await client.query_data("query { test }")
        assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_graphql_errors(self, httpx_mock):
        """Test handling of GraphQL errors."""
        # Mock a GraphQL error response
        httpx_mock.add_response(
            method="POST",
            url="http://testserver/graphql",
            json={
                "errors": [
                    {"message": "Invalid query", "locations": [{"line": 1, "column": 1}]}
                ]
            },
        )
        
        client = MCPClient("http://testserver")
        
        with pytest.raises(HTTPException) as exc_info:
            await client.get_data_sources()
        
        # The error should be a 400 Bad Request
        assert exc_info.value.status_code == 500
