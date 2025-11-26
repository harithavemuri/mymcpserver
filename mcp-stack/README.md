# MCP Stack

Model Context Protocol (MCP) Stack is a GraphQL-based API server for managing and interacting with machine learning models and data.

## Features

- **GraphQL API**: Flexible query language for your data
- **Data Access**: Built-in support for customer and call transcript data
- **Tool Management**: Register and manage ML tools and models
- **Real-time Predictions**: Make predictions using registered models
- **Health Monitoring**: Built-in health check endpoints

## GraphQL API Reference

### Health Check

Check if the API is running:

```graphql
query {
  health {
    status
    timestamp
    version
  }
}
```

**Example Response:**
```json
{
  "data": {
    "health": {
      "status": "ok",
      "timestamp": "2025-11-04T02:26:00.123456",
      "version": "1.0.0"
    }
  }
}
```

### Tools

List all available tools with optional filtering:

```graphql
query ListTools($category: String, $availableOnly: Boolean = true, $limit: Int = 10, $offset: Int = 0) {
  listTools(category: $category, availableOnly: $availableOnly, limit: $limit, offset: $offset) {
    id
    name
    description
    category
    isAvailable
    createdAt
    updatedAt
  }
}
```

**Example Query:**
```graphql
query {
  listTools(limit: 2) {
    id
    name
    description
    category
    isAvailable
  }
}
```

**Example Response:**
```json
{
  "data": {
    "listTools": [
      {
        "id": "1",
        "name": "text-generator",
        "description": "Generates text based on input",
        "category": "generation",
        "isAvailable": true
      },
      {
        "id": "2",
        "name": "image-classifier",
        "description": "Classifies images into categories",
        "category": "vision",
        "isAvailable": true
      }
    ]
  }
}
```

**Available Filters:**
- `category`: Filter tools by category (e.g., "generation", "vision")
- `availableOnly`: Set to `false` to include unavailable tools (default: `true`)
- `limit`: Maximum number of tools to return (default: 10)
- `offset`: Number of tools to skip for pagination (default: 0)

### Models

Get a specific model by ID:

```graphql
query GetModel($id: ID!) {
  getModel(id: $id) {
    id
    name
    description
    version
    createdAt
    updatedAt
  }
}
```

List all models with pagination:

```graphql
query ListModels($limit: Int = 10, $offset: Int = 0) {
  listModels(limit: $limit, offset: $offset) {
    id
    name
    description
    version
    createdAt
    updatedAt
  }
}
```

### Data Sources

List all data sources:

```graphql
query DataSources {
  dataSources {
    id
    name
    description
    path
    sourceType
    metadata
    createdAt
    updatedAt
  }
}
```

### Data Items

Query data items with filtering and pagination:

```graphql
query DataItems($sourceId: ID, $query: DataQueryInput) {
  dataItems(sourceId: $sourceId, query: $query) {
    items {
      id
      sourceId
      data
      metadata
      createdAt
      updatedAt
    }
    total
    page
    size
    hasMore
  }
}
```

### Search

Search across data items:

```graphql
query Search($query: String!, $fields: [String!], $limit: Int = 10) {
  searchDataItems(query: $query, fields: $fields, limit: $limit) {
    id
    sourceId
    data
    metadata
  }
}
```

## Mutations

### Create Model

```graphql
mutation CreateModel($input: ModelInput!) {
  createModel(input: $input) {
    id
    name
    description
    version
  }
}
```

### Create Prediction

```graphql
mutation CreatePrediction($input: PredictionInput!) {
  createPrediction(input: $input) {
    id
    modelId
    inputData
    outputData
    createdAt
  }
}
```

## Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd mcp-stack
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   cd server
   pip install -r requirements.txt
   ```

### Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Update the `.env` file with your configuration.

### Running the Server

```bash
# Start the development server
uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

The GraphQL Playground will be available at: http://localhost:8005/graphql

## GraphQL API

### Health Check

```graphql
query {
  health {
    status
    timestamp
    version
  }
}
```

### List Available Tools

```graphql
query {
  listTools {
    id
    name
    description
    category
    isAvailable
  }
}
```

### Search Customers

Search for customers with optional filtering. You can filter by various criteria like state, name, or limit the number of results.

**Query:**
```graphql
query SearchCustomers($filter: CustomerFilterInput!) {
  searchCustomers(filter: $filter) {
    customerId
    firstName
    lastName
    email
    phone
    city
    state
  }
}
```

**Variables:**
```json
{
  "filter": {
    "state": "CA",
    "limit": 3,
    "offset": 0
  }
}
```

**Filter Options:**
- `state` (String, optional): Filter by state code (e.g., "CA", "NY")
- `limit` (Int, optional, default=10): Maximum number of results to return
- `offset` (Int, optional, default=0): Number of results to skip (for pagination)

**Example Response:**
```json
{
  "data": {
    "searchCustomers": [
      {
        "customerId": "CUST1001",
        "firstName": "Joe",
        "lastName": "Moore",
        "email": "joe.moore@example.com",
        "phone": "555-0101",
        "city": "Los Angeles",
        "state": "CA"
      },
      ...
    ]
  }
}
```

### Get Call Transcripts

```graphql
query {
  getTranscript(callId: "CALL1000") {
    callId
    customerId
    callTimestamp
    callDurationSeconds
    callSummary
    transcript {
      speaker
      text
      timestamp
    }
  }
}
```

## Data Models

### Customer
- `customerId` (String): Unique identifier
- `firstName` (String): Customer's first name
- `lastName` (String): Customer's last name
- `email` (String): Customer's email address
- `phone` (String): Customer's phone number
- `city` (String): City from home address
- `state` (String): State code from home address
- `personalInfo` (Object): Additional personal details
- `homeAddress` (Object): Complete address information
- `employment` (Object): Employment details including company and work address

### Call Transcript
- `callId`: Unique call identifier
- `customerId`: Reference to customer
- `callType`: Type of call (inbound/outbound)
- `callTimestamp`: When the call occurred
- `callDurationSeconds`: Duration in seconds
- `agentId`: ID of the agent who handled the call
- `transcript`: Array of conversation turns

## Development

### Project Structure

```
mcp-stack/
├── server/                 # Main server application
│   ├── app/
│   │   ├── graphql/        # GraphQL schema and resolvers
│   │   ├── models/         # Data models
│   │   ├── data/           # Data loading utilities
│   │   └── main.py         # FastAPI application
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Example environment variables
└── README.md              # This file
```

### Testing

Run the test suite:

```bash
pytest
```

## License

[Your License Here]

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Support

For support, please open an issue in the GitHub repository.
# Navigate to the server directory
cd c:\Haritha\windsurf\MyFeedback\mcp-stack\server

# Remove any existing virtual environment
pipenv --rm

# Create a new pipenv environment with Python 3.11
pipenv --python 3.11

# Activate the environment
pipenv shell

# Install the requirements
pipenv install -r requirements.txt

rm -r venv
py -3.11 -m venv venv
python -m venv venv
.\venv\Scripts\activate
python.exe -m pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
pip install -e .[dev]
pip install setuptools wheel

uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload --log-level debug
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
python example.py --server
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

 change to mcp-stack\server folder
 remove the virtual environment folder
 clear plan
 clean virtual environment
 create new virtual environment mcp-stack\server folder using python 3.11.9 environment only and use all packages compatible with python
 install required dependencies using requirements.txt
 update the requirements.txt as you identify missing dependencies and reinstall requirements.txt
 then run the host integration tests
