from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..models import ToolName, ToolResponse, TextRequest


class BaseTool(ABC):
    """Base class for all MCP tools."""

    def __init__(self, name: ToolName, **kwargs):
        """Initialize the tool with a name and optional configuration.

        Args:
            name: The name of the tool
            **kwargs: Additional configuration parameters
        """
        self.name = name
        self.config = kwargs

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a brief description of what the tool does."""
        pass

    @abstractmethod
    async def process(self, request: TextRequest) -> ToolResponse:
        """Process the input text and return a response.

        Args:
            request: The text processing request

        Returns:
            ToolResponse containing the processing results
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the tool.

        Returns:
            Dictionary containing tool metadata
        """
        return {
            "name": self.name.value,
            "description": self.description,
            "config": self.config
        }

    async def __call__(self, request: TextRequest) -> ToolResponse:
        """Make the tool callable.

        Args:
            request: The text processing request

        Returns:
            ToolResponse containing the processing results
        """
        return await self.process(request)
