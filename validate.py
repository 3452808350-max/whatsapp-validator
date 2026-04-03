#!/usr/bin/env python3
"""Quick validation script for testing the tool."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src import Config, PhoneValidator, WhatsAppChecker

def test_validation():
    """Test phone validation with sample numbers."""
    print("=" * 60)
    print("WhatsApp Validator - Quick Test")
    print("=" * 60)
    
    config = Config()
    config.validation.default_country = "US"
    config.whatsapp.mode = "mock"
    
    # Test numbers
    test_numbers = [
        "+1 415-555-1234",
        "18823880046",
        "+86 188 2388 0046",
        "0755-12345678",
        "123",
        "",
        "+44 20 7123 4567",
    ]
    
    validator = PhoneValidator(config)
    checker = WhatsAppChecker(config)
    
    print("\nTesting phone validation:\n")
    print(f"{'Original':<25} {'Cleaned':<20} {'Valid':<10} {'E164':<20}")
    print("-" * 75)
    
    for number in test_numbers:
        result = validator.validate(number)
        wa_result = checker.check(result.e164_number or "")
        
        print(f"{result.original_number[:24]:<25} "
              f"{str(result.cleaned_number)[:19]:<20} "
              f"{result.validity_status.value:<10} "
              f"{str(result.e164_number)[:19]:<20}")
        
        if result.error_message:
            print(f"  → Error: {result.error_message}")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_validation()