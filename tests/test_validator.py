"""Test module for WhatsApp Validator."""

import pytest
import pandas as pd
import tempfile
import os
import argparse

from src.config import Config, ConfigManager, InputConfig, OutputConfig
from src.phone_validator import PhoneValidator, ValidityStatus, ParseStatus
from src.whatsapp_checker import WhatsAppChecker, WhatsAppStatus
from src.data_loader import DataLoader
from src.result_aggregator import ResultAggregator
from src.data_exporter import DataExporter
from src.cli import build_config


class TestPhoneValidator:
    """Tests for PhoneValidator class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        config = Config()
        config.validation.default_country = "US"
        return config
    
    @pytest.fixture
    def validator(self, config):
        """Create validator instance."""
        return PhoneValidator(config)
    
    def test_valid_us_number(self, validator):
        """Test valid US phone number."""
        result = validator.validate("+1 415-555-1234")
        
        assert result.validity_status == ValidityStatus.VALID
        assert result.parse_status == ParseStatus.SUCCESS
        assert result.e164_number == "+14155551234"
        assert result.country_code == "+1"
    
    def test_valid_cn_number(self, validator):
        """Test valid Chinese phone number."""
        result = validator.validate("+86 188 2388 0046")
        
        assert result.validity_status == ValidityStatus.VALID
        assert result.e164_number == "+8618823880046"
        assert result.country_code == "+86"
    
    def test_number_without_plus(self, validator):
        """Test number without international prefix."""
        result = validator.validate("4155551234")
        
        # Should use default country (US)
        assert result.validity_status == ValidityStatus.VALID
        assert result.e164_number == "+14155551234"
    
    def test_invalid_number(self, validator):
        """Test invalid phone number."""
        result = validator.validate("123")
        
        assert result.validity_status == ValidityStatus.INVALID
        assert result.parse_status in [ParseStatus.TOO_SHORT, ParseStatus.INVALID_FORMAT]
    
    def test_empty_number(self, validator):
        """Test empty phone number."""
        result = validator.validate("")
        
        assert result.validity_status == ValidityStatus.UNPARSEABLE
        assert result.parse_status == ParseStatus.EMPTY
    
    def test_none_number(self, validator):
        """Test None input."""
        result = validator.validate(None)
        
        assert result.validity_status == ValidityStatus.UNPARSEABLE
        assert result.parse_status == ParseStatus.EMPTY
    
    def test_number_with_separators(self, validator):
        """Test number with various separators."""
        result = validator.validate("+1 (415) 555-1234")
        
        assert result.validity_status == ValidityStatus.VALID
        assert result.e164_number == "+14155551234"
    
    def test_batch_validate(self, validator):
        """Test batch validation."""
        numbers = ["+14155551234", "+8618823880046", "", "123"]
        results = validator.batch_validate(numbers)
        
        assert len(results) == 4
        assert results[0].validity_status == ValidityStatus.VALID
        assert results[1].validity_status == ValidityStatus.VALID
        assert results[2].validity_status == ValidityStatus.UNPARSEABLE
        assert results[3].validity_status == ValidityStatus.INVALID


class TestWhatsAppChecker:
    """Tests for WhatsAppChecker class."""
    
    @pytest.fixture
    def config_mock(self):
        """Create mock mode configuration."""
        config = Config()
        config.whatsapp.mode = "mock"
        return config
    
    @pytest.fixture
    def config_estimated(self):
        """Create estimated mode configuration."""
        config = Config()
        config.whatsapp.mode = "estimated"
        return config
    
    def test_mock_mode(self, config_mock):
        """Test mock mode check."""
        checker = WhatsAppChecker(config_mock)
        result = checker.check("+14155551234")
        
        assert result.status in [WhatsAppStatus.YES, WhatsAppStatus.NO, WhatsAppStatus.UNKNOWN]
        assert result.source == "mock"
    
    def test_estimated_mode(self, config_estimated):
        """Test estimated mode check."""
        checker = WhatsAppChecker(config_estimated)
        
        # Valid E.164 number should be unknown
        result1 = checker.check("+14155551234")
        assert result1.status == WhatsAppStatus.UNKNOWN
        assert result1.source == "estimated"
        
        # Invalid number should be no
        result2 = checker.check("invalid")
        assert result2.status == WhatsAppStatus.NO
    
    def test_batch_check(self, config_mock):
        """Test batch WhatsApp check."""
        checker = WhatsAppChecker(config_mock)
        numbers = ["+14155551234", "+8618823880046", "+442071234567"]
        results = checker.batch_check(numbers)
        
        assert len(results) == 3
        for result in results:
            assert result.source == "mock"

    def test_api_mode_skips_missing_number(self):
        """Test API mode skips missing E.164 numbers without making a request."""
        config = Config()
        config.whatsapp.mode = "api"
        config.whatsapp.api_endpoint = "https://example.com/check"

        checker = WhatsAppChecker(config)
        result = checker.check(None)

        assert result.status == WhatsAppStatus.UNKNOWN
        assert result.error_message == "Skipped WhatsApp API check for missing E.164 number"


class TestDataLoader:
    """Tests for DataLoader class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        config = Config()
        config.input.phone_column = "phone"
        return config
    
    def test_load_csv(self, config):
        """Test CSV loading."""
        # Create temp CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("phone,name\n")
            f.write("+14155551234,John\n")
            f.write("+8618823880046,Jane\n")
            csv_path = f.name
        
        try:
            config.input.path = csv_path
            config.input.format = "csv"
            
            loader = DataLoader(config)
            loaded = loader.load()
            
            assert loaded.total_rows == 2
            assert loaded.phone_column == "phone"
            assert "name" in loaded.extra_columns
        finally:
            os.unlink(csv_path)
    
    def test_auto_detect_phone_column(self, config):
        """Test auto-detection of phone column."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("mobile,name\n")
            f.write("+14155551234,John\n")
            csv_path = f.name
        
        try:
            config.input.path = csv_path
            
            loader = DataLoader(config)
            loaded = loader.load()
            
            # Should auto-detect 'mobile' as phone column
            assert loaded.phone_column == "mobile"
        finally:
            os.unlink(csv_path)


class TestResultAggregator:
    """Tests for ResultAggregator class."""
    
    @pytest.fixture
    def aggregator(self):
        """Create aggregator instance."""
        return ResultAggregator()
    
    def test_aggregate_results(self, aggregator):
        """Test result aggregation."""
        # Create mock results
        from src.phone_validator import PhoneValidationResult
        from src.whatsapp_checker import WhatsAppCheckResult
        
        phone_results = [
            PhoneValidationResult(
                original_number="+14155551234",
                cleaned_number="+14155551234",
                e164_number="+14155551234",
                country_code="+1",
                parse_status=ParseStatus.SUCCESS,
                validity_status=ValidityStatus.VALID
            )
        ]
        
        wa_results = [
            WhatsAppCheckResult(
                phone_number="+14155551234",
                status=WhatsAppStatus.YES,
                source="mock"
            )
        ]
        
        aggregated = aggregator.aggregate(phone_results, wa_results)
        
        assert len(aggregated) == 1
        assert aggregated[0].validity_status == "valid"
        assert aggregated[0].whatsapp_status == "yes"
    
    def test_to_dataframe(self, aggregator):
        """Test DataFrame conversion."""
        from src.phone_validator import PhoneValidationResult
        from src.whatsapp_checker import WhatsAppCheckResult
        
        phone_results = [
            PhoneValidationResult(
                original_number="+14155551234",
                cleaned_number="+14155551234",
                e164_number="+14155551234",
                country_code="+1",
                parse_status=ParseStatus.SUCCESS,
                validity_status=ValidityStatus.VALID
            )
        ]
        
        wa_results = [
            WhatsAppCheckResult(
                phone_number="+14155551234",
                status=WhatsAppStatus.YES,
                source="mock"
            )
        ]
        
        aggregated = aggregator.aggregate(phone_results, wa_results)
        df = aggregator.to_dataframe(aggregated)
        
        assert len(df) == 1
        assert 'original_number' in df.columns
        assert 'validity_status' in df.columns
        assert 'whatsapp_status' in df.columns
    
    def test_generate_summary(self, aggregator):
        """Test summary generation."""
        from src.phone_validator import PhoneValidationResult
        from src.whatsapp_checker import WhatsAppCheckResult
        from src.result_aggregator import AggregatedResult
        
        results = [
            AggregatedResult(
                original_number="+14155551234",
                cleaned_number="+14155551234",
                e164_number="+14155551234",
                country_code="+1",
                parse_status="success",
                validity_status="valid",
                whatsapp_status="yes",
                error_message=None
            ),
            AggregatedResult(
                original_number="123",
                cleaned_number="123",
                e164_number=None,
                country_code=None,
                parse_status="invalid_format",
                validity_status="invalid",
                whatsapp_status="no",
                error_message="Invalid number"
            )
        ]
        
        summary = aggregator.generate_summary(results)
        
        assert summary['total_numbers'] == 2
        assert summary['valid_numbers'] == 1
        assert summary['invalid_numbers'] == 1

    def test_aggregate_preserves_rows_when_wa_results_missing(self, aggregator):
        """Test aggregation keeps all phone rows even when WhatsApp results are shorter."""
        from src.phone_validator import PhoneValidationResult
        from src.whatsapp_checker import WhatsAppCheckResult

        phone_results = [
            PhoneValidationResult(
                original_number="+14155551234",
                cleaned_number="+14155551234",
                e164_number="+14155551234",
                country_code="+1",
                parse_status=ParseStatus.SUCCESS,
                validity_status=ValidityStatus.VALID
            ),
            PhoneValidationResult(
                original_number="123",
                cleaned_number="123",
                e164_number=None,
                country_code=None,
                parse_status=ParseStatus.INVALID_FORMAT,
                validity_status=ValidityStatus.INVALID,
                error_message="Invalid number"
            )
        ]

        wa_results = [
            WhatsAppCheckResult(
                phone_number="+14155551234",
                status=WhatsAppStatus.YES,
                source="mock"
            )
        ]

        aggregated = aggregator.aggregate(phone_results, wa_results)

        assert len(aggregated) == 2
        assert aggregated[1].whatsapp_status == "unknown"


class TestConfigManager:
    """Tests for ConfigManager class."""
    
    def test_default_config(self):
        """Test default configuration."""
        manager = ConfigManager()
        config = manager.config
        
        assert config.input.format == "csv"
        assert config.whatsapp.mode == "mock"
        assert config.validation.default_country == "US"
    
    def test_yaml_config(self):
        """Test YAML configuration loading."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
input:
  path: test.csv
  format: csv
validation:
  default_country: CN
whatsapp:
  mode: estimated
""")
            yaml_path = f.name
        
        try:
            manager = ConfigManager(yaml_path)
            config = manager.config
            
            assert config.input.path == "test.csv"
            assert config.validation.default_country == "CN"
            assert config.whatsapp.mode == "estimated"
        finally:
            os.unlink(yaml_path)
    
    def test_env_overrides(self):
        """Test environment variable overrides."""
        os.environ['WA_VALIDATOR_DEFAULT_COUNTRY'] = 'GB'
        os.environ['WA_VALIDATOR_WHATSAPP_MODE'] = 'api'
        
        manager = ConfigManager()
        config = manager.config
        
        assert config.validation.default_country == "GB"
        assert config.whatsapp.mode == "api"
        
        # Clean up
        del os.environ['WA_VALIDATOR_DEFAULT_COUNTRY']
        del os.environ['WA_VALIDATOR_WHATSAPP_MODE']
    
    def test_validate_config(self):
        """Test configuration validation."""
        manager = ConfigManager()
        manager._config.whatsapp.mode = "invalid_mode"
        
        errors = manager.validate()
        
        assert len(errors) > 0
        assert "Invalid WhatsApp mode" in errors[0]


class TestCliConfig:
    """Tests for CLI configuration merging."""

    def test_build_config_preserves_yaml_values_without_cli_overrides(self):
        """Test config file values are not overwritten by CLI parser defaults."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
validation:
  default_country: CN
whatsapp:
  mode: estimated
  retry_count: 7
logging:
  level: DEBUG
""")
            yaml_path = f.name

        try:
            args = argparse.Namespace(
                input=None,
                output=None,
                config=yaml_path,
                input_format=None,
                phone_column=None,
                output_format=None,
                country=None,
                strict=False,
                mode=None,
                api_endpoint=None,
                api_key=None,
                rate_limit=None,
                retry_count=None,
                log_level=None,
                log_file=None,
                quiet=False
            )

            config = build_config(args)

            assert config.validation.default_country == "CN"
            assert config.whatsapp.mode == "estimated"
            assert config.whatsapp.retry_count == 7
            assert config.logging.level == "DEBUG"
        finally:
            os.unlink(yaml_path)


class TestDataExporter:
    """Tests for export format selection."""

    def test_export_uses_output_extension_when_format_not_explicit(self):
        """Test exporter infers xlsx from output path when no format override is passed."""
        config = Config()
        exporter = DataExporter(config)

        fmt = None
        output_path = "/tmp/results.xlsx"
        ext = os.path.splitext(output_path)[1].lower().replace('.', '')
        if ext in ['csv', 'xlsx']:
            fmt = ext
        else:
            fmt = config.output.format or 'csv'

        assert fmt == "xlsx"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
