"""Text transform client for MCP host."""
import os
import logging
from typing import Optional, Dict, Any, Union
import httpx
from pydantic import BaseModel, HttpUrl
from datetime import datetime

logger = logging.getLogger(__name__)

class TextTransformRequest(BaseModel):
    """Request model for text transformation."""
    text: str
    operation: str = "uppercase"
    options: Optional[Dict[str, Any]] = None

class TextTransformResponse(BaseModel):
    """Response model for text transformation."""
    original: str
    transformed: str
    operation: str
    timestamp: str

class MCPTextTransformClient:
    """Client for interacting with the MCP Text Transform service."""
    
    def __init__(self, base_url: str = "http://localhost:8002", timeout: float = 10.0):
        """Initialize the MCP Text Transform client.
        
        Args:
            base_url: Base URL of the MCP server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        logger.info(f"Initialized MCP Text Transform client with base URL: {self.base_url}")
    
    async def transform(
        self, 
        text: str, 
        operation: str = "uppercase", 
        options: Optional[Dict[str, Any]] = None
    ) -> TextTransformResponse:
        """Transform text using the specified operation.
        
        Args:
            text: The text to transform
            operation: The transformation operation to perform (uppercase, lowercase, title, reverse, strip)
            options: Additional options for the transformation
            
        Returns:
            TextTransformResponse containing the transformed text
            
        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        logger.info(f"Transforming text with operation '{operation}': {text[:50]}...")
        
        # Map operation to server parameters
        params = {
            "to_upper": operation == "uppercase",
            "to_lower": operation == "lowercase",
            "title_case": operation == "title",
            "reverse": operation == "reverse",
            "strip": operation == "strip"
        }
        
        # Make the request to the server
        try:
            response = await self.client.post(
                "/process",
                json={
                    "text": text,
                    "params": params
                }
            )
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            logger.debug(f"Received response: {result}")
            
            # Extract the transformed text from the response
            result_data = result.get("result", {})
            text_processor = result_data.get("results", {}).get("text_processor", {})
            
            # Get the transformed text based on the operation
            transformed_text = text
            if operation == "uppercase":
                transformed_text = text_processor.get("uppercase", text)
            elif operation == "lowercase":
                transformed_text = text_processor.get("lowercase", text)
            elif operation == "title":
                transformed_text = text_processor.get("title_case", text)
            elif operation == "reverse":
                transformed_text = text_processor.get("reversed", text)
            elif operation == "strip":
                transformed_text = text_processor.get("stripped", text)
            
            return TextTransformResponse(
                original=text,
                transformed=transformed_text,
                operation=operation,
                timestamp=datetime.utcnow().isoformat()
            )
        except Exception as e:
            logger.error(f"Transform request failed: {e}")
            # Fallback to local transformation if MCP fails
            return self._local_transform(text, operation)
    
    def _local_transform(self, text: str, operation: str) -> TextTransformResponse:
        """Fallback local text transformation with enhanced operations.
        
        Args:
            text: Input text to transform
            operation: Transformation to apply
            
        Returns:
            TextTransformResponse with the transformed text
        """
        try:
            transformed = text
            
            # Core text transformations
            if operation == "uppercase":
                transformed = text.upper()
            elif operation == "lowercase":
                transformed = text.lower()
            elif operation == "capitalize":
                transformed = ' '.join(word.capitalize() for word in text.split())
            elif operation == "title":
                transformed = text.title()
            elif operation == "reverse":
                transformed = text[::-1]
            elif operation == "trim":
                transformed = text.strip()
            elif operation == "swapcase":
                transformed = text.swapcase()
            elif operation == "length":
                transformed = str(len(text))
            elif operation == "words":
                words = text.split()
                transformed = f"{len(words)} words"
            elif operation.startswith("replace_"):
                # Format: replace_old_new (e.g., replace_hello_hi)
                parts = operation.split('_')
                if len(parts) >= 3:
                    old, new = parts[1], parts[2]
                    transformed = text.replace(old, new)
            else:
                logger.warning(f"Unsupported operation: {operation}")
                transformed = f"[Error: Unsupported operation: {operation}]"
            
            return TextTransformResponse(
                original=text,
                transformed=transformed,
                operation=operation,
                timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Local transform failed: {e}")
            return TextTransformResponse(
                original=text,
                transformed=f"[Error: {str(e)}]",
                operation=operation,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def health_check(self) -> bool:
        """Check if the MCP server is healthy."""
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
    
    async def get_available_operations(self) -> list[str]:
        """Get the list of available transformation operations."""
        # These are the supported operations by the MCP server
        return [
            "uppercase",
            "lowercase",
            "capitalize",
            "reverse",
            "trim"
        ]
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

# Global instance
text_transform_client = MCPTextTransformClient(
    base_url=os.getenv("MCP_SERVER_URL", "http://localhost:8002"),
    timeout=float(os.getenv("MCP_TIMEOUT", "30.0"))
)
