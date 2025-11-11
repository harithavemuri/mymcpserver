import pytest
import httpx
import json
from typing import Dict, Any, List
import os
from datetime import datetime, timedelta

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_API_KEY = os.getenv("MCP_API_KEY", "test-api-key")

# Test data
TEST_CUSTOMER = {
    "customerId": "TEST123",
    "firstName": "Test",
    "lastName": "User",
    "email": "test.user@example.com",
    "phone": "+1234567890",
    "address": "123 Test St",
    "city": "Testville",
    "state": "TS",
    "postalCode": "12345",
    "country": "Testland"
}

# Test fixtures
@pytest.fixture(scope="module")
async def client():
    """Create an async HTTP client for testing."""
    async with httpx.AsyncClient(
        base_url=BASE_URL,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TEST_API_KEY}"
        },
        timeout=30.0
    ) as client:
        yield client

@pytest.fixture(scope="module")
def test_customer_id() -> str:
    """Return a unique test customer ID."""
    return f"TEST_{int(datetime.utcnow().timestamp())}"

# Helper functions
async def create_test_customer(client: httpx.AsyncClient, customer_data: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to create a test customer."""
    response = await client.post("/customers", json=customer_data)
    assert response.status_code in [200, 201], f"Failed to create test customer: {response.text}"
    return response.json()

# Test cases
class TestMCPClientREST:
    async def test_health_check(self, client: httpx.AsyncClient):
        """Test the health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    async def test_create_and_get_customer(self, client: httpx.AsyncClient, test_customer_id: str):
        """Test creating and retrieving a customer."""
        # Create test customer
        customer_data = TEST_CUSTOMER.copy()
        customer_data["customerId"] = test_customer_id
        
        # Test create customer
        create_response = await client.post("/customers", json=customer_data)
        assert create_response.status_code in [200, 201], f"Failed to create customer: {create_response.text}"
        created_customer = create_response.json()
        assert created_customer["customerId"] == test_customer_id
        
        # Test get customer
        get_response = await client.get(f"/customers/{test_customer_id}")
        assert get_response.status_code == 200
        fetched_customer = get_response.json()
        assert fetched_customer["customerId"] == test_customer_id
        assert fetched_customer["email"] == customer_data["email"]

    async def test_search_customers(self, client: httpx.AsyncClient, test_customer_id: str):
        """Test searching for customers."""
        # Search by ID
        response = await client.get(f"/customers/search?q={test_customer_id}")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert any(cust["customerId"] == test_customer_id for cust in data["data"])
        
        # Search by state
        response = await client.get("/customers/search?state=TS")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0

    async def test_get_customer_transcripts(self, client: httpx.AsyncClient, test_customer_id: str):
        """Test retrieving a customer's transcripts."""
        response = await client.get(f"/customers/{test_customer_id}/transcripts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)  # Should return a list of transcripts

    async def test_list_all_customers(self, client: httpx.AsyncClient):
        """Test listing all customers with pagination."""
        response = await client.get("/customers?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert isinstance(data["data"], list)
        assert "total" in data["pagination"]
        assert "limit" in data["pagination"]
        assert "offset" in data["pagination"]

    async def test_update_customer(self, client: httpx.AsyncClient, test_customer_id: str):
        """Test updating a customer's information."""
        update_data = {"phone": "+1987654321"}
        response = await client.put(
            f"/customers/{test_customer_id}",
            json=update_data
        )
        assert response.status_code == 200
        updated_customer = response.json()
        assert updated_customer["phone"] == "+1987654321"

    async def test_delete_customer(self, client: httpx.AsyncClient, test_customer_id: str):
        """Test deleting a customer."""
        # First create a customer to delete
        customer_data = TEST_CUSTOMER.copy()
        customer_data["customerId"] = f"DELETE_{test_customer_id}"
        await create_test_customer(client, customer_data)
        
        # Test delete
        delete_response = await client.delete(f"/customers/DELETE_{test_customer_id}")
        assert delete_response.status_code in [200, 204]
        
        # Verify deletion
        get_response = await client.get(f"/customers/DELETE_{test_customer_id}")
        assert get_response.status_code == 404

# Run tests with: pytest -v tests/test_mcp_client_rest.py -s
