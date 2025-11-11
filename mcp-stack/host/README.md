# MCP Host

The MCP (Model Context Protocol) Host is a FastAPI-based service that provides a unified interface for interacting with machine learning models and data sources. It implements the MCP protocol to enable seamless integration with MCP clients.

## Features

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

## Configuration

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
