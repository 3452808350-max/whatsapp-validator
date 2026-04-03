"""Main entry point for WhatsApp Validator."""

from .config import Config, ConfigManager
from .logger import setup_logging, ProcessingStats
from .data_loader import DataLoader, LoadedData
from .phone_validator import PhoneValidator, PhoneValidationResult, ValidityStatus
from .whatsapp_checker import WhatsAppChecker, WhatsAppCheckResult, WhatsAppStatus
from .result_aggregator import ResultAggregator, AggregatedResult
from .data_exporter import DataExporter
from .cli import main, run_validation

__all__ = [
    # Config
    'Config',
    'ConfigManager',
    # Logger
    'setup_logging',
    'ProcessingStats',
    # Data loader
    'DataLoader',
    'LoadedData',
    # Phone validator
    'PhoneValidator',
    'PhoneValidationResult',
    'ValidityStatus',
    # WhatsApp checker
    'WhatsAppChecker',
    'WhatsAppCheckResult',
    'WhatsAppStatus',
    # Result aggregator
    'ResultAggregator',
    'AggregatedResult',
    # Data exporter
    'DataExporter',
    # CLI
    'main',
    'run_validation',
]