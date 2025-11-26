import requests
import json

def test_post():
    url = "http://localhost:8000/conversation/process"

    # Test data
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

        # Make the POST request
        response = requests.post(url, json=payload)

        print("\nResponse Status Code:", response.status_code)
        print("Response Headers:", dict(response.headers))

        try:
            response_data = response.json()
            print("Response Body:", json.dumps(response_data, indent=2))
        except ValueError:
            print("Response Body (raw):", response.text)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_post()
