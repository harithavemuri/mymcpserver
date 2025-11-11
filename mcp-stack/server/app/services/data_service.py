"""Service for managing data sources and items."""
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Union

from loguru import logger

from ..models.data_models import DataItem, DataPage, DataQuery, DataSource, DataSourceType
from .data_loader import DataLoader

class DataService:
    """Service for managing data sources and items."""
    
    def __init__(self, data_dir: Union[str, Path]):
        """Initialize the data service."""
        self.data_dir = Path(data_dir).resolve()
        self.sources: Dict[str, DataSource] = {}
        self.items: Dict[str, DataItem] = {}
        
        # Create data directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    async def discover_data_sources(self) -> List[DataSource]:
        """Discover and register data sources in the data directory."""
        self.sources.clear()
        
        # Load all supported file types
        file_data = DataLoader.load_directory(
            self.data_dir,
            recursive=True,
            pattern="*.{json,csv,parquet}"
        )
        
        # Create data sources and items
        for file_path, data in file_data.items():
            try:
                source_id = f"src_{file_path.stem}"
                source_type = DataLoader.detect_source_type(file_path)
                
                source = DataSource(
                    id=source_id,
                    name=file_path.name,
                    path=file_path,
                    source_type=source_type,
                    metadata={
                        "file_size": file_path.stat().st_size,
                        "num_items": len(data)
                    }
                )
                
                # Create data items
                items = DataLoader.create_data_items(
                    source_id=source_id,
                    data=data,
                    metadata={"source_path": str(file_path.relative_to(self.data_dir))}
                )
                
                # Store source and items
                self.sources[source_id] = source
                for item in items:
                    self.items[item.id] = item
                
                logger.info(f"Discovered data source: {source_id} with {len(items)} items")
                
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                continue
        
        return list(self.sources.values())
    
    async def get_data_source(self, source_id: str) -> Optional[DataSource]:
        """Get a data source by ID."""
        return self.sources.get(source_id)
    
    async def list_data_sources(self) -> List[DataSource]:
        """List all data sources."""
        return list(self.sources.values())
    
    async def query_data_items(
        self,
        query: Optional[DataQuery] = None,
        source_id: Optional[str] = None
    ) -> DataPage[DataItem]:
        """Query data items with optional filtering and pagination."""
        query = query or DataQuery()
        items = list(self.items.values())
        
        # Filter by source if specified
        if source_id:
            items = [item for item in items if item.source_id == source_id]
        
        # Apply filters if specified
        if query.filters:
            filtered_items = []
            for item in items:
                match = True
                for key, value in query.filters.items():
                    if key in item.data and item.data[key] != value:
                        match = False
                        break
                if match:
                    filtered_items.append(item)
            items = filtered_items
        
        # Sort if specified
        if query.sort_by:
            reverse = query.sort_order.lower() == "desc"
            items.sort(
                key=lambda x: x.data.get(query.sort_by, ""),
                reverse=reverse
            )
        
        # Apply pagination
        total = len(items)
        start = query.offset
        end = start + query.limit
        paginated_items = items[start:end]
        
        return DataPage(
            items=paginated_items,
            total=total,
            page=query.offset // query.limit + 1,
            size=len(paginated_items),
            has_more=end < total
        )
    
    async def get_data_item(self, item_id: str) -> Optional[DataItem]:
        """Get a data item by ID."""
        return self.items.get(item_id)
    
    async def search_data_items(
        self,
        query: str,
        fields: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[DataItem]:
        """Search data items by text query."""
        results = []
        query = query.lower()
        
        for item in self.items.values():
            # If specific fields are provided, only search those
            search_fields = fields if fields else item.data.keys()
            
            for field in search_fields:
                if field in item.data:
                    value = str(item.data[field]).lower()
                    if query in value:
                        results.append(item)
                        break
            
            if len(results) >= limit:
                break
        
        return results[:limit]
