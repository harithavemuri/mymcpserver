# MCP Host

The MCP (Model Context Protocol) Host is a FastAPI-based service that provides a unified interface for interacting with machine learning models and data sources. It implements the MCP protocol to enable seamless integration with MCP clients.

## Features

- Text transformation operations (uppercase, lowercase, title case, reverse, strip)
- Customer search with field selection and filtering
- Model registration and management
- Prediction serving with context support
- Data source integration
- RESTful API with OpenAPI documentation
- Authentication and authorization
- CORS support
- Environment-based configuration
- Comprehensive logging

## Prerequisites

- Python 3.11+
- pip (Python package manager)
- (Optional) Virtual environment (recommended)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd mcp-stack/host
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # or using pipenv
   pipenv install
   ```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Update the environment variables in `.env` as needed

## API Endpoints

### Text Transformations

#### Transform Text
- **Endpoint**: `POST /process`
- **Description**: Apply text transformations
- **Request Body**:
  ```json
  {
    "text": "hello world",
    "params": {
      "to_upper": true,
      "to_lower": false,
      "title_case": false,
      "reverse": false,
      "strip": false
    }
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "result": {
      "original_text": "hello world",
      "results": {
        "text_processor": {
          "original_text": "hello world",
          "length": 11,
          "word_count": 2,
          "line_count": 1,
          "transformed_text": "HELLO WORLD",
          "uppercase": "HELLO WORLD"
        }
      },
      "metadata": {
        "params_used": {
          "to_upper": true,
          "to_lower": false,
          "title_case": false,
          "reverse": false,
          "strip": false
        },
        "transformation_applied": true
      }
    },
    "error": null
  }
  ```

### Customer Search

Search for customers with field selection and filtering using GraphQL.

#### Search Customers
- **Endpoint**: `POST /graphql`
- **Description**: Search for customers with optional field selection and filtering
- **Request Body**:
  ```graphql
  query SearchCustomers($filter: CustomerFilterInput!) {
    searchCustomers(filter: $filter) {
      id
      firstName
      lastName
      email
      phone
      state
    }
  }
  ```
  ```json
  {
    "filter": {
      "name": "John",
      "state": "CA",
      "limit": 10,
      "offset": 0
    }
  }
  ```
- **Filter Parameters**:
  - `name`: Search by customer name (partial match)
  - `email`: Filter by email (partial match)
  - `phone`: Filter by phone number
  - `state`: Filter by state code (e.g., "CA")
  - `city`: Filter by city
  - `country`: Filter by country
  - `limit`: Maximum results to return (default: 100)
  - `offset`: Results to skip (for pagination)

- **Available Fields**:
  - `id` / `customerId`: Unique customer ID
  - `firstName`: First name
  - `lastName`: Last name
  - `email`: Email address
  - `phone`: Phone number
  - `address`: Street address
  - `city`: City
  - `state`: State/Province
  - `zipCode`: ZIP/Postal code
  - `country`: Country

- **Example Response**:
  ```json
  {
    "data": {
      "searchCustomers": [
        {
          "id": "123",
          "firstName": "John",
          "lastName": "Doe",
          "email": "john.doe@example.com",
          "phone": "+14155551234",
          "state": "CA"
        }
      ]
    }
  }
  ```

#### Health Check
- **Endpoint**: `GET /health`
- **Description**: Check if the service is running
- **Response**:
  ```json
  {
    "status": "ok"
  }
  ```

#### List Available Tools
- **Endpoint**: `GET /tools`
- **Description**: List all available text processing tools
- **Response**:
  ```json
  {
    "text_processor": {
      "name": "text_processor",
      "description": "Performs basic text processing operations like case conversion and whitespace handling.",
      "operations": ["uppercase", "lowercase", "title_case", "reverse", "strip"]
    }
  }
  ```

#### Process Conversation
- **Endpoint**: `POST /conversation/process`
- **Description**: Process natural language requests and route to appropriate client
- **Request Body**:
  ```json
  {
    "messages": [
      {
        "role": "user",
        "content": "Convert this to uppercase: hello world",
        "metadata": {}
      }
    ],
    "context": {}
  }
  ```
- **Response**:
  ```json
  {
    "response": "Here's your uppercase text: HELLO WORLD",
    "client_used": "text_transform",
    "metadata": {
      "operation": "uppercase",
      "original_text": "hello world",
      "transformed_text": "HELLO WORLD"
    }
  }
  ```

## Python Client Examples

### Basic Usage

```python
from src.text_transform import MCPTextTransformClient
import asyncio

async def main():
    # Initialize the client
    client = MCPTextTransformClient(base_url="http://localhost:8002")
    
    try:
        # Uppercase transformation
        result = await client.transform("hello world", operation="uppercase")
        print(f"Uppercase: {result.transformed}")
        
        # Multiple transformations (chaining)
        text = "hello world"
        uppercase_result = await client.transform(text, operation="uppercase")
        reverse_result = await client.transform(uppercase_result.transformed, operation="reverse")
        print(f"Chained transformations: {reverse_result.transformed}")
        
    finally:
        await client.client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
```

### Conversation Examples

#### Using the Python Client

```python
from src.routers.conversation import ConversationMessage, MCPTextTransformClient
import asyncio

async def main():
    # Initialize the client
    client = MCPTextTransformClient(base_url="http://localhost:8002")
    
    try:
        # Simple transformation
        response = await client.transform("hello world", operation="uppercase")
        print(f"Response: {response.transformed}")
        
        # Using the conversation endpoint
        from src.routers.conversation import process_conversation
        
        messages = [
            {"role": "user", "content": "Convert this to title case: the quick brown fox"}
        ]
        
        result = await process_conversation({"messages": messages})
        print(f"Assistant: {result.response}")
        
    finally:
        await client.client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
```

#### Testing the Endpoint

You can test the conversation endpoint using the example script:

```bash
python examples/test_conversation_endpoint.py
```

This will run several test cases and show you the responses from the conversation endpoint.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_SERVER_URL` | Base URL of the MCP server | `http://localhost:8002` |
| `MCP_TIMEOUT` | Request timeout in seconds | `30.0` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Running the Examples

1. Start the MCP server (from the mcp-demo directory):
   ```bash
   cd ../../mcp-demo
   python -m mcp.server
   ```

2. Run the text transformation example:
   ```bash
   python examples/text_transform_example.py
   ```

3. Run the conversation example:
   ```bash
   python examples/conversation_example.py
   ```

## Error Handling

The API returns error responses in the following format:

```json
{
  "success": false,
  "error": {
    "code": "error_code",
    "message": "Error description",
    "details": {}
  }
}
```

Common error codes:
- `400`: Bad request (invalid parameters)
- `404`: Resource not found
- `422`: Validation error
- `500`: Internal server error

Edit the `.env` file to configure the following settings:

```ini
# Server configuration
HOST=0.0.0.0
PORT=8000
DEBUG=False

# MCP Server configuration
MCP_SERVER_URL=http://localhost:8000
API_KEY=your-api-key-here

# CORS settings (comma-separated list of allowed origins)
CORS_ORIGINS=*

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/mcp_host.log

# Model storage
MODEL_DIR=./models
DATA_DIR=./data
```

## Running the Server

### Development Mode

```bash
uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`

### Production Mode

For production, use a production-ready ASGI server like Uvicorn with Gunicorn:

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app
```

## API Documentation

Once the server is running, you can access:

- **Interactive API documentation**: `http://localhost:8000/docs`
- **Alternative documentation**: `http://localhost:8000/redoc`
- **OpenAPI schema**: `http://localhost:8000/openapi.json`

## API Endpoints

### Health Check

- `GET /health` - Check if the service is running

### Model Management

- `POST /models/register` - Register a new model
- `GET /models` - List all registered models
- `GET /models/{model_id}` - Get model details
- `POST /predict` - Make a prediction using a registered model

### Data Access

- `GET /api/data/sources` - List available data sources
- `GET /api/data/items` - Query data items with filtering and pagination

## Authentication

The API uses API key authentication. Include the API key in the `X-API-Key` header with each request.

```http
GET /models HTTP/1.1
Host: localhost:8000
X-API-Key: your-api-key-here
```

## Testing

Run the test suite with:

```bash
pytest -v
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host to bind the server to |
| `PORT` | `8000` | Port to run the server on |
| `DEBUG` | `False` | Enable debug mode |
| `MCP_SERVER_URL` | `http://localhost:8000` | Base URL of the MCP server |
| `API_KEY` | (required) | API key for authentication |
| `CORS_ORIGINS` | `*` | Comma-separated list of allowed origins |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FILE` | `logs/mcp_host.log` | Path to log file |
| `MODEL_DIR` | `./models` | Directory to store model files |
| `DATA_DIR` | `./data` | Directory for data files |

## Deployment

### Docker

1. Build the Docker image:
   ```bash
   docker build -t mcp-host .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 --env-file .env mcp-host
   ```

### Kubernetes

Example deployment configuration:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-host
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-host
  template:
    metadata:
      labels:
        app: mcp-host
    spec:
      containers:
      - name: mcp-host
        image: mcp-host:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: mcp-host-secrets
        resources:
          limits:
            cpu: "1"
            memory: "1Gi"
          requests:
            cpu: "0.5"
            memory: "512Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-host
spec:
  selector:
    app: mcp-host
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue in the repository or contact the maintainers.
