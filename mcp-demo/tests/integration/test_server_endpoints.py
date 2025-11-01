"""Integration tests for the MCP server endpoints."""
import pytest
from fastapi import status, Request
from fastapi.testclient import TestClient
from mcp.server import app, MCPServer
from mcp.models import TextRequest, TextResponse, BatchTextRequest, BatchTextResponse
from unittest.mock import patch, MagicMock

def test_process_batch_endpoint(async_client):
    """Test the /process_batch endpoint with multiple texts."""
    # Prepare test data
    test_texts = ["Hello world!", "Testing batch processing", "Another test"]
    request_data = BatchTextRequest(
        texts=test_texts,
        params={"to_upper": True},
        max_concurrent=2
    ).model_dump()
    
    # Make the request
    response = async_client.post("/process_batch", json=request_data)
    
    # Assert the response
    assert response.status_code == status.HTTP_200_OK
    
    # Parse the response
    response_data = response.json()
    assert "success" in response_data
    assert "results" in response_data
    assert "processed_count" in response_data
    assert response_data["success"] is True
    assert response_data["processed_count"] == len(test_texts)
    
    # Verify each result
    for i, result in enumerate(response_data["results"]):
        assert "success" in result
        assert "text" in result
        assert result["text"] == test_texts[i]
        
        if result["success"]:
            assert "result" in result
            assert "original_text" in result["result"]
            assert "results" in result["result"]
        else:
            assert "error" in result

def test_process_batch_with_invalid_input(async_client):
    """Test the /process_batch endpoint with invalid input."""
    # Test with empty texts list
    request_data = BatchTextRequest(texts=[], max_concurrent=1).model_dump()
    response = async_client.post("/process_batch", json=request_data)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["processed_count"] == 0
    assert response_data["results"] == []
    
    # Test with invalid max_concurrent - this should be caught by Pydantic validation
    # so we'll test with a value that's too low
    request_data = {
        "texts": ["test"],
        "max_concurrent": 0  # Should be at least 1
    }
    response = async_client.post("/process_batch", json=request_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    # Test with invalid text input (not a string)
    request_data = {
        "texts": [123, 456],  # Should be a list of strings
        "max_concurrent": 1
    }
    response = async_client.post("/process_batch", json=request_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

def test_process_batch_with_mixed_results(async_client):
    """Test the /process_batch endpoint with some failing requests."""
    # Prepare test data with one case that will fail due to validation
    test_texts = [
        "This is a test",  # Will be processed successfully
        "",  # Empty string should be handled gracefully
        "This is another test"  # Will be processed successfully
    ]
    
    request_data = BatchTextRequest(
        texts=test_texts,
        max_concurrent=2
    ).model_dump()
    
    # Make the request
    response = async_client.post("/process_batch", json=request_data)
    
    # Assert the response
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    
    # Verify the overall response structure
    assert "success" in response_data
    assert "results" in response_data
    assert "processed_count" in response_data
    
    # The empty string should be filtered out by the text processor
    assert response_data["processed_count"] == 3
    assert len(response_data["results"]) == 3
    
    # Check that we have the expected number of successful and failed results
    results = response_data["results"]
    success_count = sum(1 for r in results if r.get("success"))
    assert success_count >= 2  # At least 2 should succeed
    
    # Check that the text processor was applied to successful results
    for result in results:
        if result["success"] and result["text"]:  # Only check non-empty successful results
            assert "result" in result
            assert "results" in result["result"]
            assert "text_processor" in result["result"]["results"]
            # Check that we have the expected text processor fields
            text_processor_result = result["result"]["results"]["text_processor"]
            assert "original_text" in text_processor_result
            assert "length" in text_processor_result
            assert "word_count" in text_processor_result
            assert "line_count" in text_processor_result
