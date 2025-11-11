"""
Simple test script for MCP Client REST API
"""
import asyncio
import httpx
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test-api-key"  # Update with your API key if needed
}

async def test_health():
    """Test health check endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health", headers=HEADERS)
        print("\n=== Health Check ===")
        print(f"Status: {response.status_code}")
        print("Response:", response.json())
        return response.status_code == 200

async def test_list_customers():
    """Test listing customers"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/customers?limit=2",
            headers=HEADERS
        )
        print("\n=== List Customers ===")
        print(f"Status: {response.status_code}")
        print("Response:", json.dumps(response.json(), indent=2))
        return response.status_code == 200

async def test_search_customers():
    """Test searching customers"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/customers/search?limit=2",
            headers=HEADERS
        )
        print("\n=== Search Customers ===")
        print(f"Status: {response.status_code}")
        print("Response:", json.dumps(response.json(), indent=2))
        return response.status_code == 200

async def test_get_customer(customer_id: str):
    """Test getting a specific customer"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/customers/{customer_id}",
            headers=HEADERS
        )
        print(f"\n=== Get Customer {customer_id} ===")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Response:", json.dumps(response.json(), indent=2))
        else:
            print("Error:", response.text)
        return response.status_code == 200

async def test_customer_transcripts(customer_id: str):
    """Test getting customer transcripts"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/customers/{customer_id}/transcripts",
            headers=HEADERS
        )
        print(f"\n=== Get Customer {customer_id} Transcripts ===")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Found {len(response.json())} transcripts")
            if response.json():
                print("First transcript:", json.dumps(response.json()[0], indent=2))
        else:
            print("Error:", response.text)
        return response.status_code == 200

async def main():
    """Run all tests"""
    print("Starting MCP Client REST API Tests...")
    print(f"Base URL: {BASE_URL}")
    
    # Run tests
    await test_health()
    await test_list_customers()
    await test_search_customers()
    
    # Test with a specific customer ID (you may need to update this)
    test_customer_id = "CUST123"
    await test_get_customer(test_customer_id)
    await test_customer_transcripts(test_customer_id)
    
    print("\n=== Tests Complete ===")

if __name__ == "__main__":
    asyncio.run(main())
