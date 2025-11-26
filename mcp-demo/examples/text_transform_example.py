"""
Example script demonstrating text transformations using the MCP host.
This script shows how to transform text to uppercase and reverse it.
"""
import asyncio
import os
import sys

# Add the parent directory to the path so we can import from mcp
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.client import MCPClient
from mcp.models import TextRequest

async def transform_text():
    """Demonstrate text transformations using the MCP host."""
    # Initialize the MCP client
    client = MCPClient(host="localhost", port=8002)
    
    try:
        # Text to transform
        text = "Hello, World!"
        print(f"Original text: {text}")
        
        # 1. Transform to uppercase
        print("\n1. Transforming to uppercase...")
        uppercase_request = TextRequest(
            text=text,
            params={"to_upper": True}
        )
        uppercase_response = await client.process(uppercase_request)
        
        # Extract the transformed text
        if uppercase_response and uppercase_response.result:
            text_processor = uppercase_response.result.results.get("text_processor", {})
            uppercase_text = text_processor.get("uppercase", "Transformation failed")
            print(f"Uppercase: {uppercase_text}")
        
        # 2. Transform to reverse
        print("\n2. Reversing the text...")
        reverse_request = TextRequest(
            text=text,
            params={"reverse": True}
        )
        reverse_response = await client.process(reverse_request)
        
        # Extract the reversed text
        if reverse_response and reverse_response.result:
            text_processor = reverse_response.result.results.get("text_processor", {})
            reversed_text = text_processor.get("reversed", "Transformation failed")
            print(f"Reversed: {reversed_text}")
        
        # 3. Chain transformations: uppercase + reverse
        print("\n3. Chaining transformations: uppercase + reverse")
        # First, get the uppercase text
        uppercase_request = TextRequest(
            text=text,
            params={"to_upper": True}
        )
        uppercase_response = await client.process(uppercase_request)
        
        if uppercase_response and uppercase_response.result:
            text_processor = uppercase_response.result.results.get("text_processor", {})
            uppercase_text = text_processor.get("uppercase", text)
            
            # Now reverse the uppercase text
            reverse_request = TextRequest(
                text=uppercase_text,
                params={"reverse": True}
            )
            reverse_response = await client.process(reverse_request)
            
            if reverse_response and reverse_response.result:
                text_processor = reverse_response.result.results.get("text_processor", {})
                final_text = text_processor.get("reversed", "Transformation failed")
                print(f"Uppercase + Reversed: {final_text}")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(transform_text())
