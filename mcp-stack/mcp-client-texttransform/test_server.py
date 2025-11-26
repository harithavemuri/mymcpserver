import requests
import json

def test_transformation(base_url, test_name, text, params):
    print(f"\n=== Testing {test_name} ===")
    print(f"Input text: {text}")
    print(f"Parameters: {json.dumps(params, indent=2)}")
    
    payload = {
        "text": text,
        "params": params
    }
    
    try:
        response = requests.post(
            f"{base_url}/process",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        response_data = response.json()
        print("Response:")
        print(json.dumps(response_data, indent=2))
        
        # Check if the transformation was applied
        if response_data.get("success", False):
            result = response_data.get("result", {})
            if result.get("metadata", {}).get("transformation_applied", False):
                print("✅ Transformation was applied")
                print(f"Original text: {result.get('original_text')}")
                print("Results:")
                for tool, tool_result in result.get("results", {}).items():
                    print(f"  {tool}:")
                    for k, v in tool_result.items():
                        if k != "original_text":
                            print(f"    {k}: {v}")
            else:
                print("❌ No transformation was applied")
        else:
            print(f"❌ Request failed: {response_data.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_server():
    base_url = "http://localhost:8002"
    
    # Test different transformations
    test_cases = [
        ("Uppercase", "hello world", {"to_upper": True}),
        ("Lowercase", "HELLO WORLD", {"to_lower": True}),
        ("Title Case", "hello world", {"title_case": True}),
        ("Reverse", "hello", {"reverse": True}),
        ("Strip", "  hello  ", {"strip": True})
    ]
    
    for name, text, params in test_cases:
        test_transformation(base_url, name, text, params)
    
    # Test with multiple transformations
    test_transformation(
        base_url,
        "Multiple Transformations",
        "  Hello World  ",
        {"to_upper": True, "strip": True}
    )
    
    # Test list tools endpoint
    print("\n=== Testing List Tools ===")
    try:
        response = requests.get(f"{base_url}/tools", timeout=5)
        print(f"Status Code: {response.status_code}")
        print("Available Tools:")
        tools = response.json()
        for tool_name, tool_info in tools.items():
            print(f"\n{tool_name}:")
            print(f"  Description: {tool_info.get('description')}")
            print(f"  Enabled: {tool_info.get('enabled', False)}")
            print("  Configuration:")
            for k, v in tool_info.get('config', {}).items():
                print(f"    {k}: {v}")
    except Exception as e:
        print(f"❌ Error listing tools: {str(e)}")
    
    # Test health check
    print("\n=== Testing Health Check ===")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"❌ Error checking health: {str(e)}")

if __name__ == "__main__":
    test_server()
