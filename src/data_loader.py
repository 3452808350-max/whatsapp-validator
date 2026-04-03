"""Data loading module for CSV and Excel files."""

import os
from typing import List, Optional, Dict, Any
import pandas as pd
from dataclasses import dataclass

from .config import Config
from .logger import setup_logging

logger = setup_logging()


@dataclass
class LoadedData:
    """Container for loaded data."""
    df: pd.DataFrame
    phone_column: str
    total_rows: int
    extra_columns: List[str]
    errors: List[str]


class DataLoader:
    """
    Handles loading phone number data from CSV and Excel files.
    
    Features:
    - Supports .csv and .xlsx formats
    - Auto-detects phone number column
    - Preserves extra columns (name, country, source, notes)
    - Handles encoding issues
    """
    
    PHONE_COLUMN_NAMES = [
        'phone', 'Phone', 'PHONE',
        'phone_number', 'phone_number', 'PhoneNumber',
        'mobile', 'Mobile', 'MOBILE',
        'cell', 'Cell', 'CELL',
        'number', 'Number', 'NUMBER',
        'tel', 'Tel', 'TEL',
        'contact', 'Contact', 'CONTACT'
    ]
    
    SUPPORTED_COLUMNS = ['name', 'country', 'source', 'notes']
    
    def __init__(self, config: Config):
        """
        Initialize data loader.
        
        Args:
            config: Configuration object
        """
        self.config = config
    
    def load(self, file_path: Optional[str] = None) -> LoadedData:
        """
        Load data from file.
        
        Args:
            file_path: Override path (uses config if not provided)
            
        Returns:
            LoadedData object with DataFrame and metadata
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format not supported
        """
        path = file_path or self.config.input.path
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Input file not found: {path}")
        
        logger.info(f"Loading data from: {path}")
        
        # Determine format from file extension or config
        file_format = self._get_format(path)
        
        # Load based on format
        if file_format == 'csv':
            df = self._load_csv(path)
        elif file_format == 'xlsx':
            df = self._load_excel(path)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
        
        logger.info(f"Loaded {len(df)} rows from {path}")
        
        # Detect or validate phone column
        phone_column = self._find_phone_column(df)
        
        if phone_column is None:
            # Try to use configured column
            phone_column = self.config.input.phone_column
            if phone_column not in df.columns:
                raise ValueError(
                    f"Phone column '{phone_column}' not found. "
                    f"Available columns: {list(df.columns)}"
                )
        
        logger.info(f"Using phone column: {phone_column}")
        
        # Find extra columns
        extra_columns = [col for col in df.columns 
                        if col != phone_column and col.lower() in self.SUPPORTED_COLUMNS]
        
        if extra_columns:
            logger.info(f"Found extra columns: {extra_columns}")
        
        return LoadedData(
            df=df,
            phone_column=phone_column,
            total_rows=len(df),
            extra_columns=extra_columns,
            errors=[]
        )
    
    def _get_format(self, path: str) -> str:
        """Determine file format from path or config."""
        ext = os.path.splitext(path)[1].lower().replace('.', '')
        if ext in ['csv', 'xlsx']:
            return ext
        return self.config.input.format
    
    def _load_csv(self, path: str) -> pd.DataFrame:
        """Load CSV file with encoding handling."""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(
                    path,
                    encoding=encoding,
                    dtype=str,
                    keep_default_na=False
                )
                logger.debug(f"Successfully loaded CSV with encoding: {encoding}")
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"Error loading CSV: {e}")
                raise
        
        raise ValueError(f"Could not read CSV file with any supported encoding: {path}")
    
    def _load_excel(self, path: str) -> pd.DataFrame:
        """Load Excel file."""
        try:
            df = pd.read_excel(
                path,
                dtype=str,
                engine='openpyxl',
                keep_default_na=False
            )
            return df
        except Exception as e:
            logger.error(f"Error loading Excel: {e}")
            raise
    
    def _find_phone_column(self, df: pd.DataFrame) -> Optional[str]:
        """Find the most likely phone number column."""
        for col_name in self.PHONE_COLUMN_NAMES:
            if col_name in df.columns:
                return col_name
        return None
