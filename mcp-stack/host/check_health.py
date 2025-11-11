"""Simple script to check the health of the MCP host."""
import asyncio
import json
import httpx
from datetime import datetime

async def check_health():
    """Check the health of the MCP host."""
    base_url = "http://localhost:8000"
    
    print("\n=== MCP Host Health Check ===\n")
    
    # 1. Check REST health endpoint
    print("1. Checking REST health endpoint...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{base_url}/health")
            response.raise_for_status()
            data = response.json()
            print(f"   ✅ Status: {data.get('status', 'unknown')}")
            print(f"   ✅ Version: {data.get('version', 'unknown')}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # 2. Test health check through converse endpoint
    print("\n2. Testing health check through /converse endpoint...")
    test_queries = [
        "Is the server healthy?",
        "Check server status",
        "Is the server up and running?",
        "Verify server health"
    ]
    
    for query in test_queries:
        print(f"\n   Testing query: '{query}'")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{base_url}/api/converse",
                    json={"query": query, "context": {}},
                    timeout=5.0
                )
                response.raise_for_status()
                data = response.json()
                
                print(f"   ✅ Response: {data.get('response', 'No response')}")
                if "data" in data:
                    print(f"   ✅ Data: {json.dumps(data['data'], indent=4)}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n=== Health Check Complete ===\n")

if __name__ == "__main__":
    asyncio.run(check_health())
