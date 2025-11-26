"""
Example script demonstrating text transformations using the MCP host.
This script shows how to transform text to uppercase and reverse it.
"""
import asyncio
import os
import sys

# Add the host directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.text_transform import MCPTextTransformClient

async def transform_text():
    """Demonstrate text transformations using the MCP host."""
    # Initialize the MCP Text Transform client
    client = MCPTextTransformClient(base_url="http://localhost:8002")
    
    try:
        # Text to transform
        text = "Hello, World!"
        print(f"Original text: {text}")
        
        # 1. Transform to uppercase
        print("\n1. Transforming to uppercase...")
        uppercase_result = await client.transform(text, operation="uppercase")
        print(f"Uppercase: {uppercase_result.transformed}")
        
        # 2. Transform to reverse
        print("\n2. Reversing the text...")
        reverse_result = await client.transform(text, operation="reverse")
        print(f"Reversed: {reverse_result.transformed}")
        
        # 3. Chain transformations: uppercase + reverse
        print("\n3. Chaining transformations: uppercase + reverse")
        # First, get the uppercase text
        uppercase_result = await client.transform(text, operation="uppercase")
        # Then reverse the uppercase text
        final_result = await client.transform(uppercase_result.transformed, operation="reverse")
        print(f"Uppercase + Reversed: {final_result.transformed}")
        
        # 4. Show all available transformations
        print("\n4. All transformations:")
        for operation in ["uppercase", "lowercase", "title", "reverse", "strip"]:
            result = await client.transform(text, operation=operation)
            print(f"{operation.capitalize()}: {result.transformed}")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.client.aclose()

if __name__ == "__main__":
    asyncio.run(transform_text())
