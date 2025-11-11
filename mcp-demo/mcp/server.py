from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional, List
import uvicorn
import logging
import json

from .models import (
    TextRequest,
    TextResponse,
    BatchTextRequest,
    BatchTextResponse,
    ProcessingResult,
    ToolName,
    WorkflowState
)
from .models import MCPConfig  # Explicitly import from models to ensure we get the right version
from .workflow import create_workflow
from .tools import TextProcessor, SentimentAnalyzer, KeywordExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPServer:
    """MCP Server implementation using FastAPI."""
    
    def __init__(self, config: Optional[MCPConfig] = None):
        """Initialize the MCP server with the given configuration."""
        # Create default config if none provided
        self.config = config or MCPConfig()
        
        # Set up FastAPI app
        self.app = FastAPI(
            title="MCP Server",
            description="Model Context Protocol Server",
            version="0.1.0",
        )
        
        # Set up logging with detailed formatting and file output
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.DEBUG,
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('mcp_server.log', mode='w')
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        # Initialize tools with their configurations
        self.tools = {}
        
        # Text Processor
        if hasattr(self.config, 'text_processor') and self.config.text_processor.enabled:
            text_processor_params = {
                'to_upper': self.config.text_processor.to_upper,
                'to_lower': self.config.text_processor.to_lower,
                'title_case': self.config.text_processor.title_case,
                'reverse': self.config.text_processor.reverse,
                'strip': self.config.text_processor.strip
            }
            self.logger.info(f"Initializing TextProcessor with params: {text_processor_params}")
            self.tools[ToolName.TEXT_PROCESSOR] = TextProcessor(**text_processor_params)
        
        # Sentiment Analyzer
        if hasattr(self.config, 'sentiment_analyzer') and self.config.sentiment_analyzer.enabled:
            sentiment_params = {
                'analyze_emotion': self.config.sentiment_analyzer.analyze_emotion,
                'analyze_subjectivity': self.config.sentiment_analyzer.analyze_subjectivity
            }
            self.logger.info(f"Initializing SentimentAnalyzer with params: {sentiment_params}")
            self.tools[ToolName.SENTIMENT_ANALYZER] = SentimentAnalyzer(**sentiment_params)
        
        # Keyword Extractor
        if hasattr(self.config, 'keyword_extractor') and self.config.keyword_extractor.enabled:
            keyword_params = {
                'top_n': self.config.keyword_extractor.top_n,
                'min_word_length': self.config.keyword_extractor.min_word_length
            }
            self.logger.info(f"Initializing KeywordExtractor with params: {keyword_params}")
            self.tools[ToolName.KEYWORD_EXTRACTOR] = KeywordExtractor(**keyword_params)
        
        self.logger.info(f"Initialized tools: {list(self.tools.keys())}")
        
        if not self.tools:
            self.logger.warning("No tools were initialized. Check your configuration.")
        
        # Set up CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Create a dictionary of tool names to tool instances using the ToolName enum values
        tool_instances = {
            ToolName.TEXT_PROCESSOR.value: self.tools[ToolName.TEXT_PROCESSOR],
            ToolName.SENTIMENT_ANALYZER.value: self.tools[ToolName.SENTIMENT_ANALYZER],
            ToolName.KEYWORD_EXTRACTOR.value: self.tools[ToolName.KEYWORD_EXTRACTOR],
        }
        
        # Define the tool execution order using the ToolName enum values
        tool_order = [
            ToolName.TEXT_PROCESSOR.value,
            ToolName.SENTIMENT_ANALYZER.value,
            ToolName.KEYWORD_EXTRACTOR.value,
        ]
        
        self.logger.info(f"Creating workflow with tools: {list(tool_instances.keys())}")
        self.logger.info(f"Tool order: {tool_order}")
        
        # Create the workflow
        self.workflow = create_workflow(
            tools=tool_instances,
            tool_order=tool_order
        )
        
        # Set up routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up the API routes."""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "ok", "version": "0.1.0"}
        
        @self.app.get("/tools")
        async def list_tools():
            """List all available tools and their configurations."""
            tools_info = {}
            
            if hasattr(self.config, 'text_processor'):
                tool_info = {"enabled": self.config.text_processor.enabled}
                if ToolName.TEXT_PROCESSOR in self.tools:
                    tool_info.update(self.tools[ToolName.TEXT_PROCESSOR].get_metadata())
                tools_info[ToolName.TEXT_PROCESSOR.value] = tool_info
                
            if hasattr(self.config, 'sentiment_analyzer'):
                tool_info = {"enabled": self.config.sentiment_analyzer.enabled}
                if ToolName.SENTIMENT_ANALYZER in self.tools:
                    tool_info.update(self.tools[ToolName.SENTIMENT_ANALYZER].get_metadata())
                tools_info[ToolName.SENTIMENT_ANALYZER.value] = tool_info
                
            if hasattr(self.config, 'keyword_extractor'):
                tool_info = {"enabled": self.config.keyword_extractor.enabled}
                if ToolName.KEYWORD_EXTRACTOR in self.tools:
                    tool_info.update(self.tools[ToolName.KEYWORD_EXTRACTOR].get_metadata())
                tools_info[ToolName.KEYWORD_EXTRACTOR.value] = tool_info
                
            return tools_info
        
        @self.app.post("/process", response_model=TextResponse)
        async def process_text(request: TextRequest):
            """Process text through the MCP workflow."""
            try:
                logger.info(f"Processing text: {request.text[:100]}...")
                
                # Log the available tools
                logger.info(f"Available tools: {list(self.tools.keys())}")
                
                # Create initial workflow state with all required fields and tool parameters
                state = WorkflowState(
                    input_text=request.text,
                    results={},
                    current_tool=None,
                    error=None,
                    # Include tool parameters in the state
                    params={
                        "to_upper": True,
                        "to_lower": True,
                        "title_case": True,
                        "strip": True
                    }
                )
                logger.info(f"Initial state: {state}")
                
                # Execute the workflow
                logger.info("Executing workflow...")
                
                # Debug: Print the workflow object
                logger.info(f"Workflow object: {self.workflow}")
                logger.info(f"Workflow type: {type(self.workflow)}")
                
                # Debug: Check if the workflow has the expected methods
                if not hasattr(self.workflow, 'ainvoke'):
                    logger.error("Workflow does not have 'ainvoke' method")
                    return TextResponse(
                        success=False,
                        error="Workflow is not properly initialized"
                    )
                
                logger.info("Workflow has 'ainvoke' method")
                
                # Log the available tools and their configurations
                logger.info("Available tools and their configurations:")
                for tool_name, tool in self.tools.items():
                    logger.info(f"- {tool_name}: {tool.__class__.__name__}")
                    if hasattr(tool, 'config'):
                        logger.info(f"  Config: {tool.config}")
                    else:
                        logger.info("  No config found")
                
                # Create a dictionary with the initial state
                initial_state = {
                    "input_text": request.text,
                    "results": {},
                    "current_tool": None,
                    "error": None
                }
                
                logger.info(f"Initial state for workflow: {initial_state}")
                
                # Execute the workflow with the initial state
                logger.info("Starting workflow execution...")
                result = await self.workflow.ainvoke(initial_state)
                logger.info(f"Workflow execution completed. Result type: {type(result)}")
                
                # Debug: Print the result object
                logger.info(f"Workflow result: {result}")
                
                # Convert the result to a dictionary if it's a Pydantic model
                if hasattr(result, 'dict'):
                    result_dict = result.dict()
                    logger.info("Converted result using .dict() method")
                elif hasattr(result, '__dict__'):
                    result_dict = result.__dict__
                    logger.info("Converted result using .__dict__")
                else:
                    result_dict = dict(result) if isinstance(result, dict) else {}
                    logger.info("Converted result using dict()")
                
                logger.info(f"Workflow result as dict: {result_dict}")
                
                # Extract the results from the workflow execution
                results_dict = result_dict.get('results', {})
                logger.info(f"Results from result_dict.get('results'): {results_dict}")
                
                # If results is empty, try to get it from the root of the result
                if not results_dict and hasattr(result, 'results'):
                    results_dict = result.results
                    logger.info(f"Got results from result.results: {results_dict}")
                    
                    # If still no results, try to get it directly from the result
                    if not results_dict and isinstance(result, dict):
                        results_dict = {k: v for k, v in result.items() if k not in ['input_text', 'current_tool', 'error']}
                        logger.info(f"Extracted results directly from result dict: {results_dict}")
                    
                    # If we still don't have results, return an error
                    if not results_dict:
                        error_msg = "No results found in workflow execution"
                        logger.error(error_msg)
                        return TextResponse(
                            success=False,
                            error=error_msg
                        )
                    
                    # Check for error in the result
                    if isinstance(result, dict) and 'error' in result and result['error']:
                        error_msg = f"Workflow error: {result['error']}"
                        logger.error(error_msg)
                        return TextResponse(
                            success=False,
                            error=error_msg
                        )
                
                # Extract results from the workflow state
                results_dict = {}
                
                # Convert the result to a dictionary if it's a Pydantic model
                if hasattr(result, 'dict'):
                    result_dict = result.dict()
                    logger.info("Converted result using .dict() method")
                elif hasattr(result, '__dict__'):
                    result_dict = result.__dict__
                    logger.info("Converted result using .__dict__")
                else:
                    result_dict = dict(result) if isinstance(result, dict) else {}
                    logger.info("Converted result using dict()")
                
                logger.info(f"Result as dictionary: {result_dict}")
                
                # First, try to get results from the 'results' key
                if 'results' in result_dict and isinstance(result_dict['results'], dict):
                    results_dict = result_dict['results']
                    logger.info(f"Found results in 'results' key: {results_dict}")
                # If not found, look for tool results directly in the result dictionary
                else:
                    logger.info("No 'results' key found, looking for tool results directly")
                    for tool_name in ['text_processor', 'sentiment_analyzer', 'keyword_extractor']:
                        if tool_name in result_dict and result_dict[tool_name]:
                            results_dict[tool_name] = result_dict[tool_name]
                    
                    logger.info(f"Collected tool results: {results_dict}")
                
                # If still no results, try to extract from the result object's attributes
                if not results_dict and hasattr(result, '__dict__'):
                    logger.info("No results in dictionary, checking result object attributes")
                    for tool_name in ['text_processor', 'sentiment_analyzer', 'keyword_extractor']:
                        if hasattr(result, tool_name):
                            tool_result = getattr(result, tool_name)
                            if tool_result is not None:
                                results_dict[tool_name] = tool_result
                    
                    logger.info(f"Extracted results from object attributes: {results_dict}")
                
                # If we still don't have results, log a warning
                if not results_dict:
                    logger.warning("No tool results found in the workflow output")
                    logger.info(f"Result object type: {type(result)}")
                    if hasattr(result, '__dict__'):
                        logger.info(f"Result attributes: {result.__dict__}")
                
                logger.info(f"Processed results: {results_dict}")
                
                # Create response
                processing_result = ProcessingResult(
                    original_text=request.text,
                    results=results_dict,
                    metadata={
                        "tools_executed": list(results_dict.keys()) if results_dict else []
                    }
                )
                
                logger.info("Processing successful")
                return TextResponse(
                    success=True,
                    result=processing_result
                )
                
            except Exception as e:
                error_msg = f"Error processing request: {str(e)}"
                logger.exception(error_msg)
                return TextResponse(
                    success=False,
                    error=f"Error processing text: {str(e)}"
                )
        
        @self.app.post("/process_batch", response_model=BatchTextResponse)
        async def process_batch(request: BatchTextRequest):
            """Process multiple texts through the MCP workflow in parallel."""
            try:
                import asyncio
                from concurrent.futures import ThreadPoolExecutor
                
                logger.info(f"Processing batch of {len(request.texts)} texts with max {request.max_concurrent} concurrent requests")
                
                # Create a semaphore to limit concurrency
                semaphore = asyncio.Semaphore(request.max_concurrent)
                
                async def process_single_text(text: str) -> dict:
                    """Process a single text with rate limiting."""
                    async with semaphore:
                        try:
                            # Create a TextRequest with the same parameters
                            text_request = TextRequest(
                                text=text,
                                params=request.params or {}
                            )
                            
                            # Process the text using the existing endpoint
                            response = await process_text(text_request)
                            
                            # Convert the response to a dict for the batch response
                            if response.success and response.result:
                                # Use model_dump() if available, otherwise fall back to dict()
                                result_dict = response.result.model_dump() if hasattr(response.result, 'model_dump') else response.result.dict()
                                return {
                                    "success": True,
                                    "text": text,
                                    "result": result_dict,
                                    "error": None
                                }
                            else:
                                return {
                                    "success": False,
                                    "text": text,
                                    "result": None,
                                    "error": response.error
                                }
                        except Exception as e:
                            logger.error(f"Error processing text '{text[:50]}...': {str(e)}")
                            return {
                                "success": False,
                                "text": text,
                                "result": None,
                                "error": str(e)
                            }
                
                # Process all texts concurrently
                tasks = [process_single_text(text) for text in request.texts]
                results = await asyncio.gather(*tasks)
                
                # Count successful results
                success_count = sum(1 for r in results if r.get('success'))
                
                return BatchTextResponse(
                    success=True,
                    results=results,
                    processed_count=len(results),
                    error=None
                )
                
            except Exception as e:
                logger.error(f"Error in batch processing: {str(e)}")
                return BatchTextResponse(
                    success=False,
                    results=[],
                    processed_count=0,
                    error=f"Error in batch processing: {str(e)}"
                )
        
        # Add exception handler
        @self.app.exception_handler(Exception)
        async def global_exception_handler(request: Request, exc: Exception):
            """Global exception handler."""
            logger.exception("Unhandled exception")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": f"Internal server error: {str(exc)}"
                }
            )
    
    async def run(self, host: Optional[str] = None, port: Optional[int] = None):
        """Run the MCP server."""
        host = host or self.config.host
        port = port or self.config.port
        
        logger.info(f"Starting MCP server on {host}:{port}")
        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="info" if not self.config.debug else "debug",
        )
        server = uvicorn.Server(config)
        await server.serve()


# For backward compatibility
app = MCPServer().app

if __name__ == "__main__":
    import asyncio
    server = MCPServer()
    asyncio.run(server.run())
