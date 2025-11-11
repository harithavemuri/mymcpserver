"""Data loading functionality for MCP."""
import json
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from loguru import logger

from ..models.data_models import DataItem, DataSource, DataSourceType

class DataLoader:
    """Loads data from various file formats."""
    
    @classmethod
    def detect_source_type(cls, file_path: Union[str, Path]) -> DataSourceType:
        """Detect the type of data source from file extension."""
        path = Path(file_path)
        ext = path.suffix.lower()
        
        if ext == '.json':
            return DataSourceType.JSON
        elif ext == '.csv':
            return DataSourceType.CSV
        elif ext in ('.parquet', '.pq'):
            return DataSourceType.PARQUET
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    @classmethod
    def load_json_file(cls, file_path: Path) -> List[Dict[str, Any]]:
        """Load data from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return [data]
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON file {file_path}: {e}")
            raise
    
    @classmethod
    def load_csv_file(cls, file_path: Path) -> List[Dict[str, Any]]:
        """Load data from a CSV file."""
        try:
            df = pd.read_csv(file_path)
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Error loading CSV file {file_path}: {e}")
            raise
    
    @classmethod
    def load_parquet_file(cls, file_path: Path) -> List[Dict[str, Any]]:
        """Load data from a Parquet file."""
        try:
            df = pd.read_parquet(file_path)
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Error loading Parquet file {file_path}: {e}")
            raise
    
    @classmethod
    def load_file(cls, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Load data from a file, automatically detecting the format."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        source_type = cls.detect_source_type(path)
        
        if source_type == DataSourceType.JSON:
            return cls.load_json_file(path)
        elif source_type == DataSourceType.CSV:
            return cls.load_csv_file(path)
        elif source_type == DataSourceType.PARQUET:
            return cls.load_parquet_file(path)
        else:
            raise ValueError(f"Unsupported file type: {source_type}")
    
    @classmethod
    def load_directory(
        cls,
        directory: Union[str, Path],
        recursive: bool = True,
        pattern: str = "*.*"
    ) -> Dict[Path, List[Dict[str, Any]]]:
        """Load all data files from a directory."""
        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")
        
        result = {}
        glob_pattern = "**/" + pattern if recursive else pattern
        
        for file_path in dir_path.glob(glob_pattern):
            if file_path.is_file():
                try:
                    data = cls.load_file(file_path)
                    if data:
                        result[file_path] = data
                except Exception as e:
                    logger.warning(f"Skipping file {file_path}: {e}")
                    continue
        
        return result
    
    @classmethod
    def create_data_items(
        cls,
        source_id: str,
        data: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DataItem]:
        """Convert raw data to DataItem objects."""
        metadata = metadata or {}
        return [
            DataItem(
                id=f"item_{source_id}_{i}",
                source_id=source_id,
                data=item,
                metadata=metadata
            )
            for i, item in enumerate(data)
        ]
