"""Configuration management module."""

import os
import yaml
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class InputConfig:
    """Input configuration settings."""
    path: str = "data/input.csv"
    format: str = "csv"
    phone_column: str = "phone"


@dataclass
class OutputConfig:
    """Output configuration settings."""
    path: str = "data/output.csv"
    format: str = "csv"


@dataclass
class ValidationConfig:
    """Validation configuration settings."""
    default_country: str = "US"
    strict_mode: bool = False


@dataclass
class WhatsAppConfig:
    """WhatsApp check configuration settings."""
    mode: str = "mock"  # api, mock, estimated
    api_endpoint: str = ""
    api_key: str = ""
    timeout: int = 10
    retry_count: int = 3
    retry_delay: float = 1.0


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_second: float = 5.0
    burst_limit: int = 10


@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: str = "INFO"
    file: str = "logs/validator.log"
    console: bool = True


@dataclass
class Config:
    """Main configuration container."""
    input: InputConfig = field(default_factory=InputConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    whatsapp: WhatsAppConfig = field(default_factory=WhatsAppConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


class ConfigManager:
    """
    Manages configuration loading and access.
    
    Supports:
    - YAML configuration files
    - Environment variable overrides
    - Default values
    """
    
    ENV_PREFIX = "WA_VALIDATOR_"
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to YAML configuration file (optional)
        """
        self._config = Config()
        if config_path:
            self.load_from_file(config_path)
        self._apply_env_overrides()
    
    def load_from_file(self, config_path: str) -> None:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to YAML configuration file
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        
        self._apply_dict(data)
    
    def _apply_dict(self, data: Dict[str, Any]) -> None:
        """Apply dictionary values to config."""
        if 'input' in data:
            self._update_dataclass(self._config.input, data['input'])
        if 'output' in data:
            self._update_dataclass(self._config.output, data['output'])
        if 'validation' in data:
            self._update_dataclass(self._config.validation, data['validation'])
        if 'whatsapp' in data:
            self._update_dataclass(self._config.whatsapp, data['whatsapp'])
        if 'rate_limit' in data:
            self._update_dataclass(self._config.rate_limit, data['rate_limit'])
        if 'logging' in data:
            self._update_dataclass(self._config.logging, data['logging'])
    
    def _update_dataclass(self, obj: Any, data: Dict[str, Any]) -> None:
        """Update dataclass fields from dictionary."""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        env_mappings = {
            'INPUT_PATH': ('input', 'path'),
            'INPUT_FORMAT': ('input', 'format'),
            'OUTPUT_PATH': ('output', 'path'),
            'OUTPUT_FORMAT': ('output', 'format'),
            'DEFAULT_COUNTRY': ('validation', 'default_country'),
            'WHATSAPP_MODE': ('whatsapp', 'mode'),
            'WHATSAPP_API_KEY': ('whatsapp', 'api_key'),
            'LOG_LEVEL': ('logging', 'level'),
        }
        
        for env_key, (section, attr) in env_mappings.items():
            full_key = f"{self.ENV_PREFIX}{env_key}"
            value = os.environ.get(full_key)
            if value:
                section_obj = getattr(self._config, section)
                setattr(section_obj, attr, value)
    
    @property
    def config(self) -> Config:
        """Get the current configuration."""
        return self._config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        from dataclasses import asdict
        return asdict(self._config)
    
    def validate(self) -> list:
        """
        Validate configuration settings.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate WhatsApp mode
        valid_modes = ['api', 'mock', 'estimated']
        if self._config.whatsapp.mode not in valid_modes:
            errors.append(
                f"Invalid WhatsApp mode '{self._config.whatsapp.mode}'. "
                f"Must be one of: {valid_modes}"
            )
        
        # Validate API mode requirements
        if self._config.whatsapp.mode == 'api':
            if not self._config.whatsapp.api_endpoint:
                errors.append("API endpoint required when WhatsApp mode is 'api'")
        
        # Validate input format
        valid_input_formats = ['csv', 'xlsx']
        if self._config.input.format not in valid_input_formats:
            errors.append(
                f"Invalid input format '{self._config.input.format}'. "
                f"Must be one of: {valid_input_formats}"
            )
        
        # Validate output format
        valid_output_formats = ['csv', 'xlsx']
        if self._config.output.format not in valid_output_formats:
            errors.append(
                f"Invalid output format '{self._config.output.format}'. "
                f"Must be one of: {valid_output_formats}"
            )
        
        return errors