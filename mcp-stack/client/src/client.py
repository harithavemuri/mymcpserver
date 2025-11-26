"""MCP Client for interacting with MCP servers with natural language support."""
import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic, Type

import httpx
import spacy
from pydantic import BaseModel, Field, HttpUrl, validator
from pydantic_settings import BaseSettings

# Type variable for generic response type
T = TypeVar('T')

class IntentClassifier:
    """Lightweight intent classifier using rule-based matching."""

    def __init__(self):
        # Load a small English model for NLP
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # If model not found, download it
            import subprocess
            import sys
            subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")

        # Define intents and their patterns
        self.intent_patterns = {
            "register_model": ["register", "add", "create", "new model"],
            "list_models": ["list", "show", "get models", "what models"],
            "predict": ["predict", "run", "execute", "what is", "analyze"],
            "get_data": ["get data", "fetch data", "show data", "list data"]
        }

    def extract_intent(self, text: str) -> str:
        """Extract the most likely intent from the input text."""
        doc = self.nlp(text.lower())
        text = doc.text

        # Simple pattern matching
        for intent, patterns in self.intent_patterns.items():
            if any(pattern in text for pattern in patterns):
                return intent

        return "unknown"

@dataclass
class ParsedQuery:
    """Container for parsed query information."""
    intent: str
    entities: Dict[str, str]
    confidence: float = 0.9

class MCPConversationHandler:
    """Handles natural language conversation with the MCP Client."""

    def __init__(self, client: 'MCPClient'):
        self.client = client
        self.classifier = IntentClassifier()

    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a natural language query and return the API response."""
        # Parse the query
        parsed = self._parse_query(query)

        # Map intent to API call
        handler = getattr(self, f"_handle_{parsed.intent}", self._handle_unknown)
        return await handler(parsed.entities)

    def _parse_query(self, query: str) -> ParsedQuery:
        """Parse the natural language query into structured data."""
        intent = self.classifier.extract_intent(query)
        doc = self.classifier.nlp(query)

        # Simple entity extraction
        entities = {
            "model_name": next((ent.text for ent in doc.ents if ent.label_ == "PRODUCT"), None),
            "model_version": next((ent.text for ent in doc.ents if ent.label_ == "CARDINAL"), None),
            "query": query
        }

        return ParsedQuery(intent=intent, entities=entities)

    async def _handle_register_model(self, entities: Dict[str, str]) -> Dict[str, Any]:
        """Handle model registration."""
        if not entities.get("model_name"):
            return {"error": "Please specify a model name to register."}

        model_config = {
            "name": entities["model_name"],
            "version": entities.get("model_version", "1.0.0")
        }
        return await self.client.register_model(model_config)

    async def _handle_list_models(self, entities: Dict[str, str]) -> Dict[str, Any]:
        """Handle listing models."""
        return await self.client.list_models()

    async def _handle_predict(self, entities: Dict[str, str]) -> Dict[str, Any]:
        """Handle prediction requests."""
        if not entities.get("model_name"):
            return {"error": "Please specify which model to use for prediction."}

        prediction_request = {
            "model_name": entities["model_name"],
            "input_data": {"query": entities.get("query", "")}
        }
        return await self.client.predict(prediction_request)

    async def _handle_unknown(self, entities: Dict[str, str]) -> Dict[str, Any]:
        """Handle unknown intents."""
        return {
            "error": "I'm not sure how to process that request.",
            "suggestions": [
                "Register a model: 'Register a new model named sentiment-analysis'",
                "List models: 'Show me all available models'",
                "Make a prediction: 'Predict sentiment for this text'"
            ]
        }

logger = logging.getLogger(__name__)

class ClientConfig(BaseSettings):
    """Configuration for the MCP Client."""

    # Server configuration
    MCP_SERVER_URL: HttpUrl = "http://localhost:8005"
    MCP_API_KEY: Optional[str] = None

    # Request settings
    TIMEOUT: int = 30
    MAX_RETRIES: int = 3

    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields instead of raising an error

class MCPError(Exception):
    """Base exception for MCP client errors."""
    pass

class ModelInfo(BaseModel):
    """Information about a registered model."""
    id: str
    name: str
    description: Optional[str] = None
    version: str
    created_at: datetime
    updated_at: datetime

class ContextInfo(BaseModel):
    """Information about a context."""
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class MCPClient:
    """Client for interacting with an MCP server with natural language support."""

    def __init__(
        self,
        server_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize the MCP client with natural language conversation support.

        Args:
            server_url: URL of the MCP server
            api_key: API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.config = ClientConfig()
        self.server_url = server_url or str(self.config.MCP_SERVER_URL)
        self.api_key = api_key or self.config.MCP_API_KEY
        self.timeout = timeout or self.config.TIMEOUT
        self.max_retries = max_retries or self.config.MAX_RETRIES

        self._client = httpx.AsyncClient(
            base_url=self.server_url,
            timeout=self.timeout,
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
        )

        # Initialize conversation handler
        self.conversation = MCPConversationHandler(self)

    async def __aenter__(self):
        """Async context manager entry."""
        await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._client.aclose()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the MCP server."""
        url = f"{self.server_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                if attempt == self.max_retries or e.response.status_code < 500:
                    try:
                        error_data = e.response.json()
                        error_msg = error_data.get("detail", str(e))
                    except Exception:
                        error_msg = str(e)
                    raise MCPError(f"HTTP error: {error_msg}") from e

                # Exponential backoff
                backoff = 2 ** attempt
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                    f"Retrying in {backoff} seconds..."
                )
                await asyncio.sleep(backoff)

            except (httpx.RequestError, json.JSONDecodeError) as e:
                if attempt == self.max_retries:
                    raise MCPError(f"Request failed: {e}") from e

                backoff = 2 ** attempt
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                    f"Retrying in {backoff} seconds..."
                )
                await asyncio.sleep(backoff)

    async def chat(self, message: str) -> Dict[str, Any]:
        """
        Process a natural language message and execute the corresponding MCP operation.

        Example:
            response = await client.chat("Register a new model named sentiment-analysis")
            response = await client.chat("List all available models")
            response = await client.chat("Predict sentiment for this text: I love this product!")

        Args:
            message: Natural language message to process

        Returns:
            Dict containing the response from the MCP server or an error message
        """
        return await self.conversation.process_query(message)

    # Model operations
    async def register_model(self, model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new model with the MCP server.

        Args:
            model_config: Dictionary containing model configuration
                - name: Name of the model (required)
                - version: Version of the model (required)
                - description: Optional description of the model

        Returns:
            Dictionary containing the registration response
        """
        response = await self._make_request("POST", "/models/register", data=model_config)
        return response

    async def list_models(self) -> List[ModelInfo]:
        """List all available models.

        Returns:
            List[ModelInfo]: A list of ModelInfo objects representing the available models.

        Raises:
            MCPError: If there's an error fetching the models from the server.
        """
        try:
            response = await self._make_request("GET", "/models")
            # Handle both response formats: direct list or nested under "data"
            models = response.get("data", []) if isinstance(response, dict) else response
            if not isinstance(models, list):
                models = [models]  # Handle case where a single model is returned
            return [ModelInfo(**model) for model in models]
        except httpx.HTTPStatusError as e:
            raise MCPError(f"Failed to list models. Status code: {e.response.status_code}, Error: {str(e)}")
        except Exception as e:
            raise MCPError(f"Failed to list models: {str(e)}")

    async def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """Get information about a specific model."""
        response = await self._make_request("GET", "/graphql", {
            "query": """
                query GetModel($id: ID!) {
                    model(id: $id) {
                        id
                        name
                        description
                        version
                        created_at
                        updated_at
                    }
                }
            """,
            "variables": {"id": model_id}
        })
        if "data" in response and response["data"].get("model"):
            return ModelInfo(**response["data"]["model"])
        return None

    # Context operations
    async def create_context(self, name: str, description: Optional[str] = None) -> ContextInfo:
        """Create a new context."""
        response = await self._make_request("POST", "/graphql", {
            "query": """
                mutation CreateContext($input: ContextInput!) {
                    createContext(input: $input) {
                        id
                        name
                        description
                        created_at
                        updated_at
                    }
                }
            """,
            "variables": {
                "input": {
                    "name": name,
                    "description": description
                }
            }
        })
        return ContextInfo(**response["data"]["createContext"])

    # Prediction operations
    async def _handle_predict(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prediction requests from the conversation handler.

        Args:
            entities: Dictionary containing extracted entities from the query
                - model_id: ID of the model to use for prediction
                - input_data: Input data for the prediction

        Returns:
            Dictionary containing the prediction result
        """
        if not entities.get("model_id"):
            return {"error": "Please specify which model to use for prediction."}

        # Create a new context for this prediction
        try:
            context = await self.create_context("prediction-context")
            context_id = context.id
        except Exception as e:
            return {"error": f"Failed to create prediction context: {str(e)}"}

        # Make the prediction
        try:
            result = await self.predict(
                model_id=entities["model_id"],
                context_id=context_id,
                input_data={"text": entities.get("input_data", "")}
            )
            return result
        except Exception as e:
            return {"error": f"Prediction failed: {str(e)}"}

    async def predict(
        self,
        model_id: str,
        context_id: str,
        input_data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Make a prediction using a model.

        Args:
            model_id: ID of the model to use for prediction
            context_id: ID of the context for this prediction
            input_data: Input data for the prediction
            **kwargs: Additional parameters to pass to the model

        Returns:
            Dictionary containing the prediction result
        """
        response = await self._make_request("POST", "/predict", {
            "model_id": model_id,
            "context_id": context_id,
            "input_data": input_data,
            **kwargs
        })

        # Try to parse the output data if it's a JSON string
        if isinstance(response.get("output_data"), str):
            try:
                response["output_data"] = json.loads(response["output_data"])
            except (json.JSONDecodeError, TypeError):
                pass

        return response

    # File operations
    async def upload_file(
        self,
        file_path: Union[str, Path],
        context_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Upload a file to the MCP server.

        Args:
            file_path: Path to the file to upload
            context_id: Optional ID of the context for this file
            metadata: Optional metadata for the file

        Returns:
            Dictionary containing the file upload response
        """
        query = """
        mutation UploadFile($input: FileInput!) {
            uploadFile(input: $input) {
                id
                name
                size
                type
                created_at
                updated_at
            }
        }
        """

        variables = {
            "input": {
                "file": file_path,
                "context_id": context_id,
                "metadata": metadata
            }
        }

        try:
            response = await self._make_request(
                "POST",
                "/graphql",
                data={"query": query, "variables": variables}
            )
            return response.get("data", {}).get("uploadFile")
        except Exception as e:
            raise MCPError(f"Failed to upload file: {str(e)}")

    async def search_customers(
        self,
        name: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        requested_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for customers with optional filters and field selection.

        Args:
            name: Optional name to search for (partial match on first and last name)
            state: Optional state to filter by
            limit: Maximum number of results to return (default: 10)
            offset: Number of results to skip (for pagination, default: 0)
            requested_fields: List of fields to include in the response. If None, returns all fields.
                             Available fields: id, name, email, phone, address, city, state, zipCode, country,
                                            createdAt, updatedAt, transcripts

        Returns:
            List of customer dictionaries with only the requested fields
        """
        # Default fields to include if none specified
        if not requested_fields:
            requested_fields = ['id', 'name', 'email', 'phone', 'state']

        # Map field names to their GraphQL representations
        field_mapping = {
            'id': 'id',
            'name': 'name',
            'email': 'email',
            'phone': 'phone',
            'address': 'address { street city state zipCode country }',
            'city': 'address { city }',
            'state': 'state',
            'zipCode': 'address { zipCode }',
            'country': 'address { country }',
            'createdAt': 'createdAt',
            'updatedAt': 'updatedAt',
            'transcripts': 'transcripts { id callDate duration }'
        }

        # Get the GraphQL fields to request
        graphql_fields = []
        for field in requested_fields:
            if field in field_mapping:
                graphql_fields.append(field_mapping[field])

        # Construct the GraphQL query
        fields_str = '\n                '.join(graphql_fields)

        # Construct the GraphQL query with dynamic fields
        query = f"""
        query SearchCustomers($name: String, $state: String, $limit: Int, $offset: Int) {{
            searchCustomers(
                name: $name,
                state: $state,
                limit: $limit,
                offset: $offset
            ) {{
                {fields_str}
            }}
        }}
        """.format(fields_str=fields_str)

        # Build filter arguments
        filter_args = {
            'name': name,
            'state': state,
            'limit': limit,
            'offset': offset
        }

        # Remove None values
        variables = {k: v for k, v in filter_args.items() if v is not None}

        try:
            response = await self._make_request(
                "POST",
                "/graphql",
                data={"query": query, "variables": variables}
            )

            if "errors" in response:
                error_messages = [e.get("message", "Unknown error") for e in response.get("errors", [])]
                raise MCPError(f"GraphQL error: {', '.join(error_messages)}")

            customers = response.get("data", {}).get("searchCustomers", [])

            # Process the response to handle nested fields
            processed_customers = []
            for customer in customers:
                processed_customer = {}
                for field in requested_fields:
                    if field in ['city', 'state', 'zipCode', 'country'] and 'address' in customer:
                        # Handle address subfields
                        processed_customer[field] = customer['address'].get(field) if field != 'state' else customer.get('state')
                    else:
                        processed_customer[field] = customer.get(field)
                processed_customers.append(processed_customer)

            return processed_customers

        except Exception as e:
            raise MCPError(f"Failed to search customers: {str(e)}")

    async def search_transcripts(
        self,
        customer_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search for call transcripts with optional filters.

        Args:
            customer_id: Optional customer ID to filter by
            agent_id: Optional agent ID to filter by
            start_date: Optional start date (ISO format) to filter transcripts
            end_date: Optional end date (ISO format) to filter transcripts
            limit: Maximum number of results to return (default: 10)
            offset: Number of results to skip (for pagination, default: 0)

        Returns:
            List of transcript dictionaries matching the search criteria
        """
        query = """
        query SearchTranscripts($filter: TranscriptFilterInput!) {
            searchTranscripts(filter: $filter) {
                callId
                customerId
                agentId
                callTimestamp
                callDurationSeconds
                callSummary
                isAdaRelated
                adaViolationOccurred
                transcript {
                    speaker
                    text
                    timestamp
                }
                sentiment {
                    polarity
                    subjectivity
                    analyzer
                }
                contexts
            }
        }
        """

        variables = {
            "filter": {
                "customer_id": customer_id,
                "agent_id": agent_id,
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit,
                "offset": offset
            }
        }

        try:
            response = await self._make_request(
                "POST",
                "/graphql",
                data={"query": query, "variables": variables}
            )
            return response.get("data", {}).get("searchTranscripts", [])
        except Exception as e:
            raise MCPError(f"Failed to search transcripts: {str(e)}")

    async def get_transcript(self, call_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific transcript by its ID.

        Args:
            call_id: The ID of the transcript to retrieve

        Returns:
            The transcript dictionary or None if not found
        """
        query = """
        query GetTranscript($callId: ID!) {
            getTranscript(call_id: $callId) {
                callId
                customerId
                agentId
                callTimestamp
                callDurationSeconds
                callSummary
                isAdaRelated
                adaViolationOccurred
                transcript {
                    speaker
                    text
                    timestamp
                }
                sentiment {
                    polarity
                    subjectivity
                    analyzer
                }
                contexts
            }
        }
        """

        try:
            response = await self._make_request(
                "POST",
                "/graphql",
                data={"query": query, "variables": {"callId": call_id}}
            )
            return response.get("data", {}).get("getTranscript")
        except Exception as e:
            raise MCPError(f"Failed to get transcript: {str(e)}")

    async def get_customers_with_transcripts(self) -> List[Dict[str, Any]]:
        """
        Get all customers that have at least one transcript.

        Returns:
            List of customer dictionaries with their transcripts
        """
        query = """
        query GetCustomersWithTranscripts {
            getCustomersWithTranscripts {
                customerId
                firstName
                lastName
                email
                phone
                city
                state
                transcripts {
                    callId
                    callTimestamp
                    callSummary
                }
            }
        }
        """

        try:
            response = await self._make_request(
                "POST",
                "/graphql",
                data={"query": query}
            )
            return response.get("data", {}).get("getCustomersWithTranscripts", [])
        except Exception as e:
            raise MCPError(f"Failed to get customers with transcripts: {str(e)}")

    async def list_tools(
        self,
        category: Optional[str] = None,
        available_only: bool = True,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all available tools with optional filtering.

        Args:
            category: Optional category to filter tools by
            available_only: Whether to only return available tools (default: True)
            limit: Maximum number of results to return (default: 10)
            offset: Number of results to skip (for pagination, default: 0)

        Returns:
            List of tool dictionaries matching the criteria
        """
        query = """
        query ListTools($category: String, $availableOnly: Boolean, $limit: Int, $offset: Int) {
            listTools(
                category: $category,
                available_only: $availableOnly,
                limit: $limit,
                offset: $offset
            ) {
                id
                name
                description
                category
                isAvailable
                createdAt
                updatedAt
            }
        }
        """

        variables = {
            "category": category,
            "availableOnly": available_only,
            "limit": limit,
            "offset": offset
        }

        try:
            response = await self._make_request(
                "POST",
                "/graphql",
                data={"query": query, "variables": variables}
            )
            return response.get("data", {}).get("listTools", [])
        except Exception as e:
            raise MCPError(f"Failed to list tools: {str(e)}")

    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the MCP server.

        Returns:
            Dictionary containing health status information
        """
        query = """
        query HealthCheck {
            health {
                status
                timestamp
                version
            }
        }
        """

        try:
            response = await self._make_request(
                "POST",
                "/graphql",
                data={"query": query}
            )
            return response.get("data", {}).get("health", {})
        except Exception as e:
            raise MCPError(f"Health check failed: {str(e)}")
