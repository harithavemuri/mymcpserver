"""Tests for the MCP client with the new data models."""
import pytest
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, patch, MagicMock

from src.models import (
    Customer, PersonalInfo, Address, Employment,
    CallTranscript, TranscriptEntry, Sentiment,
    CustomerListResponse, TranscriptListResponse
)
from src.main import MCPClient

# Test data
TEST_CUSTOMER_DATA = {
    "customerId": "CUST123",
    "personalInfo": {
        "firstName": "John",
        "lastName": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "dateOfBirth": "1980-01-01"
    },
    "homeAddress": {
        "street": "123 Main St",
        "city": "Anytown",
        "state": "CA",
        "postalCode": "12345",
        "country": "USA"
    },
    "employment": {
        "company": "ACME Corp",
        "position": "Software Engineer",
        "workEmail": "john.doe@acme.com",
        "workPhone": "+1987654321",
        "workAddress": {
            "street": "456 Work Ave",
            "city": "Businesstown",
            "state": "CA",
            "postalCode": "54321",
            "country": "USA"
        }
    },
    "createdAt": "2023-01-01T00:00:00Z",
    "updatedAt": "2023-01-02T00:00:00Z"
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
def mock_client():
    """Create a mock MCP client."""
    client = MCPClient(base_url="http://test-server", api_key="test-api-key")
    client.query_data = AsyncMock()
    return client

@pytest.mark.asyncio
async def test_get_customer(mock_client):
    """Test getting a customer by ID."""
    # Mock the response from the server
    mock_client.query_data.return_value = {"getCustomer": TEST_CUSTOMER_DATA}

    # Call the method under test
    customer = await mock_client.get_customer("CUST123")

    # Verify the result
    assert isinstance(customer, Customer)
    assert customer.customer_id == "CUST123"
    assert customer.personal_info.first_name == "John"
    assert customer.personal_info.last_name == "Doe"
    assert customer.home_address.city == "Anytown"
    assert customer.employment.company == "ACME Corp"
    assert customer.created_at == datetime(2023, 1, 1, tzinfo=timezone.utc)

    # Verify the query was made correctly
    mock_client.query_data.assert_awaited_once()
    args, kwargs = mock_client.query_data.await_args
    assert "getCustomer" in kwargs["query"]
    assert kwargs["variables"] == {"customerId": "CUST123"}

@pytest.mark.asyncio
async def test_search_customers(mock_client):
    """Test searching for customers."""
    # Mock the response from the server
    mock_client.query_data.return_value = {
        "searchCustomers": [TEST_CUSTOMER_DATA]
    }

    # Call the method under test
    response = await mock_client.search_customers(
        name="John Doe",
        state="CA",
        transcript_text="account",
        limit=10,
        offset=0
    )

    # Verify the result
    assert isinstance(response, CustomerListResponse)
    assert len(response.items) == 1
    customer = response.items[0]
    assert customer.customer_id == "CUST123"

    # Verify the query was made correctly
    mock_client.query_data.assert_awaited_once()
    args, kwargs = mock_client.query_data.await_args
    assert "searchCustomers" in kwargs["query"]
    assert kwargs["variables"] == {
        "name": "John Doe",
        "state": "CA",
        "transcriptText": "account",
        "limit": 10,
        "offset": 0
    }

@pytest.mark.asyncio
async def test_get_transcript(mock_client):
    """Test getting a transcript by ID."""
    # Mock the response from the server
    mock_client.query_data.return_value = {"getTranscript": TEST_TRANSCRIPT_DATA}

    # Call the method under test
    transcript = await mock_client.get_transcript("CALL456")

    # Verify the result
    assert isinstance(transcript, CallTranscript)
    assert transcript.call_id == "CALL456"
    assert transcript.customer_id == "CUST123"
    assert transcript.call_type == "support"
    assert len(transcript.transcript) == 2
    assert transcript.transcript[0].speaker == "agent"
    assert transcript.sentiment.polarity == 0.8
    assert "account_inquiry" in transcript.contexts

    # Verify the query was made correctly
    mock_client.query_data.assert_awaited_once()
    args, kwargs = mock_client.query_data.await_args
    assert "getTranscript" in kwargs["query"]
    assert kwargs["variables"] == {"callId": "CALL456"}

@pytest.mark.asyncio
async def test_search_transcripts(mock_client):
    """Test searching for transcripts."""
    # Mock the response from the server
    mock_client.query_data.return_value = {
        "searchTranscripts": [TEST_TRANSCRIPT_DATA]
    }

    # Call the method under test
    response = await mock_client.search_transcripts(
        customer_id="CUST123",
        agent_id="AGENT789",
        start_date="2023-01-01",
        end_date="2023-01-31",
        limit=10,
        offset=0
    )

    # Verify the result
    assert isinstance(response, TranscriptListResponse)
    assert len(response.items) == 1
    transcript = response.items[0]
    assert transcript.call_id == "CALL456"
    assert transcript.customer_id == "CUST123"

    # Verify the query was made correctly
    mock_client.query_data.assert_awaited_once()
    args, kwargs = mock_client.query_data.await_args
    assert "searchTranscripts" in kwargs["query"]
    assert kwargs["variables"] == {
        "customerId": "CUST123",
        "agentId": "AGENT789",
        "startDate": "2023-01-01",
        "endDate": "2023-01-31",
        "limit": 10,
        "offset": 0
    }

@pytest.mark.asyncio
async def test_get_customer_with_transcripts(mock_client):
    """Test getting a customer with their transcripts."""
    # Mock the responses from the server
    mock_client.get_customer = AsyncMock(return_value=Customer(**TEST_CUSTOMER_DATA))
    mock_client.search_transcripts = AsyncMock(return_value=TranscriptListResponse(
        items=[CallTranscript(**TEST_TRANSCRIPT_DATA)],
        total_count=1,
        has_next_page=False
    ))

    # Call the method under test
    customer = await mock_client.get_customer_with_transcripts("CUST123")

    # Verify the result
    assert customer.customer_id == "CUST123"
    assert len(customer.transcripts) == 1
    assert customer.transcripts[0].call_id == "CALL456"

    # Verify the methods were called correctly
    mock_client.get_customer.assert_awaited_once_with("CUST123")
    mock_client.search_transcripts.assert_awaited_once_with(customer_id="CUST123")
