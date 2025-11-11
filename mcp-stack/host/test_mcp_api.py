"""
Test script for MCP Client REST API
"""
import asyncio
import httpx
import json
import os
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {
    "Content-Type": "application/json",
}

# Try to get MCP server URL from environment or use default
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8005")
MCP_API_KEY = os.getenv("MCP_API_KEY", "")

async def test_health():
    """Test health check endpoint"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health", headers=HEADERS, timeout=5.0)
            print("\n=== Health Check ===")
            print(f"Status: {response.status_code}")
            print("Response:", response.json())
            return response.status_code == 200
        except Exception as e:
            print(f"Health check failed: {str(e)}")
            return False

async def test_mcp_server_connection() -> bool:
    """Test connection to the MCP server"""
    print("\n=== MCP Server Connection Test ===")
    print(f"MCP Server URL: {MCP_SERVER_URL}")
    
    # Test GraphQL endpoint
    query = """
    query {
        health {
            status
            version
        }
    }
    """
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Content-Type": "application/json"}
            if MCP_API_KEY:
                headers["Authorization"] = f"Bearer {MCP_API_KEY}" 
            
            # Test GraphQL endpoint
            response = await client.post(
                f"{MCP_SERVER_URL}/graphql",
                json={"query": query},
                headers=headers,
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "health" in data["data"]:
                    print("✅ Successfully connected to MCP Server")
                    print(f"Server Status: {data['data']['health']['status']}")
                    print(f"Server Version: {data['data']['health'].get('version', 'unknown')}")
                    return True
                else:
                    print("❌ Unexpected response format from MCP Server:")
                    print(json.dumps(data, indent=2))
            else:
                print(f"❌ Failed to connect to MCP Server (HTTP {response.status_code}):")
                print(response.text)
                
    except Exception as e:
        print(f"❌ Error connecting to MCP Server: {str(e)}")
    
    return False

async def test_get_sources():
    """Test getting available data sources"""
    print("\n=== Data Sources ===")
    print(f"Testing endpoint: {BASE_URL}/api/data/sources")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/api/data/sources",
                headers=HEADERS,
                timeout=5.0
            )
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                sources = response.json()
                print("Available data sources:")
                for source in sources:
                    print(f"- {source['id']}: {source['name']} ({source['description']})")
                return True
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error getting data sources: {str(e)}")
            return False

async def test_get_customers():
    """Test getting customer data"""
    print("\n=== Customer Data ===")
    
    # First try the MCP host endpoint
    print(f"Testing MCP Host endpoint: {BASE_URL}/api/data/items?source_id=customers")
    
    params = {
        "source_id": "customers",
        "limit": 2
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Test MCP host endpoint
            response = await client.get(
                f"{BASE_URL}/api/data/items",
                params=params,
                headers=HEADERS,
                timeout=5.0
            )
            
            print(f"MCP Host Response ({response.status_code}):")
            data = response.json()
            
            if response.status_code == 200:
                items = data.get('items', [])
                print(f"Found {len(items)} customers")
                if items:
                    print("Sample customer:", json.dumps(items[0], indent=2))
                else:
                    print("No customers found. This could be because:")
                    print("1. The MCP server has no customer data")
                    print("2. The MCP host is not properly connected to the MCP server")
                    print(f"3. The MCP server at {MCP_SERVER_URL} is not returning customer data")
                    
                    # Try to query MCP server directly for customers
                    print("\nAttempting to query MCP server directly...")
                    await query_mcp_server_directly("customers")
            else:
                print(f"Error: {response.status_code} - {response.text}")
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error getting customer data: {str(e)}")
            return False

async def query_mcp_server_directly(data_type: str):
    """Query the MCP server directly to check for data"""
    query_map = {
        "customers": """
        query SearchCustomers($limit: Int, $offset: Int) {
            searchCustomers(limit: $limit, offset: $offset) {
                customerId
                firstName
                lastName
                email
                phone
            }
        }
        """,
        "transcripts": """
        query SearchTranscripts($limit: Int, $offset: Int) {
            searchTranscripts(limit: $limit, offset: $offset) {
                callId
                customerId
                callTimestamp
                callSummary
            }
        }
        """
    }
    
    if data_type not in query_map:
        print(f"No direct query available for {data_type}")
        return
    
    query = query_map[data_type]
    variables = {"limit": 2, "offset": 0}
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Content-Type": "application/json"}
            if MCP_API_KEY:
                headers["Authorization"] = f"Bearer {MCP_API_KEY}"
                
            print(f"\nQuerying MCP Server directly at {MCP_SERVER_URL}/graphql")
            print(f"Query: {query.strip()}")
            
            response = await client.post(
                f"{MCP_SERVER_URL}/graphql",
                json={"query": query, "variables": variables},
                headers=headers,
                timeout=5.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if "errors" in result:
                    print("GraphQL errors:")
                    for error in result["errors"]:
                        print(f"- {error.get('message')}")
                else:
                    data = result.get("data", {})
                    items = data.get(f"search{data_type.capitalize()}", [])
                    print(f"Found {len(items)} {data_type} directly from MCP server")
                    if items:
                        print("Sample item:", json.dumps(items[0], indent=2))
            else:
                print(f"Error querying MCP server: {response.status_code}")
                print(response.text)
                
    except Exception as e:
        print(f"Error querying MCP server: {str(e)}")

async def test_get_transcripts():
    """Test getting transcript data"""
    print("\n=== Transcript Data ===")
    
    # First try the MCP host endpoint
    print(f"Testing MCP Host endpoint: {BASE_URL}/api/data/items?source_id=transcripts")
    
    params = {
        "source_id": "transcripts",
        "limit": 2
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Test MCP host endpoint
            response = await client.get(
                f"{BASE_URL}/api/data/items",
                params=params,
                headers=HEADERS,
                timeout=5.0
            )
            
            print(f"MCP Host Response ({response.status_code}):")
            data = response.json()
            
            if response.status_code == 200:
                items = data.get('items', [])
                print(f"Found {len(items)} transcripts")
                if items:
                    print("Sample transcript:", json.dumps(items[0], indent=2))
                else:
                    print("No transcripts found. This could be because:")
                    print("1. The MCP server has no transcript data")
                    print("2. The MCP host is not properly connected to the MCP server")
                    print(f"3. The MCP server at {MCP_SERVER_URL} is not returning transcript data")
                    
                    # Try to query MCP server directly for transcripts
                    print("\nAttempting to query MCP server directly...")
                    await query_mcp_server_directly("transcripts")
            else:
                print(f"Error: {response.status_code} - {response.text}")
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error getting transcript data: {str(e)}")
            return False

async def main():
    """Run all tests"""
    print("=" * 60)
    print("MCP Client API Tests")
    print("=" * 60)
    print(f"MCP Host URL: {BASE_URL}")
    print(f"MCP Server URL: {MCP_SERVER_URL}")
    print("-" * 60)
    
    # Run tests
    test_results = {}
    
    # Test MCP host health
    test_results["host_health"] = await test_health()
    
    # Test MCP server connection
    test_results["server_connection"] = await test_mcp_server_connection()
    
    # Only continue if server connection is successful
    if test_results["server_connection"]:
        test_results["data_sources"] = await test_get_sources()
        test_results["customers"] = await test_get_customers()
        test_results["transcripts"] = await test_get_transcripts()
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name.replace('_', ' ').title()}")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    
    if not test_results.get("server_connection", False):
        print("1. Check if the MCP server is running at:", MCP_SERVER_URL)
        print("2. Verify the MCP_SERVER_URL in your environment variables")
        print("3. Check if the MCP server requires authentication")
    elif not any([test_results.get("customers"), test_results.get("transcripts")]):
        print("1. The MCP server is running but returned no data")
        print("   You may need to add test data to the MCP server")
        print("2. Check the MCP server logs for any errors")
        print("3. Verify the GraphQL queries in the MCP host match the server schema")
    
    print("\nTests complete!")

if __name__ == "__main__":
    asyncio.run(main())
