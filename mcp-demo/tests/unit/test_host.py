"""Unit tests for the MCP host functionality."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from mcp.host import MPCHost
from mcp.models import TextRequest, TextResponse, ProcessingResult

@pytest.mark.asyncio
async def test_host_initialization():
    """Test that the MPCHost initializes correctly."""
    async with MPCHost(base_url="http://test-server") as host:
        assert host.base_url == "http://test-server"
        # The client's base_url should be exactly what was passed in
        assert str(host.client.base_url) == "http://test-server"

@pytest.mark.asyncio
async def test_health_check_success():
    """Test the health check method with a successful response."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "ok"}

    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        async with MPCHost() as host:
            is_healthy = await host.health_check()
            assert is_healthy is True
            mock_get.assert_called_once_with("/health")

@pytest.mark.asyncio
async def test_process_text_success():
    """Test the process_text method with a successful response."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "success": True,
        "result": {
            "original_text": "test",
            "results": {"text_processor": {"processed_text": "TEST"}},
            "metadata": {"tools_executed": ["text_processor"]}
        }
    }

    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        async with MPCHost() as host:
            response = await host.process_text("test")
            assert response.success is True
            assert response.result.original_text == "test"
            assert "text_processor" in response.result.results
            mock_post.assert_called_once()

@pytest.mark.asyncio
async def test_process_texts_batch():
    """Test the process_texts method with multiple texts."""
    # Create the expected response objects
    response1 = TextResponse(
        success=True,
        result=ProcessingResult(
            original_text="test1",
            results={"text_processor": {"processed_text": "TEST1"}},
            metadata={"tools_executed": ["text_processor"]},
            current_tool=None,
            error=None
        )
    )

    response2 = TextResponse(
        success=True,
        result=ProcessingResult(
            original_text="test2",
            results={"text_processor": {"processed_text": "TEST2"}},
            metadata={"tools_executed": ["text_processor"]},
            current_tool=None,
            error=None
        )
    )

    # Create a mock for the process_text method
    async def mock_process_text(text, params=None):
        if text == "test1":
            return response1
        elif text == "test2":
            return response2
        return TextResponse(success=False, error="Unexpected input")

    # Patch the process_text method
    with patch.object(MPCHost, 'process_text', side_effect=mock_process_text):
        async with MPCHost() as host:
            # Call the method under test
            results = await host.process_texts(["test1", "test2"])

            # Verify the results
            assert len(results) == 2
            assert all(isinstance(r, TextResponse) for r in results)

            # Check the first result
            assert results[0].success is True
            assert results[0].result.original_text == "test1"
            assert results[0].result.results["text_processor"]["processed_text"] == "TEST1"

            # Check the second result
            assert results[1].success is True
            assert results[1].result.original_text == "test2"
            assert results[1].result.results["text_processor"]["processed_text"] == "TEST2"
