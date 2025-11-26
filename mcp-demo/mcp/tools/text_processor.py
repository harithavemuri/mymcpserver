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
        
        logger.info("=" * 80)
        logger.info("TextProcessor.process called")
        logger.info(f"Request: {request}")
        logger.info(f"Request type: {type(request)}")
        logger.info(f"Request attributes: {dir(request)}")
        
        text = request.text
        params = request.params or {}
        
        logger.info(f"TextProcessor params: {params} (type: {type(params)})")
        logger.info(f"Params has 'to_upper': {'to_upper' in params}")
        logger.info(f"to_upper value: {params.get('to_upper')}")
        logger.info(f"TextProcessor input text (first 100 chars): {text[:100]}")
        logger.info("-" * 40)
        
        result: Dict[str, Any] = {
            "original_text": text[:100] + "..." if len(text) > 100 else text,
            "length": len(text),
            "word_count": len(text.split()),
            "line_count": len(text.splitlines()),
        }
        
        # Log the initial result
        logger.info(f"Initial result: {result}")
        
        # Apply each transformation and update the result
        if params.get("to_upper", False):
            result["uppercase"] = text.upper()
            logger.info(f"Applied to_upper: {result['uppercase']}")
            
        if params.get("to_lower", False):
            result["lowercase"] = text.lower()
            logger.info(f"Applied to_lower: {result['lowercase']}")
            
        if params.get("title_case", False):
            result["title_case"] = text.title()
            logger.info(f"Applied title_case: {result['title_case']}")
            
        if params.get("reverse", False):
            result["reversed"] = text[::-1]
            logger.info(f"Applied reverse: {result['reversed']}")
            
        if params.get("strip", False):
            result["stripped"] = text.strip()
            logger.info(f"Applied strip: {result['stripped']}")
            
        # Determine the final transformed text based on the last applied transformation
        transformed_text = text
        if "uppercase" in result:
            transformed_text = result["uppercase"]
        elif "lowercase" in result:
            transformed_text = result["lowercase"]
        elif "title_case" in result:
            transformed_text = result["title_case"]
        elif "reversed" in result:
            transformed_text = result["reversed"]
        elif "stripped" in result:
            transformed_text = result["stripped"]
            
        # Add the final transformed text to the result
        result["transformed_text"] = transformed_text
        logger.info(f"Final transformed_text: {transformed_text}")
        
        logger.info(f"Final result: {result}")
        
        response = ToolResponse(
            tool_name=self.name,
            result=result,
            metadata={"processed": True}
        )
        
        logger.info(f"Returning response: {response}")
        return response
