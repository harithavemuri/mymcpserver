import requests
import json

def test_process_endpoint():
    url = "http://localhost:8002/process"
    payload = {
        "text": "hello world",
        "params": {"to_upper": True}
    }
    
    print("Sending request to:", url)
    print("Payload:", json.dumps(payload, indent=2))
    
    response = requests.post(url, json=payload)
    print("\nResponse Status Code:", response.status_code)
    
    try:
        response_data = response.json()
        print("\nResponse JSON:", json.dumps(response_data, indent=2))
        
        # Check if the response has the expected structure
        if "result" in response_data and "results" in response_data["result"]:
            text_processor = response_data["result"]["results"].get("text_processor", {})
            
            print("\nChecking for 'uppercase' in response:", "uppercase" in text_processor)
            print("Checking for 'transformed_text' in response:", "transformed_text" in text_processor)
            
            if "uppercase" in text_processor:
                print("\nUppercase value:", text_processor["uppercase"])
            if "transformed_text" in text_processor:
                print("Transformed text value:", text_processor["transformed_text"])
        else:
            print("\nUnexpected response structure:")
            print("Expected 'result.results.text_processor' in response")
            
    except json.JSONDecodeError:
        print("\nFailed to parse response as JSON")
        print("Raw response:", response.text)

if __name__ == "__main__":
    test_process_endpoint()
