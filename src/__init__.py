"""WhatsApp Number Validation Tool.

A practical data-processing tool to clean, validate, and check phone numbers
for potential WhatsApp availability.
"""

__version__ = "1.0.0"

from .config import Config, ConfigManager, InputConfig, OutputConfig, ValidationConfig
from .config import WhatsAppConfig, RateLimitConfig, LoggingConfig
from .logger import setup_logging, ProcessingStats
from .data_loader import DataLoader, LoadedData
from .phone_validator import PhoneValidator, PhoneValidationResult, ValidityStatus, ParseStatus
from .whatsapp_checker import WhatsAppChecker, WhatsAppCheckResult, WhatsAppStatus
from .result_aggregator import ResultAggregator, AggregatedResult
from .data_exporter import DataExporter

__all__ = [
    # Version
    "__version__",
    # Config
    "Config",
    "ConfigManager",
    "InputConfig",
    "OutputConfig",
    "ValidationConfig",
    "WhatsAppConfig",
    "RateLimitConfig",
    "LoggingConfig",
    # Logger
    "setup_logging",
    "ProcessingStats",
    # Data loader
    "DataLoader",
    "LoadedData",
    # Phone validator
    "PhoneValidator",
    "PhoneValidationResult",
    "ValidityStatus",
    "ParseStatus",
    # WhatsApp checker
    "WhatsAppChecker",
    "WhatsAppCheckResult",
    "WhatsAppStatus",
    # Result aggregator
    "ResultAggregator",
    "AggregatedResult",
    # Data exporter
    "DataExporter",
]