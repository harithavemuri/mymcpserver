"""Tests for the API endpoints with the new data models."""
import pytest
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status

from src.models import (
    Customer, PersonalInfo, Address, Employment, 
    CallTranscript, TranscriptEntry, Sentiment,
    CustomerListResponse, TranscriptListResponse
)
from src.main import app

# Test data
TEST_CUSTOMER_DATA = {
    "customerId": "CUST123",
    "personalInfo": {
        "firstName": "John",
        "lastName": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890"
    },
    "homeAddress": {
        "street": "123 Main St",
        "city": "Anytown",
        "state": "CA",
        "postalCode": "12345"
    },
    "employment": {
        "company": "ACME Corp",
        "position": "Software Engineer"
    }
}

TEST_TRANSCRIPT_DATA = {
    "callId": "CALL456",
    "customerId": "CUST123",
    "callType": "support",
    "callTimestamp": "2023-01-15T14:30:00Z",
    "callDurationSeconds": 300,
    "agentId": "AGENT789",
    "callSummary": "Customer had questions about their account",
    "isAdaRelated": False,
    "adaViolationOccurred": False,
    "transcript": [
        {
            "speaker": "agent",
            "text": "Thank you for calling support. How can I help you today?",
            "timestamp": "2023-01-15T14:30:00Z"
        },
        {
            "speaker": "customer",
            "text": "I have questions about my account balance.",
            "timestamp": "2023-01-15T14:31:00Z"
        }
    ],
    "sentiment": {
        "polarity": 0.8,
        "subjectivity": 0.7,
        "analyzer": "vader"
    },
    "contexts": ["account_inquiry", "billing"]
}

@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client."""
    with patch('src.main.mcp_client') as mock:
        yield mock

@pytest.fixture
def client():
    """Create a test client."""
    return httpx.AsyncClient(app=app, base_url="http://test")

@pytest.mark.asyncio
async def test_get_customer(client, mock_mcp_client):
    """Test getting a customer by ID."""
    # Setup mock
    customer = Customer(**TEST_CUSTOMER_DATA)
    mock_mcp_client.get_customer = AsyncMock(return_value=customer)
    
    # Make request
    response = await client.get("/api/customers/CUST123")
    
    # Verify response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["customerId"] == "CUST123"
    assert data["personalInfo"]["firstName"] == "John"
    
    # Verify the client was called correctly
    mock_mcp_client.get_customer.assert_awaited_once_with("CUST123")

@pytest.mark.asyncio
async def test_search_customers(client, mock_mcp_client):
    """Test searching for customers."""
    # Setup mock
    customer = Customer(**TEST_CUSTOMER_DATA)
    mock_response = CustomerListResponse(
        items=[customer],
        total_count=1,
        has_next_page=False
    )
    mock_mcp_client.search_customers = AsyncMock(return_value=mock_response)
    
    # Make request
    params = {
        "name": "John Doe",
        "state": "CA",
        "limit": 10,
        "offset": 0
    }
    response = await client.get("/api/customers", params=params)
    
    # Verify response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["customerId"] == "CUST123"
    assert data["totalCount"] == 1
    assert not data["hasNextPage"]
    
    # Verify the client was called correctly
    mock_mcp_client.search_customers.assert_awaited_once_with(
        name="John Doe",
        state="CA",
        transcript_text=None,
        limit=10,
        offset=0
    )

@pytest.mark.asyncio
async def test_get_transcript(client, mock_mcp_client):
    """Test getting a transcript by ID."""
    # Setup mock
    transcript = CallTranscript(**TEST_TRANSCRIPT_DATA)
    mock_mcp_client.get_transcript = AsyncMock(return_value=transcript)
    
    # Make request
    response = await client.get("/api/transcripts/CALL456")
    
    # Verify response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["callId"] == "CALL456"
    assert data["customerId"] == "CUST123"
    assert len(data["transcript"]) == 2
    
    # Verify the client was called correctly
    mock_mcp_client.get_transcript.assert_awaited_once_with("CALL456")

@pytest.mark.asyncio
async def test_search_transcripts(client, mock_mcp_client):
    """Test searching for transcripts."""
    # Setup mock
    transcript = CallTranscript(**TEST_TRANSCRIPT_DATA)
    mock_response = TranscriptListResponse(
        items=[transcript],
        total_count=1,
        has_next_page=False
    )
    mock_mcp_client.search_transcripts = AsyncMock(return_value=mock_response)
    
    # Make request
    params = {
        "customer_id": "CUST123",
        "start_date": "2023-01-01",
        "end_date": "2023-01-31",
        "limit": 10,
        "offset": 0
    }
    response = await client.get("/api/transcripts", params=params)
    
    # Verify response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["callId"] == "CALL456"
    assert data["totalCount"] == 1
    assert not data["hasNextPage"]
    
    # Verify the client was called correctly
    mock_mcp_client.search_transcripts.assert_awaited_once_with(
        customer_id="CUST123",
        agent_id=None,
        start_date="2023-01-01",
        end_date="2023-01-31",
        limit=10,
        offset=0
    )

@pytest.mark.asyncio
async def test_get_customer_with_transcripts(client, mock_mcp_client):
    """Test getting a customer with their transcripts."""
    # Setup mocks
    customer = Customer(**TEST_CUSTOMER_DATA)
    transcript = CallTranscript(**TEST_TRANSCRIPT_DATA)
    
    mock_mcp_client.get_customer = AsyncMock(return_value=customer)
    mock_mcp_client.search_transcripts = AsyncMock(return_value=TranscriptListResponse(
        items=[transcript],
        total_count=1,
        has_next_page=False
    ))
    
    # Make request
    response = await client.get("/api/customers/CUST123/transcripts")
    
    # Verify response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["customerId"] == "CUST123"
    assert len(data["transcripts"]) == 1
    assert data["transcripts"][0]["callId"] == "CALL456"
    
    # Verify the client was called correctly
    mock_mcp_client.get_customer.assert_awaited_once_with("CUST123")
    mock_mcp_client.search_transcripts.assert_awaited_once_with(customer_id="CUST123")
