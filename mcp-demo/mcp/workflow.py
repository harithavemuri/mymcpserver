import logging
from typing import Dict, Any, Optional, List, TypeVar, Union, Callable, Type
from pydantic import BaseModel
from langgraph.graph import StateGraph, END

from .models import WorkflowState, ToolName, TextRequest, ToolResponse
from .tools import TextProcessor, SentimentAnalyzer, KeywordExtractor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define a type variable for the state
State = TypeVar('State', bound=BaseModel)

class Workflow:
    """A simple workflow that chains together multiple tools."""
    
    def __init__(self, tools: Optional[Dict[str, Any]] = None):
        """Initialize the workflow with a set of tools."""
        self.tools = tools or {}
        self.workflow = StateGraph(WorkflowState)
        self.logger = logging.getLogger(__name__)
        
    def add_tool(self, name: str, tool: Any) -> 'Workflow':
        """Add a tool to the workflow."""
        self.tools[name] = tool
        
        async def process_tool(state: WorkflowState) -> WorkflowState:
            """Process the current state with the given tool."""
            import logging
            logger = logging.getLogger(__name__)
            logger.setLevel(logging.DEBUG)
            
            try:
                logger.info(f"\n{'='*80}")
                logger.info(f"Processing with tool: {name}")
                
                # Convert state to dict if it's a Pydantic model
                if hasattr(state, 'model_dump'):
                    state_dict = state.model_dump()
                elif hasattr(state, 'dict'):
                    state_dict = state.dict()  # Fallback for older Pydantic versions
                else:
                    state_dict = dict(state)
                
                logger.info(f"Current state type: {type(state)}")
                logger.info(f"Current state: {state_dict}")
                logger.info(f"Tool type: {type(tool)}")
                logger.info(f"Tool attributes: {dir(tool)}")
                
                # Get tool parameters
                tool_params = {}
                if hasattr(tool, 'config'):
                    tool_config = tool.config
                    logger.info(f"Tool config: {tool_config}")
                    
                    if hasattr(tool_config, 'model_dump'):
                        tool_config_dict = tool_config.model_dump()
                        tool_params = tool_config_dict.get('params', {})
                    elif hasattr(tool_config, 'dict'):
                        tool_config_dict = tool_config.dict()  # Fallback for older Pydantic versions
                        tool_params = tool_config_dict.get('params', {})
                    elif hasattr(tool_config, 'get'):
                        tool_params = tool_config.get('params', {})
                
                logger.info(f"Tool parameters for {name}: {tool_params}")
                
                # Get input text from state
                input_text = state_dict.get('input_text', '')
                logger.info(f"Input text (first 200 chars): {input_text[:200]}")
                
                # Create request
                request = TextRequest(text=input_text, params=tool_params)
                logger.info(f"Created request: {request}")
                
                # Call the tool's process method
                logger.info(f"Calling {name}.process()...")
                response = await tool.process(request)
                logger.info(f"Tool response type: {type(response)}")
                
                # Process the response
                if response is not None:
                    logger.info(f"Response: {response}")
                    
                    # Convert response to dict
                    if hasattr(response, 'model_dump'):
                        response_dict = response.model_dump()
                    elif hasattr(response, 'dict'):
                        response_dict = response.dict()  # Fallback for older Pydantic versions
                    elif hasattr(response, '__dict__'):
                        response_dict = response.__dict__
                    else:
                        response_dict = dict(response) if hasattr(response, 'items') else {}
                    
                    logger.info(f"Response as dict: {response_dict}")
                    
                    # Extract result from response
                    result = {}
                    
                    # If response has a 'result' key, use that
                    if 'result' in response_dict and isinstance(response_dict['result'], dict):
                        result = response_dict['result']
                    # Otherwise, use the entire response dict as the result
                    elif isinstance(response_dict, dict):
                        result = response_dict
                    
                    logger.info(f"Extracted result for {name}: {result}")
                    
                    # Update state with results
                    if 'results' not in state_dict or state_dict['results'] is None:
                        state_dict['results'] = {}
                    
                    # Store the result with the tool name as the key
                    state_dict['results'][name] = result
                    
                    # Also store the result directly on the state for easier access
                    state_dict[name] = result
                    state_dict['current_tool'] = name
                    state_dict['error'] = None
                    
                    logger.info(f"Updated state.results[{name}]: {result}")
                else:
                    error_msg = f"No response returned from {name}"
                    logger.error(error_msg)
                    state_dict['error'] = error_msg
                
            except Exception as e:
                error_msg = f"Error in {name}: {str(e)}"
                logger.exception(error_msg)
                state_dict['error'] = error_msg
            
            logger.info(f"Final state after {name}: {state_dict}")
            logger.info(f"{'='*80}\n")
            
            # Create a new WorkflowState instance
            try:
                return WorkflowState(**state_dict)
            except Exception as e:
                logger.error(f"Error creating WorkflowState: {str(e)}")
                logger.error(f"State dict: {state_dict}")
                raise
        
        # Add the tool node to the workflow
        self.workflow.add_node(name, process_tool)
        return self
    
    def add_edge(self, from_tool: str, to_tool: str) -> 'Workflow':
        """Add an edge between two tools in the workflow."""
        self.workflow.add_edge(from_tool, to_tool)
        return self
    
    def compile(self):
        """Compile the workflow."""
        # Set the entry point to the first tool
        first_tool = next(iter(self.tools.keys()), None)
        if first_tool:
            self.workflow.set_entry_point(first_tool)
        
        # Set the finish point to the last tool
        last_tool = next(reversed(self.tools.keys()), None)
        if last_tool:
            self.workflow.set_finish_point(last_tool)
        
        return self.workflow.compile()


def create_workflow(
    tools: Dict[str, Any],
    tool_order: List[str]
):
    """
    Create a LangGraph workflow for processing text through multiple tools.
    
    Args:
        tools: Dictionary of tool instances to use in the workflow
        tool_order: List specifying the order of tool execution
        
    Returns:
        A compiled LangGraph workflow
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Creating workflow with tools: {list(tools.keys())}")
    logger.info(f"Tool order: {tool_order}")
    
    # Create and configure the workflow
    workflow = Workflow(tools)
    
    # Add tools to the workflow in the specified order
    for tool_name in tool_order:
        if tool_name not in tools:
            raise ValueError(f"Tool {tool_name} not found in provided tools")
        logger.info(f"Adding tool to workflow: {tool_name}")
        workflow.add_tool(tool_name, tools[tool_name])
    
    # Connect the tools in the specified order
    for i in range(len(tool_order) - 1):
        from_tool = tool_order[i]
        to_tool = tool_order[i + 1]
        logger.info(f"Adding edge: {from_tool} -> {to_tool}")
        workflow.add_edge(from_tool, to_tool)
    
    # Compile the workflow
    logger.info("Compiling workflow...")
    compiled_workflow = workflow.compile()
    logger.info("Workflow compiled successfully")
    
    return compiled_workflow
