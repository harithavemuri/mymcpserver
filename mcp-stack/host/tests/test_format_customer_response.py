"""Tests for the format_customer_response function."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any, List
import sys
import os

# Add the parent directory to the path so we can import from the src directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.routers.conversation import format_customer_response

@pytest.mark.asyncio
async def test_format_customer_response_with_transformations():
    """Test format_customer_response with text transformations."""
    # Mock customer data
    customers = [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "(123) 456-7890",
            "notes": "Important customer"
        }
    ]
    
    # Mock message and context with transformation request
    message = "Show me all customers with masked emails and phone numbers"
    context = {
        "transformations": {
            "email": ["mask"],
            "phone": ["mask"]
        }
    }
    
    # Mock the text_transform_client
    from src.routers import conversation
    
    # Create a mock for the transform method
    async def mock_transform(text, operation):
        if operation == "mask":
            if "@" in text:  # Email
                user, domain = text.split("@")
                return type('obj', (object,), {
                    'transformed': f"{user[0]}***{user[-1:]}@{domain}"
                })
            else:  # Phone
                return type('obj', (object,), {
                    'transformed': "(***) ***-****"
                })
        return type('obj', (object,), {'transformed': text})
    
    # Patch the text_transform_client
    conversation.text_transform_client = MagicMock()
    conversation.text_transform_client.transform = mock_transform
    
    # Call the function
    result = await format_customer_response(
        customers=customers,
        message=message,
        requested_fields={"id", "name", "email", "phone"},
        context=context
    )
    
    # Assertions
    assert "response" in result
    assert "data" in result
    assert len(result["data"]) == 1
    
    # Check if the email and phone were transformed
    transformed_customer = result["data"][0]
    assert "email" in transformed_customer
    assert "phone" in transformed_customer
    
    # The email should be masked (e.g., j***e@example.com)
    assert transformed_customer["email"] != customers[0]["email"]
    assert "***" in transformed_customer["email"]
    
    # The phone should be masked
    assert transformed_customer["phone"] == "(***) ***-****"
    
    # The original data should not be modified
    assert customers[0]["email"] == "john.doe@example.com"
    assert customers[0]["phone"] == "(123) 456-7890"

@pytest.mark.asyncio
async def test_format_customer_response_no_transformations():
    """Test format_customer_response without any transformations."""
    # Mock customer data
    customers = [
        {
            "id": 1,
            "name": "Jane Smith",
            "email": "jane.smith@example.com"
        }
    ]
    
    # Call the function without any transformation context
    result = await format_customer_response(
        customers=customers,
        message="Show me all customers",
        requested_fields={"id", "name", "email"}
    )
    
    # Assertions
    assert "response" in result
    assert "data" in result
    assert len(result["data"]) == 1
    
    # The data should be unchanged
    assert result["data"][0] == customers[0]
