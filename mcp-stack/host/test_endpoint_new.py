import requests
import json

def test_post_endpoint():
    url = "http://localhost:8000/conversation/process"

    # Test payload
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "Show me all customers"
            }
        ]
    }

    try:
        print("Sending POST request to:", url)
        print("Request payload:", json.dumps(payload, indent=2))

        # Send POST request
        response = requests.post(url, json=payload)

        print("\nResponse Status Code:", response.status_code)
        print("Response Headers:", dict(response.headers))

        try:
            print("Response Body:", json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            print("Response Body (raw):", response.text)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_post_endpoint()
