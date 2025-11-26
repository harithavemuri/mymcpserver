# MCP Text Transform Client

A TypeScript client for interacting with the MCP Text Transform service.

## Prerequisites

- Node.js (v16 or later)
- npm (v7 or later) or yarn
- MCP Text Transform Server running at http://localhost:8002

## Installation

```bash
# Install dependencies
npm install

# Build the project
npm run build
```

## Usage

```typescript
import { TextTransformClient } from './dist/TextTransformClient';

// Create a new client instance
const client = new TextTransformClient({
  baseURL: 'http://localhost:8002',
  timeout: 5000
});

// Check server health
const isHealthy = await client.healthCheck();
console.log(`Server is ${isHealthy ? 'healthy' : 'unhealthy'}`);

// Get available transformations
const transformations = await client.getAvailableTransformations();
console.log('Available transformations:', transformations);

// Transform text
const result = await client.transform('hello world', 'uppercase');
console.log('Transformed text:', result.transformed);
```

## Available Methods

### `transform(text: string, operation: string, options?: Record<string, unknown>): Promise<TransformResponse>`

Transforms the input text using the specified operation.

**Parameters:**
- `text`: The text to transform
- `operation`: The transformation operation to apply (e.g., 'uppercase', 'lowercase')
- `options`: Additional options for the transformation (optional)

**Returns:** A promise that resolves to the transformed text and metadata

### `healthCheck(): Promise<boolean>`

Checks if the MCP server is healthy.

**Returns:** A promise that resolves to `true` if the server is healthy, `false` otherwise

### `getAvailableTransformations(): Promise<string[]>`

Gets a list of available transformation operations.

**Returns:** A promise that resolves to an array of available transformation names

## Error Handling

The client includes comprehensive error handling and logging. All methods throw errors that include detailed information about what went wrong.

## Logging

Logs are written to both the console and log files in the `logs` directory. The log level can be controlled using the `LOG_LEVEL` environment variable.

## License

MIT
