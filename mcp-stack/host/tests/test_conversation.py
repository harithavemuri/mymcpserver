"""Tests for the conversation endpoints."""
import pytest
import httpx
import json
from typing import Dict, Any, List

# Base URL for the API
BASE_URL = "http://localhost:8000/conversation"

def validate_conversation_response(response_data: Dict[str, Any]) -> None:
    """Helper function to validate conversation response structure."""
    assert isinstance(response_data, dict), "Response should be a dictionary"
    assert "response" in response_data, "Response should contain 'response' field"
    assert "client_used" in response_data, "Response should contain 'client_used' field"
    assert "metadata" in response_data, "Response should contain 'metadata' field"
    assert isinstance(response_data["response"], str), "Response field should be a string"
    assert response_data["client_used"] in ["customer", "fallback", "text_transform"], "Invalid client_used value"
    assert isinstance(response_data["metadata"], dict), "Metadata should be a dictionary"

@pytest.mark.asyncio
async def test_post_process_conversation():
    """Test the POST /process endpoint with a valid request."""
    test_cases = [
        # Minimal valid request
        {
            "messages": [{"role": "user", "content": "Show me all customers"}]
        },
        # Multiple messages
        {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Show me all customers"}
            ]
        },
        # With empty context
        {
            "messages": [{"role": "user", "content": "Show me all customers"}],
            "context": {}
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for test_case in test_cases:
            response = await client.post(
                f"{BASE_URL}/process",
                json=test_case,
                timeout=10.0
            )
            assert response.status_code == 200, f"Failed with input: {test_case}"
            data = response.json()
            validate_conversation_response(data)

@pytest.mark.asyncio
async def test_post_process_conversation_with_context():
    """Test the POST /process endpoint with various context scenarios."""
    test_cases = [
        # Simple context
        {
            "messages": [{"role": "user", "content": "Show me all customers"}],
            "context": {"user_id": "12345"}
        },
        # Nested context
        {
            "messages": [{"role": "user", "content": "Show me all customers"}],
            "context": {
                "user": {"id": "12345", "name": "Test User"},
                "session": {"id": "session_123", "timestamp": "2023-01-01"}
            }
        },
        # Context with metadata in messages
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Show me all customers",
                    "metadata": {"source": "web", "version": "1.0"}
                }
            ],
            "context": {"app": {"version": "1.0.0", "environment": "test"}}
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for test_case in test_cases:
            response = await client.post(
                f"{BASE_URL}/process",
                json=test_case,
                timeout=10.0
            )
            assert response.status_code == 200, f"Failed with context: {test_case['context']}"
            data = response.json()
            validate_conversation_response(data)
            
            # Verify context was processed (if the endpoint modifies/uses it)
            if "context" in test_case and test_case["context"]:
                assert "context" in data.get("metadata", {}), "Response metadata should include context"

@pytest.mark.asyncio
async def test_post_process_invalid_request():
    """Test the POST /process endpoint with various invalid requests."""
    test_cases = [
        # Missing messages field
        ({"invalid": "request"}, 422, "missing messages field"),
        # Empty messages array
        ({"messages": []}, 400, "empty messages array"),
        # Invalid message structure
        ({"messages": [{"wrong_key": "value"}]}, 422, "invalid message structure"),
        # Missing content in message
        ({"messages": [{"role": "user"}]}, 422, "missing content in message"),
        # Invalid role
        ({"messages": [{"role": "invalid_role", "content": "test"}]}, 422, "invalid role")
    ]
    
    async with httpx.AsyncClient() as client:
        for payload, expected_status, description in test_cases:
            response = await client.post(
                f"{BASE_URL}/process",
                json=payload,
                timeout=10.0
            )
            assert response.status_code == expected_status, f"Failed test case: {description}"
            
            # For validation errors, check the error structure
            if expected_status == 422:
                error_data = response.json()
                assert "detail" in error_data, "Error response should contain 'detail' field"
                assert len(error_data["detail"]) > 0, "Error details should not be empty"

@pytest.mark.asyncio
async def test_get_process_conversation():
    """Test the GET /process endpoint with various parameters."""
    test_cases = [
        # Basic GET request
        ({"message": "Show me all customers"}, 200),
        # With explicit role
        ({"message": "Show me all customers", "role": "user"}, 200),
        # With different roles
        ({"message": "Show me all customers", "role": "admin"}, 200),
        # With URL-encoded message
        ({"message": "Show me customers from NY", "role": "user"}, 200)
    ]
    
    async with httpx.AsyncClient() as client:
        for params, expected_status in test_cases:
            response = await client.get(
                f"{BASE_URL}/process",
                params=params,
                timeout=10.0
            )
            assert response.status_code == expected_status, f"Failed with params: {params}"
            
            if expected_status == 200:
                data = response.json()
                validate_conversation_response(data)
                
                # Verify the response contains the original message or part of it
                original_message = params["message"].lower()
                response_text = data["response"].lower()
                # At least one word from the original message should be in the response
                assert any(word in response_text for word in original_message.split() if len(word) > 3), \
                    f"Response should relate to the original message. Original: '{original_message}', Response: '{response_text}'"

@pytest.mark.asyncio
async def test_get_process_error_cases():
    """Test the GET /process endpoint with various error cases."""
    test_cases = [
        # Missing message parameter
        ({}, 422, "missing message parameter"),
        # Empty message
        ({"message": ""}, 400, "empty message"),
        # Message with only whitespace
        ({"message": "   "}, 400, "whitespace only message"),
        # Message too long
        ({"message": "a" * 1001}, 422, "message too long")
    ]
    
    async with httpx.AsyncClient() as client:
        for params, expected_status, description in test_cases:
            response = await client.get(
                f"{BASE_URL}/process",
                params=params,
                timeout=10.0
            )
            assert response.status_code == expected_status, f"Failed test case: {description}"
            
            # For validation errors, check the error structure
            if expected_status == 422:
                error_data = response.json()
                assert "detail" in error_data, "Error response should contain 'detail' field"
                assert len(error_data["detail"]) > 0, "Error details should not be empty"

@pytest.mark.asyncio
async def test_conversation_flow():
    """Test a complete conversation flow with multiple turns."""
    async with httpx.AsyncClient() as client:
        # Initial message
        response = await client.post(
            f"{BASE_URL}/process",
            json={
                "messages": [
                    {"role": "user", "content": "Hello, can you help me find customers?"}
                ]
            }
        )
        assert response.status_code == 200
        data1 = response.json()
        validate_conversation_response(data1)
        
        # Follow-up message with conversation context
        response = await client.post(
            f"{BASE_URL}/process",
            json={
                "messages": [
                    {"role": "user", "content": "Hello, can you help me find customers?"},
                    {"role": "assistant", "content": data1["response"]},
                    {"role": "user", "content": "Yes, show me all customers from New York"}
                ]
            }
        )
        assert response.status_code == 200
        data2 = response.json()
        validate_conversation_response(data2)
        
        # Verify the conversation context was maintained
        assert data1["client_used"] == data2["client_used"], \
            "Client used should be consistent in a conversation"
