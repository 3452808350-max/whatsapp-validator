#!/usr/bin/env python3
"""
Quick test script for WhatsApp Validator
Demonstrates all core features
"""

import sys
sys.path.insert(0, '/home/kyj/.openclaw/workspace/whatsapp-validator')

from src import Config, PhoneValidator, WhatsAppChecker, DataLoader, ResultAggregator, DataExporter, setup_logging, ProcessingStats
from src.phone_validator import ValidityStatus

def test_phone_validation():
    """Test phone validation with various inputs."""
    print("=" * 60)
    print("WhatsApp Validator - Quick Test")
    print("=" * 60)
    
    print("\nTesting phone validation:\n")
    print(f"{'Original':<25} {'Cleaned':<20} {'Valid':<10} {'E164':<20}")
    print("-" * 75)
    
    config = Config()
    config.validation.default_country = "CN"  # Use China as default
    validator = PhoneValidator(config)
    
    test_numbers = [
        "+1 415-555-1234",
        "18823880046",
        "+86 188 2388 0046",
        "0755-12345678",
        "123",
        "",
        "+44 20 7123 4567"
    ]
    
    for number in test_numbers:
        result = validator.validate(number)
        print(f"{number:<25} {result.cleaned_number or 'None':<20} {result.validity_status.value:<10} {result.e164_number or 'None':<20}")
        if result.error_message:
            print(f"  → Error: {result.error_message}")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


def test_full_pipeline():
    """Test the full validation pipeline."""
    print("\n" + "=" * 60)
    print("Full Pipeline Test")
    print("=" * 60)
    
    # Setup
    logger = setup_logging(level='INFO', console=False)
    config = Config()
    config.input.path = 'data/sample_input.csv'
    config.output.path = 'data/test_output.csv'
    config.validation.default_country = 'US'
    config.whatsapp.mode = 'mock'
    
    stats = ProcessingStats(logger)
    
    # Step 1: Load data
    print("\n1. Loading data...")
    loader = DataLoader(config)
    loaded = loader.load()
    print(f"   ✓ Loaded {loaded.total_rows} rows from {config.input.path}")
    print(f"   ✓ Phone column: {loaded.phone_column}")
    print(f"   ✓ Extra columns: {loaded.extra_columns}")
    
    # Step 2: Validate phone numbers
    print("\n2. Validating phone numbers...")
    validator = PhoneValidator(config)
    phone_numbers = loaded.df[loaded.phone_column].tolist()
    phone_results = validator.batch_validate(phone_numbers)
    
    valid_count = sum(1 for r in phone_results if r.validity_status == ValidityStatus.VALID)
    invalid_count = sum(1 for r in phone_results if r.validity_status == ValidityStatus.INVALID)
    unparseable_count = sum(1 for r in phone_results if r.validity_status == ValidityStatus.UNPARSEABLE)
    
    print(f"   ✓ Valid: {valid_count}")
    print(f"   ✓ Invalid: {invalid_count}")
    print(f"   ✓ Unparseable: {unparseable_count}")
    
    # Step 3: Check WhatsApp
    print("\n3. Checking WhatsApp availability...")
    checker = WhatsAppChecker(config, stats)
    e164_numbers = [r.e164_number for r in phone_results]
    wa_results = checker.batch_check(e164_numbers)
    print(f"   ✓ Checked {len(wa_results)} numbers")
    
    # Step 4: Aggregate results
    print("\n4. Aggregating results...")
    aggregator = ResultAggregator(stats)
    aggregated = aggregator.aggregate(phone_results, wa_results, loaded.df, loaded.extra_columns)
    print(f"   ✓ Aggregated {len(aggregated)} results")
    
    # Step 5: Export
    print("\n5. Exporting results...")
    exporter = DataExporter(config)
    output_path = exporter.export(aggregated, config.output.path)
    print(f"   ✓ Exported to: {output_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Processing Summary")
    print("=" * 60)
    summary = stats.finish()
    print(f"\n   Total processed: {summary['total_rows']}")
    print(f"   Valid numbers: {summary['valid']}")
    print(f"   Invalid numbers: {summary['invalid']}")
    print(f"   Unparseable: {summary['unparseable']}")
    print(f"   WhatsApp found: {summary['whatsapp_found']}")
    print(f"   WhatsApp not found: {summary['whatsapp_not_found']}")
    print(f"   WhatsApp unknown: {summary['whatsapp_unknown']}")
    print(f"   Duration: {summary['duration_seconds']}s")
    
    print("\n" + "=" * 60)
    print("Pipeline test complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_phone_validation()
    test_full_pipeline()