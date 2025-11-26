import requests
import json

# Test the /process endpoint with to_upper transformation
response = requests.post(
    "http://localhost:8002/process",
    json={"text": "hello world", "params": {"to_upper": True}},
    headers={"Content-Type": "application/json"}
)

print("Status Code:", response.status_code)
print("Response:")
print(json.dumps(response.json(), indent=2))
