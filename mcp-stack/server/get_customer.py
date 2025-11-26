import asyncio
from fastmcp import FastMCP

async def get_customer_details(customer_id):
    # Create a client connected to the MCP server
    client = FastMCP('http://localhost:8005/mcp')

    try:
        # Call the get_customer tool
        result = await client.get_customer(customer_id=customer_id)
        return result
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    customer_id = "CUST1000"
    result = asyncio.run(get_customer_details(customer_id))
    print(result)
