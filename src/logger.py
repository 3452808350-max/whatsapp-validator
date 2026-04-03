"""Logging setup module."""

import logging
import os
import sys
from datetime import datetime
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """
    Configure and return the main logger.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file (optional)
        console: Whether to output to console
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("wa_validator")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Create log directory if needed
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


class ProcessingStats:
    """Track and log processing statistics."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.total_rows: int = 0
        self.valid_rows: int = 0
        self.invalid_rows: int = 0
        self.unparseable_rows: int = 0
        self.api_failures: int = 0
        self.skipped_rows: int = 0
        self.whatsapp_found: int = 0
        self.whatsapp_not_found: int = 0
        self.whatsapp_unknown: int = 0
    
    def start(self, total_rows: int) -> None:
        """Mark processing start."""
        self.start_time = datetime.now()
        self.total_rows = total_rows
        self.logger.info(f"Starting processing of {total_rows} rows...")
    
    def record_valid(self) -> None:
        """Record a valid number."""
        self.valid_rows += 1
    
    def record_invalid(self) -> None:
        """Record an invalid number."""
        self.invalid_rows += 1
    
    def record_unparseable(self) -> None:
        """Record an unparseable number."""
        self.unparseable_rows += 1
    
    def record_api_failure(self) -> None:
        """Record an API failure."""
        self.api_failures += 1
    
    def record_skipped(self) -> None:
        """Record a skipped row."""
        self.skipped_rows += 1
    
    def record_whatsapp(self, status: str) -> None:
        """Record WhatsApp check result."""
        if status == 'yes':
            self.whatsapp_found += 1
        elif status == 'no':
            self.whatsapp_not_found += 1
        else:
            self.whatsapp_unknown += 1
    
    def finish(self) -> dict:
        """Mark processing end and log summary."""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0
        
        summary = {
            'total_rows': self.total_rows,
            'valid': self.valid_rows,
            'invalid': self.invalid_rows,
            'unparseable': self.unparseable_rows,
            'api_failures': self.api_failures,
            'skipped': self.skipped_rows,
            'whatsapp_found': self.whatsapp_found,
            'whatsapp_not_found': self.whatsapp_not_found,
            'whatsapp_unknown': self.whatsapp_unknown,
            'duration_seconds': round(duration, 2)
        }
        
        self.logger.info("=" * 60)
        self.logger.info("PROCESSING COMPLETE")
        self.logger.info("=" * 60)
        self.logger.info(f"Total rows processed: {self.total_rows}")
        self.logger.info(f"Valid numbers: {self.valid_rows}")
        self.logger.info(f"Invalid numbers: {self.invalid_rows}")
        self.logger.info(f"Unparseable numbers: {self.unparseable_rows}")
        self.logger.info(f"API failures: {self.api_failures}")
        self.logger.info(f"Skipped rows: {self.skipped_rows}")
        self.logger.info(f"WhatsApp found: {self.whatsapp_found}")
        self.logger.info(f"WhatsApp not found: {self.whatsapp_not_found}")
        self.logger.info(f"WhatsApp unknown: {self.whatsapp_unknown}")
        self.logger.info(f"Duration: {duration:.2f} seconds")
        self.logger.info("=" * 60)
        
        return summary