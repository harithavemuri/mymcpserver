# MCP Client with Natural Language Support

This client provides a natural language interface to interact with the MCP (Model Control Plane) server.

## Features

- Natural language processing for MCP operations
- Support for model registration, listing, and prediction
- Built-in error handling and retries
- Async/await support for concurrent operations

## Installation

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. The spacy model will be automatically downloaded when you first import the client.

## Usage

### Basic Usage

```python
import asyncio
from src.client import MCPClient

async def main():
    # Initialize the client
    async with MCPClient(server_url="http://localhost:8000") as client:
        # Register a model using natural language
        response = await client.chat("Register a new model named sentiment-analysis version 1.0.0")
        print(f"Model registered: {response}")
        
        # List all models
        models = await client.chat("Show me all available models")
        print(f"Available models: {models}")
        
        # Make a prediction
        prediction = await client.chat("Predict sentiment for: I love this product!")
        print(f"Prediction: {prediction}")

# Run the example
asyncio.run(main())
```

### Available Commands

1. **Register a model**:
   - "Register a new model named [name] version [version]"
   - "Add a model called [name]"
   - "Create a new model [name]"

2. **List models**:
   - "List all models"
   - "Show me available models"
   - "What models do you have?"

3. **Make predictions**:
   - "Predict [text]"
   - "Analyze [text]"
   - "What is the sentiment of [text]?"

## Error Handling

The client provides helpful error messages when it can't understand a request:

```python
try:
    response = await client.chat("This is not a valid command")
    print(response)
except Exception as e:
    print(f"Error: {e}")
```

## Development

To run the tests:

```bash
pytest tests/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
