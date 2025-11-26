"""GraphQL schema definition for the MCP Server."""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import strawberry
from strawberry.fastapi import BaseContext
from strawberry.types import Info as _Info
from strawberry.types.info import RootValueType

# Import data-related types and queries
from .data_types import DataQuery as DataQueryType, CustomerType, CallTranscriptType

# Context type for GraphQL resolvers
class GraphQLContext(BaseContext):
    """Custom context for GraphQL resolvers."""
    def __init__(self):
        super().__init__()
        # You can add custom context properties here
        self.request = None
        self.response = None

# Custom Info type that uses our custom Context
Info = _Info[GraphQLContext, RootValueType]

# --- Types ---
@strawberry.type
class ToolType:
    """A tool that can be used by the MCP system."""
    id: str
    name: str
    description: str
    category: str
    is_available: bool = True
    created_at: str
    updated_at: str

@strawberry.type
class ModelType:
    """A machine learning model in the MCP system."""
    id: str
    name: str
    description: Optional[str] = None
    version: str
    created_at: str
    updated_at: str

@strawberry.type
class ContextType:
    """Context information for model execution."""
    id: str
    name: str
    description: Optional[str] = None
    created_at: str
    updated_at: str

@strawberry.type
class PredictionType:
    """Prediction result from a model."""
    id: str
    model_id: str
    input_data: str  # JSON string
    output_data: str  # JSON string
    created_at: str

# --- Input Types ---
@strawberry.input
class ModelInput:
    """Input for creating or updating a model."""
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"

@strawberry.input
class ContextInput:
    """Input for creating or updating a context."""
    name: str
    description: Optional[str] = None

@strawberry.input
class PredictionInput:
    """Input for creating a prediction."""
    model_id: str
    context_id: str
    input_data: str  # JSON string

# --- Query ---
@strawberry.type
class HealthCheckType:
    """Health check response type."""
    status: str
    timestamp: str
    version: str = "1.0.0"

@strawberry.type
class Query:
    """Root query type."""
    @strawberry.field
    async def health(self, info: Info) -> HealthCheckType:
        """Health check endpoint."""
        return HealthCheckType(
            status="ok",
            timestamp=datetime.now().isoformat()
        )

    @strawberry.field
    async def list_tools(
        self,
        info: Info,
        category: Optional[str] = None,
        available_only: bool = True,
        limit: int = 10,
        offset: int = 0
    ) -> List[ToolType]:
        """
        List all available tools with optional filtering.

        Args:
            category: Filter tools by category
            available_only: Only return tools that are currently available
            limit: Maximum number of tools to return
            offset: Number of tools to skip for pagination

        Returns:
            List of ToolType objects
        """
        # TODO: Implement actual data fetching from your data source
        # This is a mock implementation
        mock_tools = [
            ToolType(
                id="1",
                name="text-generator",
                description="Generates text based on input",
                category="generation",
                is_available=True,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ),
            ToolType(
                id="2",
                name="image-classifier",
                description="Classifies images into categories",
                category="vision",
                is_available=True,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
        ]

        # Apply filters
        filtered_tools = [
            tool for tool in mock_tools
            if (not available_only or tool.is_available) and
               (not category or tool.category == category)
        ]

        # Apply pagination
        return filtered_tools[offset:offset + limit]

    @strawberry.field
    async def get_model(self, info: Info, id: str) -> Optional[ModelType]:
        """Get a model by ID."""
        # TODO: Implement actual data fetching
        return None

    @strawberry.field
    async def list_models(
        self,
        info: Info,
        limit: int = 10,
        offset: int = 0,
    ) -> List[ModelType]:
        """List all models with pagination."""
        # TODO: Implement actual data fetching
        return []

    @strawberry.field
    async def get_context(self, info: Info, id: str) -> Optional[ContextType]:
        """Get a context by ID."""
        # TODO: Implement actual data fetching
        return None

    @strawberry.field
    async def get_prediction(self, info: Info, id: str) -> Optional[PredictionType]:
        """Get a prediction by ID."""
        # TODO: Implement actual data fetching
        return None

# --- Mutation ---
@strawberry.type
class Mutation:
    """Root mutation type."""
    @strawberry.mutation
    async def create_model(self, info: Info, input: ModelInput) -> ModelType:
        """Create a new model."""
        # TODO: Implement actual creation
        return ModelType(
            id="1",
            name=input.name,
            description=input.description,
            version=input.version,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

    @strawberry.mutation
    async def create_prediction(self, info: Info, input: PredictionInput) -> PredictionType:
        """Create a new prediction."""
        # TODO: Implement actual prediction
        return PredictionType(
            id="1",
            model_id=input.model_id,
            input_data=input.input_data,
            output_data="{\"result\": \"sample_output\"}",
            created_at=datetime.now().isoformat()
        )

# Main Query class that combines all query types
@strawberry.type
class Query(DataQueryType):
    """Root query type."""
    @strawberry.field
    async def health(self, info: Info) -> HealthCheckType:
        """Health check endpoint."""
        return HealthCheckType(
            status="ok",
            timestamp=datetime.now().isoformat()
        )

    @strawberry.field
    async def list_tools(
        self,
        info: Info,
        category: Optional[str] = None,
        available_only: bool = True,
        limit: int = 10,
        offset: int = 0
    ) -> List[ToolType]:
        """List all available tools with optional filtering."""
        # This is a mock implementation
        mock_tools = [
            ToolType(
                id="1",
                name="text-generator",
                description="Generates text based on input",
                category="generation",
                is_available=True,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ),
            ToolType(
                id="2",
                name="image-classifier",
                description="Classifies images into categories",
                category="vision",
                is_available=True,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
        ]

        # Apply filters
        if category:
            mock_tools = [t for t in mock_tools if t.category == category]
        if available_only:
            mock_tools = [t for t in mock_tools if t.is_available]

        # Apply pagination
        return mock_tools[offset:offset + limit]

# Create the schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    types=[CustomerType, CallTranscriptType]  # Register custom types
)

def get_context() -> GraphQLContext:
    """Get the GraphQL context."""
    return GraphQLContext()
