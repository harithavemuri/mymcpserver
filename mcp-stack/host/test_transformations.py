"""Test script to verify text transformations in format_customer_response."""
import asyncio
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List
import sys
import os

# Add the parent directory to the path so we can import from the src directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the function we want to test
from src.routers.conversation import format_customer_response

# Mock the text_transform_client
class MockTextTransformClient:
    async def transform(self, text, operation):
        if operation == "mask":
            if "@" in text:  # Email masking
                user, domain = text.split("@")
                masked = f"{user[0]}***{user[-1:]}@{domain}"
                return type('obj', (object,), {'transformed': masked})
            else:  # Phone masking
                return type('obj', (object,), {'transformed': "(***) ***-****"})
        return type('obj', (object,), {'transformed': text})

# Patch the text_transform_client in the conversation module
@patch('src.routers.conversation.text_transform_client', new_callable=MockTextTransformClient)
async def test_format_customer_response_with_transformations(mock_client):
    """Test format_customer_response with text transformations."""
    # Test data
    customers = [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "(123) 456-7890",
            "notes": "Important customer"
        }
    ]

    # Context with transformation requests
    context = {
        "transformations": {
            "email": ["mask"],
            "phone": ["mask"]
        }
    }

    # Call the function
    result = await format_customer_response(
        customers=customers,
        message="Show me all customers with masked emails and phone numbers",
        requested_fields={"id", "name", "email", "phone"},
        context=context
    )

    # Print the results
    print("\n=== Test Results ===")
    print(f"Original customer data: {customers[0]}")
    print(f"Transformed customer data: {result['data'][0]}")

    # Verify the transformations
    transformed = result["data"][0]
    assert transformed["email"] == "j***e@example.com", f"Email not masked correctly: {transformed['email']}"
    assert transformed["phone"] == "(***) ***-****", f"Phone not masked correctly: {transformed['phone']}"
    assert transformed["name"] == "John Doe", "Name should not be modified"

    print("\n✅ All tests passed!")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_format_customer_response_with_transformations())
