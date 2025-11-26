# MCP (Model Context Protocol) Example

A simple example demonstrating the Model Context Protocol (MCP) with a server and host implementation using Python, Pydantic, and LangGraph. This implementation includes batch processing capabilities for handling multiple text inputs efficiently.

## Project Structure
```
mcp-demo/
├── mcp/
│   ├── __init__.py
│   ├── models.py       # Pydantic models
│   ├── server.py       # MCP Server implementation
│   ├── host.py         # MCP Host implementation
│   ├── workflow.py     # LangGraph workflow definition
│   └── tools/          # MCP Tools
│       ├── __init__.py
│       ├── base.py     # Base tool class
│       ├── text_processor.py
│       ├── sentiment_analyzer.py
│       └── keyword_extractor.py
├── requirements.txt    # Python dependencies
└── example.py         # Example usage
```

## Setup

1. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the example:
   ```bash
   python example.py

   python example.py --server
   ```

## Tools

1. **Text Processor**: Basic text manipulation (uppercase, lowercase, etc.)
2. **Sentiment Analyzer**: Analyzes text sentiment
3. **Keyword Extractor**: Extracts keywords from text

## Example Workflow

The example demonstrates a text processing pipeline that can handle both single and batch text processing:

### Single Text Processing
1. Takes input text
2. Processes it through the text processor
3. Analyzes sentiment
4. Extracts keywords
5. Returns the combined results

### Batch Processing
1. Takes multiple text inputs
2. Processes them in parallel with configurable concurrency
3. Applies the same processing pipeline to each text
4. Returns results for all inputs, including any processing errors
5. Maintains order of results to match input order

## API Endpoints

### Single Text Processing
- `POST /process`: Process a single text through the MCP workflow
  - Request body:
    ```json
    {
      "text": "Your input text here",
      "params": {
        "to_upper": true,
        "to_lower": false
      }
    }
    ```
  - Response: JSON with processed results

### Batch Processing
- `POST /process_batch`: Process multiple texts in parallel
  - Request body:
    ```json
    {
      "texts": ["First text", "Second text", "Third text"],
      "params": {
        "to_upper": true
      },
      "max_concurrent": 2
    }
    ```
  - Parameters:
    - `texts`: Array of strings to process
    - `params`: Optional parameters for text processing
    - `max_concurrent`: Maximum number of concurrent requests (default: 5)
  - Response: JSON with results for all processed texts

## Testing

The test suite includes unit tests and integration tests for the MCP server endpoints.

### Running Tests

1. Install test dependencies:
   ```bash
   pip install pytest pytest-asyncio pytest-cov
   ```

2. Run all tests with coverage:
   ```bash
   pytest -v --cov=mcp --cov-report=term-missing tests/
   ```

3. Run specific test files:
   ```bash
   pytest -v tests/integration/test_server_endpoints.py
   ```

### Test Coverage
- Unit tests for individual components
- Integration tests for API endpoints
- Tests for error handling and edge cases
- Batch processing with concurrent requests

Current test coverage includes:
- Single text processing
- Batch text processing
- Input validation
- Error handling for invalid inputs
- Concurrent request handling

## Extending the System
To add a new tool:
[ ] Create a new Python file in the mcp/tools/ directory
Create a class that inherits from BaseTool
Implement the execute method
Register the tool in the MCPServer.register_default_tools method
