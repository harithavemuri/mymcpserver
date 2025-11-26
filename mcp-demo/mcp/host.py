import httpx
import asyncio
import os
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urljoin
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .models import TextRequest, TextResponse, ProcessingResult, ToolName, MCPConfig


class MPCHost:
    """MCP Host for interacting with MCP servers."""

    def __init__(self, base_url: str = None):
        """Initialize the MCP Host.

        Args:
            base_url: Base URL of the MCP server. Defaults to MCP_SERVER_URL environment variable or 'http://localhost:8001'
        """
        self.base_url = (base_url or os.getenv('MCP_SERVER_URL', 'http://localhost:8001')).rstrip('/')
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def health_check(self) -> bool:
        """Check if the MCP server is healthy."""
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            return response.json().get("status") == "ok"
        except Exception as e:
            return False

    async def list_tools(self) -> Dict[str, Any]:
        """List all available tools on the MCP server."""
        response = await self.client.get("/tools")
        response.raise_for_status()
        return response.json()

    async def process_text(
        self,
        text: str,
        params: Optional[Dict[str, Any]] = None
    ) -> TextResponse:
        """Process text through the MCP workflow.

        Args:
            text: The text to process
            params: Additional parameters for processing

        Returns:
            TextResponse containing the processing results
        """
        request = TextRequest(text=text, params=params or {})

        try:
            response = await self.client.post(
                "/process",
                json=request.model_dump()
            )
            response.raise_for_status()
            return TextResponse(**response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 422:
                # Handle validation errors
                error_detail = e.response.json().get("detail", {})
                return TextResponse(
                    success=False,
                    error=f"Validation error: {error_detail}"
                )
            return TextResponse(
                success=False,
                error=f"HTTP error: {str(e)}"
            )
        except Exception as e:
            return TextResponse(
                success=False,
                error=f"Error processing text: {str(e)}"
            )

    async def process_texts(
        self,
        texts: List[str],
        params: Optional[Dict[str, Any]] = None,
        max_concurrent: int = 5
    ) -> List[TextResponse]:
        """Process multiple texts in parallel.

        Args:
            texts: List of texts to process
            params: Additional parameters for processing
            max_concurrent: Maximum number of concurrent requests

        Returns:
            List of TextResponse objects
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(text: str):
            async with semaphore:
                return await self.process_text(text, params)

        tasks = [process_with_semaphore(text) for text in texts]
        return await asyncio.gather(*tasks)

    async def get_tool_result(
        self,
        response: TextResponse,
        tool_name: Union[str, ToolName],
        default: Any = None
    ) -> Optional[Dict[str, Any]]:
        """Get the result for a specific tool from a TextResponse.

        Args:
            response: The TextResponse from process_text
            tool_name: Name of the tool to get results for
            default: Default value if tool result not found

        Returns:
            The tool's result or default if not found
        """
        if not response.success or not response.result:
            return default

        tool_name = tool_name.value if isinstance(tool_name, ToolName) else tool_name

        # Check if result is already a dictionary with the tool results
        if hasattr(response.result, 'results'):
            return response.result.results.get(tool_name, default)
        # If result is a dictionary itself, try to get the tool's result directly
        elif isinstance(response.result, dict):
            return response.result.get(tool_name, default)
        return default


# Helper function for synchronous usage
def create_mcp_host(base_url: str = None) -> MPCHost:
    """Create and return an MCP host (synchronous interface)."""
    return MPCHost(base_url=base_url)


# Example usage
async def example_usage():
    """Example usage of the MPCHost class."""
    # Create a host instance using environment variable
    async with MPCHost() as host:
        # Check if server is healthy
        if not await host.health_check():
            print("MCP server is not healthy")
            return

        # List available tools
        tools = await host.list_tools()
        print("Available tools:", list(tools.keys()))

        # Process some text
        text = """
        The Model Context Protocol (MCP) is a powerful framework for building
        AI-powered applications. It enables seamless integration of multiple
        AI models and tools in a unified workflow.
        """

        print("\nProcessing text...")
        response = await host.process_text(text)

        if response.success:
            print("\nProcessing successful!")

            # Get specific tool results
            sentiment = await host.get_tool_result(
                response,
                ToolName.SENTIMENT_ANALYZER
            )

            keywords = await host.get_tool_result(
                response,
                ToolName.KEYWORD_EXTRACTOR
            )

            print("\nSentiment Analysis:")
            print(f"  Polarity: {sentiment['sentiment']['polarity']:.2f}")
            print(f"  Subjectivity: {sentiment['sentiment']['subjectivity']:.2f}")

            print("\nTop Keywords:")
            for kw in keywords['keywords'][:5]:
                print(f"  - {kw['phrase']} (score: {kw['score']:.2f})")
        else:
            print(f"\nError: {response.error}")


if __name__ == "__main__":
    asyncio.run(example_usage())
