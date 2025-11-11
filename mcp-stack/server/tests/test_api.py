"""Test cases for the MCP Server API."""
import os
import pytest
import aiohttp
import asyncio
from typing import Dict, Any

# Base URL for the API
BASE_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8005")
GRAPHQL_ENDPOINT = f"{BASE_URL}/graphql"

# Test data
TEST_CUSTOMER_ID = "CUST1000"
TEST_CALL_ID = "CALL1000"

async def make_graphql_query(query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
    """Helper function to make GraphQL queries."""
    headers = {"Content-Type": "application/json"}
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    print(f"\nSending GraphQL request to {GRAPHQL_ENDPOINT}")
    print(f"Query: {query.strip()}")
    if variables:
        print(f"Variables: {variables}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(GRAPHQL_ENDPOINT, json=payload, headers=headers) as response:
                response_data = await response.json()
                print(f"Response status: {response.status}")
                print(f"Response data: {response_data}")
                
                if "errors" in response_data:
                    print(f"GraphQL Errors: {response_data['errors']}")
                
                return response_data
    except Exception as e:
        print(f"Error making GraphQL request: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_health_check():
    """
    Test the health check endpoint.
    
    This test verifies that:
    1. The health endpoint is accessible
    2. Returns a valid response with expected fields
    3. Status is 'ok' when service is healthy
    """
    # Define the GraphQL query
    query = """
    query HealthCheck {
        health {
            status
            timestamp
            version
        }
    }
    """
    
    # Make the request
    response = await make_graphql_query(query)
    
    # Basic response validation
    assert "data" in response, "Response should contain 'data' field"
    assert "health" in response["data"], "Response should contain 'health' field"
    
    # Get health data
    health_data = response["data"]["health"]
    
    # Validate fields
    assert "status" in health_data, "Health response should contain 'status' field"
    assert "timestamp" in health_data, "Health response should contain 'timestamp' field"
    assert "version" in health_data, "Health response should contain 'version' field"
    
    # Validate status
    assert health_data["status"] == "ok", "Health status should be 'ok'"
    
    # Validate timestamp format (ISO 8601)
    try:
        datetime.fromisoformat(health_data["timestamp"].replace('Z', '+00:00'))
    except ValueError:
        pytest.fail(f"Invalid timestamp format: {health_data['timestamp']}")
    
    # Validate version format (semantic versioning)
    import re
    version_pattern = r'^\d+\.\d+\.\d+$'  # Basic semver pattern
    assert re.match(version_pattern, health_data["version"]), \
        f"Version should be in semver format (e.g., 1.0.0), got {health_data['version']}"

@pytest.mark.asyncio
async def test_list_tools():
    """Test listing available tools."""
    query = """
    query {
        listTools {
            id
            name
            description
            category
            isAvailable
        }
    }
    """
    
    response = await make_graphql_query(query)
    assert "data" in response, "Response should contain 'data' field"
    assert "listTools" in response["data"], "Response should contain 'listTools' field"
    assert isinstance(response["data"]["listTools"], list), "Tools should be a list"

@pytest.mark.asyncio
async def test_get_customer():
    """Test retrieving a customer by ID."""
    query = """
    query GetCustomer($customerId: String!) {
        getCustomer(customerId: $customerId) {
            customerId
            firstName
            lastName
            email
        }
    }
    """
    
    variables = {"customerId": TEST_CUSTOMER_ID}
    response = await make_graphql_query(query, variables)
    
    assert "data" in response, "Response should contain 'data' field"
    assert "getCustomer" in response["data"], "Response should contain 'getCustomer' field"
    customer = response["data"]["getCustomer"]
    assert customer is not None, f"Customer with ID {TEST_CUSTOMER_ID} should exist"
    assert customer["customerId"] == TEST_CUSTOMER_ID, "Customer ID should match"

@pytest.mark.asyncio
async def test_get_transcript():
    """Test retrieving a call transcript by ID."""
    query = """
    query GetTranscript($callId: String!) {
        getTranscript(callId: $callId) {
            callId
            customerId
            callTimestamp
            callDurationSeconds
            callSummary
        }
    }
    """
    
    variables = {"callId": TEST_CALL_ID}
    response = await make_graphql_query(query, variables)
    
    assert "data" in response, "Response should contain 'data' field"
    assert "getTranscript" in response["data"], "Response should contain 'getTranscript' field"
    transcript = response["data"]["getTranscript"]
    assert transcript is not None, f"Transcript with ID {TEST_CALL_ID} should exist"
    assert transcript["callId"] == TEST_CALL_ID, "Call ID should match"
    assert int(transcript["callDurationSeconds"]) > 0, "Call duration should be positive"

@pytest.mark.asyncio
async def test_search_customers():
    """Test searching for customers."""
    query = """
    query SearchCustomers($filter: CustomerFilterInput!) {
        searchCustomers(filter: $filter) {
            customerId
            firstName
            lastName
            state
        }
    }
    """
    
    variables = {
        "filter": {
            "state": "CA",
            "limit": 3
        }
    }
    
    response = await make_graphql_query(query, variables)
    
    assert "data" in response, "Response should contain 'data' field"
    assert "searchCustomers" in response["data"], "Response should contain 'searchCustomers' field"
    customers = response["data"]["searchCustomers"]
    assert isinstance(customers, list), "Should return a list of customers"
    
    if customers:  # If there are customers in CA
        for customer in customers:
            assert customer["state"] == "CA", "All customers should be from CA"

# Run the tests
if __name__ == "__main__":
    import pytest
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
