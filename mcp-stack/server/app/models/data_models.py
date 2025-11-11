"""Data models for MCP data."""
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, Generic, Type

from pydantic import BaseModel, Field, validator
from pydantic.generics import GenericModel

DataT = TypeVar('DataT')

class DataSourceType(str, Enum):
    """Supported data source types."""
    JSON = "json"
    CSV = "csv"
    PARQUET = "parquet"

class DataSource(BaseModel):
    """Represents a data source in the MCP system."""
    id: str
    name: str
    description: Optional[str] = None
    path: Path
    source_type: DataSourceType
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""
        json_encoders = {
            Path: str,
            datetime: lambda dt: dt.isoformat(),
        }

class DataItem(BaseModel):
    """Represents a single data item from a data source."""
    id: str
    source_id: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class DataPage(GenericModel, Generic[DataT]):
    """Paginated data response."""
    items: List[DataT]
    total: int
    page: int
    size: int
    has_more: bool

class DataQuery(BaseModel):
    """Query parameters for data retrieval."""
    limit: int = 100
    offset: int = 0
    filters: Optional[Dict[str, Any]] = None
    sort_by: Optional[str] = None
    sort_order: str = "asc"

    @validator('limit')
    def validate_limit(cls, v):
        """Validate limit parameter."""
        if v < 1 or v > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        """Validate sort order parameter."""
        if v not in ("asc", "desc"):
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v
