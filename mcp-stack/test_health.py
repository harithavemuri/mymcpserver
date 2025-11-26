"""Test script for MCP Server health check."""
import json
import requests

def test_health_check():
    """Test the GraphQL health check endpoint."""
    url = 'http://localhost:8005/graphql'
    headers = {'Content-Type': 'application/json'}

    # GraphQL query
    query = '''
    query {
        health {
            status
            timestamp
            version
        }
    }
    '''

    # Send the request
    response = requests.post(
        url,
        json={'query': query},
        headers=headers
    )

    # Print the response
    print("Status Code:", response.status_code)
    print("Response:", json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_health_check()
