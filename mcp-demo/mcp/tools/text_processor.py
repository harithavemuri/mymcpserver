from typing import Dict, Any

from ..models import ToolName, TextRequest, ToolResponse
from .base import BaseTool


class TextProcessor(BaseTool):
    """A tool for basic text processing operations."""
    
    def __init__(self, **kwargs):
        super().__init__(name=ToolName.TEXT_PROCESSOR, **kwargs)
        
    @property
    def description(self) -> str:
        return "Performs basic text processing operations like case conversion and whitespace handling."
    
    async def process(self, request: TextRequest) -> ToolResponse:
        """Process the input text with various transformations."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"TextProcessor.process called with request: {request}")
        
        text = request.text
        params = request.params or {}
        
        logger.info(f"TextProcessor params: {params}")
        logger.info(f"TextProcessor input text (first 100 chars): {text[:100]}")
        
        result: Dict[str, Any] = {
            "original_text": text[:100] + "..." if len(text) > 100 else text,
            "length": len(text),
            "word_count": len(text.split()),
            "line_count": len(text.splitlines()),
        }
        
        # Log the initial result
        logger.info(f"Initial result: {result}")
        
        # Apply transformations based on parameters
        if params.get("to_upper", False):
            result["uppercase"] = text.upper()
            logger.info("Applied to_upper transformation")
            
        if params.get("to_lower", False):
            result["lowercase"] = text.lower()
            logger.info("Applied to_lower transformation")
            
        if params.get("title_case", False):
            result["title_case"] = text.title()
            logger.info("Applied title_case transformation")
            
        if params.get("reverse", False):
            result["reversed"] = text[::-1]
            logger.info("Applied reverse transformation")
            
        if params.get("strip", False):
            result["stripped"] = text.strip()
            logger.info("Applied strip transformation")
        
        logger.info(f"Final result: {result}")
        
        response = ToolResponse(
            tool_name=self.name,
            result=result,
            metadata={"processed": True}
        )
        
        logger.info(f"Returning response: {response}")
        return response
