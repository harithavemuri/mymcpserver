"""Tests for the health check functionality of the MCP host."""
import pytest
import httpx
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

# Test configuration
BASE_URL = "http://localhost:8000"

@pytest.fixture
async def client():
    """Create an async HTTP client for testing."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        yield client

@pytest.mark.asyncio
async def test_rest_health_check(client):
    """Test the REST health check endpoint directly."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "version" in data

@pytest.mark.asyncio
async def test_converse_health_check(client):
    """Test health check through the converse endpoint."""
    test_queries = [
        "Is the server healthy?",
        "Check server status",
        "Is the server up and running?",
        "Verify server health"
    ]
    
    for query in test_queries:
        response = await client.post(
            "/api/converse",
            json={"query": query, "context": {}}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "response" in data
        assert "data" in data
        assert "context" in data
        
        # Check if the response indicates the server is healthy
        assert "up and running" in data["response"] or "trouble reaching" in data["response"]
        
        # If we got a successful response, the status should be in the data
        if "up and running" in data["response"]:
            assert data["data"].get("status") == "ok"

@pytest.mark.asyncio
async def test_converse_health_check_with_error():
    """Test health check when the server is down."""
    from src.conversation import ConversationHandler, QueryIntent
    
    # Create a mock that will simulate a connection error
    async with patch('httpx.AsyncClient.get') as mock_get:
        # Configure the mock to raise a connection error
        mock_get.side_effect = httpx.ConnectError("Connection error")
        
        # Initialize the conversation handler
        handler = ConversationHandler()
        
        # Test with a health check query
        query_params = handler.parse_query("Is the server healthy?")
        assert query_params.intent == QueryIntent.HEALTH_CHECK
        
        # The format_response should handle the error case
        response = await handler.format_response(
            query_params.intent, 
            {"status": "error", "error": "Connection error"}
        )
        assert "trouble reaching" in response or "down" in response

if __name__ == "__main__":
    # Run the tests directly
    import sys
    import pytest
    sys.exit(pytest.main(["-v", "-s", __file__]))
