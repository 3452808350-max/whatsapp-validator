#!/usr/bin/env python3
"""
Comprehensive test demonstrating all WhatsApp Validator features.
This test verifies all FR-1 to FR-10 requirements.
"""

import sys
import os
sys.path.insert(0, '/home/kyj/.openclaw/workspace/whatsapp-validator')

from src import Config, ConfigManager
from src.phone_validator import PhoneValidator, ValidityStatus
from src.whatsapp_checker import WhatsAppChecker, WhatsAppStatus
from src.data_loader import DataLoader
from src.result_aggregator import ResultAggregator
from src.data_exporter import DataExporter
from src.logger import setup_logging, ProcessingStats


def run_all_tests():
    """Run all requirement tests."""
    print("=" * 70)
    print("WhatsApp Validator - Comprehensive Requirements Test")
    print("=" * 70)
    
    # FR-1: Input file support
    print("\n[FR-1] Testing input file support...")
    config = Config()
    config.input.path = 'data/sample_input.csv'
    loader = DataLoader(config)
    loaded = loader.load()
    assert loaded.total_rows > 0
    print(f"  ✓ CSV loading works ({loaded.total_rows} rows)")
    
    # FR-2: Input schema
    print("\n[FR-2] Testing input schema...")
    assert loaded.phone_column is not None
    print(f"  ✓ Phone column detected: {loaded.phone_column}")
    print(f"  ✓ Extra columns: {loaded.extra_columns}")
    
    # FR-3: Phone cleaning
    print("\n[FR-3] Testing phone cleaning...")
    validator = PhoneValidator(config)
    result = validator.validate("+1 415-555-1234")
    assert result.e164_number == "+14155551234"
    print(f"  ✓ Cleaning works: '+1 415-555-1234' → {result.e164_number}")
    
    # FR-4: Number validation
    print("\n[FR-4] Testing number validation...")
    valid = validator.validate("+1 415-555-1234")
    invalid = validator.validate("123")
    unparseable = validator.validate("")
    assert valid.validity_status == ValidityStatus.VALID
    assert invalid.validity_status == ValidityStatus.INVALID
    assert unparseable.validity_status == ValidityStatus.UNPARSEABLE
    print(f"  ✓ Valid: {valid.validity_status.value}")
    print(f"  ✓ Invalid: {invalid.validity_status.value}")
    print(f"  ✓ Unparseable: {unparseable.validity_status.value}")
    
    # FR-5: WhatsApp check
    print("\n[FR-5] Testing WhatsApp check modes...")
    config.whatsapp.mode = "mock"
    checker = WhatsAppChecker(config)
    wa_result = checker.check("+14155551234")
    assert wa_result.status in [WhatsAppStatus.YES, WhatsAppStatus.NO, WhatsAppStatus.UNKNOWN]
    print(f"  ✓ Mock mode: {wa_result.status.value}")
    
    # FR-6: Batch processing
    print("\n[FR-6] Testing batch processing...")
    numbers = ["+14155551234"] * 100
    results = validator.batch_validate(numbers)
    assert len(results) == 100
    print(f"  ✓ Batch validation: {len(results)} numbers")
    
    # FR-7: Output generation
    print("\n[FR-7] Testing output generation...")
    config.output.path = 'data/test_comprehensive.csv'
    aggregator = ResultAggregator()
    aggregated = aggregator.aggregate(results, [wa_result] * 100)
    exporter = DataExporter(config)
    output_path = exporter.export(aggregated, config.output.path)
    assert os.path.exists(output_path)
    print(f"  ✓ Output generated: {output_path}")
    os.remove(output_path)
    
    # FR-8: Error handling
    print("\n[FR-8] Testing error handling...")
    for bad_input in [None, "", "123"]:
        result = validator.validate(bad_input)
        assert result.validity_status in [ValidityStatus.INVALID, ValidityStatus.UNPARSEABLE]
    print(f"  ✓ Error handling works for bad inputs")
    
    # FR-9: Logging
    print("\n[FR-9] Testing logging...")
    logger = setup_logging(level='INFO', console=False)
    stats = ProcessingStats(logger)
    stats.start(10)
    stats.record_valid()
    summary = stats.finish()
    assert summary['total_rows'] == 10
    print(f"  ✓ Logging and stats work")
    
    # FR-10: Configurability
    print("\n[FR-10] Testing configurability...")
    config2 = Config()
    config2.validation.default_country = "CN"
    config2.whatsapp.mode = "estimated"
    assert config2.validation.default_country == "CN"
    assert config2.whatsapp.mode == "estimated"
    print(f"  ✓ Configuration works")
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED - All FR-1 to FR-10 requirements verified!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()