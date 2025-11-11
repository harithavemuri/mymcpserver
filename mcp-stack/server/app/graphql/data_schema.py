"""GraphQL schema for data access."""
from datetime import datetime
from typing import List, Optional

import strawberry
from strawberry.types import Info

from ..models.data_models import DataItem, DataPage, DataQuery, DataSource
from ..services.data_service import DataService


@strawberry.type
class HealthCheckType:
    """Health check response type."""
    status: str
    timestamp: str
    version: str = "1.0.0"


@strawberry.type
class DataSourceType:
    """GraphQL type for a data source."""
    id: str
    name: str
    description: Optional[str]
    path: str
    source_type: str
    metadata: strawberry.scalars.JSON
    created_at: str
    updated_at: str


@strawberry.type
class DataItemType:
    """GraphQL type for a data item."""
    id: str
    source_id: str
    data: strawberry.scalars.JSON
    metadata: strawberry.scalars.JSON
    created_at: str
    updated_at: str


@strawberry.input
class DataQueryInput:
    """Input type for querying data items."""
    limit: int = 100
    offset: int = 0
    filters: Optional[strawberry.scalars.JSON] = None
    sort_by: Optional[str] = None
    sort_order: str = "asc"


@strawberry.type
class DataPageType:
    """Paginated data response."""
    items: List[DataItemType]
    total: int
    page: int
    size: int
    has_more: bool


def get_data_service(info) -> DataService:
    """Get the data service from the context."""
    return info.context["data_service"]


@strawberry.type
class DataQuery:
    @strawberry.field
    async def health(self, info: Info) -> HealthCheckType:
        """Health check endpoint."""
        return HealthCheckType(
            status="ok",
            timestamp=datetime.utcnow().isoformat(),
            version="1.0.0"
        )

    """Data-related queries."""
    
    @strawberry.field
    async def data_sources(self, info: Info) -> List[DataSourceType]:
        """Get all data sources."""
        data_service = get_data_service(info)
        sources = await data_service.list_data_sources()
        return [
            DataSourceType(
                id=source.id,
                name=source.name,
                description=source.description,
                path=str(source.path),
                source_type=source.source_type.value,
                metadata=source.metadata,
                created_at=source.created_at.isoformat(),
                updated_at=source.updated_at.isoformat(),
            )
            for source in sources
        ]
    
    @strawberry.field
    async def data_source(
        self,
        info: Info,
        id: str
    ) -> Optional[DataSourceType]:
        """Get a data source by ID."""
        data_service = get_data_service(info)
        source = await data_service.get_data_source(id)
        if not source:
            return None
            
        return DataSourceType(
            id=source.id,
            name=source.name,
            description=source.description,
            path=str(source.path),
            source_type=source.source_type.value,
            metadata=source.metadata,
            created_at=source.created_at.isoformat(),
            updated_at=source.updated_at.isoformat(),
        )
    
    @strawberry.field
    async def data_items(
        self,
        info: Info,
        source_id: Optional[str] = None,
        query: Optional[DataQueryInput] = None,
    ) -> DataPageType:
        """Query data items with optional filtering and pagination."""
        data_service = get_data_service(info)
        
        # Convert input to internal query object
        query_obj = DataQuery(
            limit=query.limit if query else 100,
            offset=query.offset if query else 0,
            filters=query.filters if query and query.filters else {},
            sort_by=query.sort_by if query else None,
            sort_order=query.sort_order if query else "asc",
        )
        
        # Execute query
        result = await data_service.query_data_items(
            query=query_obj,
            source_id=source_id,
        )
        
        # Convert to GraphQL types
        items = [
            DataItemType(
                id=item.id,
                source_id=item.source_id,
                data=item.data,
                metadata=item.metadata,
                created_at=item.created_at.isoformat(),
                updated_at=item.updated_at.isoformat(),
            )
            for item in result.items
        ]
        
        return DataPageType(
            items=items,
            total=result.total,
            page=result.page,
            size=result.size,
            has_more=result.has_more,
        )
    
    @strawberry.field
    async def search_data_items(
        self,
        info: Info,
        query: str,
        fields: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[DataItemType]:
        """Search data items by text query."""
        data_service = get_data_service(info)
        items = await data_service.search_data_items(
            query=query,
            fields=fields,
            limit=limit,
        )
        
        return [
            DataItemType(
                id=item.id,
                source_id=item.source_id,
                data=item.data,
                metadata=item.metadata,
                created_at=item.created_at.isoformat(),
                updated_at=item.updated_at.isoformat(),
            )
            for item in items
        ]
