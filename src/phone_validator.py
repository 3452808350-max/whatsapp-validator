"""Phone number cleaning and validation module."""

import re
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import phonenumbers
from phonenumbers import (
    parse, 
    format_number, 
    PhoneNumberFormat,
    is_valid_number,
    is_possible_number,
    NumberParseException
)

from .config import Config
from .logger import setup_logging

logger = setup_logging()


class ValidityStatus(Enum):
    """Phone number validity status."""
    VALID = "valid"
    INVALID = "invalid"
    UNPARSEABLE = "unparseable"


class ParseStatus(Enum):
    """Phone number parsing status."""
    SUCCESS = "success"
    MISSING_COUNTRY = "missing_country"
    INVALID_FORMAT = "invalid_format"
    TOO_SHORT = "too_short"
    TOO_LONG = "too_long"
    EMPTY = "empty"


@dataclass
class PhoneValidationResult:
    """Result of phone number validation."""
    original_number: str
    cleaned_number: Optional[str]
    e164_number: Optional[str]
    country_code: Optional[str]
    parse_status: ParseStatus
    validity_status: ValidityStatus
    error_message: Optional[str] = None
    formatted_national: Optional[str] = None
    formatted_international: Optional[str] = None
    carrier: Optional[str] = None


class PhoneValidator:
    """
    Handles phone number cleaning, normalization, and validation.
    
    Features:
    - Cleans and normalizes phone numbers
    - Converts to E.164 format
    - Validates phone number structure
    - Handles country code inference
    - Supports multiple input formats
    """
    
    # Characters to remove from phone numbers
    CLEANUP_PATTERN = re.compile(r'[\s\-\(\)\[\]\{\}\.]+')
    
    # Pattern to extract numbers from strings
    EXTRACT_PATTERN = re.compile(r'[\d\+]+')
    
    def __init__(self, config: Config):
        """
        Initialize phone validator.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.default_country = config.validation.default_country.upper()
        self.strict_mode = config.validation.strict_mode
    
    def validate(self, phone_input: Optional[str]) -> PhoneValidationResult:
        """
        Validate a phone number.
        
        Args:
            phone_input: Phone number string to validate
            
        Returns:
            PhoneValidationResult with validation details
        """
        # Handle empty/None input
        if phone_input is None or str(phone_input).strip() == '':
            return PhoneValidationResult(
                original_number=str(phone_input) if phone_input else '',
                cleaned_number=None,
                e164_number=None,
                country_code=None,
                parse_status=ParseStatus.EMPTY,
                validity_status=ValidityStatus.UNPARSEABLE,
                error_message="Empty or null phone number"
            )
        
        original = str(phone_input).strip()
        
        # Step 1: Clean the number
        cleaned = self._clean_number(original)
        
        if not cleaned:
            return PhoneValidationResult(
                original_number=original,
                cleaned_number=None,
                e164_number=None,
                country_code=None,
                parse_status=ParseStatus.INVALID_FORMAT,
                validity_status=ValidityStatus.UNPARSEABLE,
                error_message="No valid digits found in phone number"
            )
        
        # Step 2: Parse and validate with phonenumbers library
        try:
            result = self._parse_and_validate(original, cleaned)
            return result
        except Exception as e:
            logger.debug(f"Error parsing number '{original}': {e}")
            return PhoneValidationResult(
                original_number=original,
                cleaned_number=cleaned,
                e164_number=None,
                country_code=None,
                parse_status=ParseStatus.INVALID_FORMAT,
                validity_status=ValidityStatus.UNPARSEABLE,
                error_message=str(e)
            )
    
    def _clean_number(self, phone: str) -> Optional[str]:
        """
        Clean phone number by removing unnecessary characters.
        
        Args:
            phone: Raw phone number string
            
        Returns:
            Cleaned phone number or None if invalid
        """
        if not phone:
            return None
        
        # Remove common separators
        cleaned = self.CLEANUP_PATTERN.sub('', phone)
        
        # Extract digits and plus sign
        extracted = ''.join(self.EXTRACT_PATTERN.findall(cleaned))
        
        # Ensure it starts with + if it's an international number
        # But don't add + if the original already had it or if it's clearly local
        if phone.strip().startswith('+') and not extracted.startswith('+'):
            extracted = '+' + extracted
        
        return extracted if extracted else None
    
    def _parse_and_validate(
        self, 
        original: str, 
        cleaned: str
    ) -> PhoneValidationResult:
        """
        Parse and validate phone number using phonenumbers library.
        
        Args:
            original: Original phone number string
            cleaned: Cleaned phone number string
            
        Returns:
            PhoneValidationResult
        """
        # Try parsing with default country
        try:
            # First try parsing as international (with +)
            if cleaned.startswith('+'):
                parsed = parse(cleaned, None)
            else:
                # Try with default country
                parsed = parse(cleaned, self.default_country)
        except NumberParseException as e:
            # Try other approaches
            if 'Missing or invalid default region' in str(e):
                return PhoneValidationResult(
                    original_number=original,
                    cleaned_number=cleaned,
                    e164_number=None,
                    country_code=None,
                    parse_status=ParseStatus.MISSING_COUNTRY,
                    validity_status=ValidityStatus.UNPARSEABLE,
                    error_message=f"Cannot determine country code. Provide international format (+...) or set default country."
                )
            
            # Try adding + if missing
            if not cleaned.startswith('+'):
                try:
                    parsed = parse('+' + cleaned, None)
                except NumberParseException:
                    return self._handle_parse_error(original, cleaned, e)
            else:
                return self._handle_parse_error(original, cleaned, e)
        
        # Validate the parsed number
        is_possible = is_possible_number(parsed)
        is_valid = is_valid_number(parsed)
        
        # Determine status
        if is_valid:
            validity_status = ValidityStatus.VALID
            parse_status = ParseStatus.SUCCESS
            error_message = None
        elif is_possible:
            validity_status = ValidityStatus.INVALID
            parse_status = ParseStatus.INVALID_FORMAT
            error_message = "Number is possible but not valid (incorrect length or format)"
        else:
            validity_status = ValidityStatus.INVALID
            parse_status = ParseStatus.INVALID_FORMAT
            error_message = "Number is not a possible phone number"
        
        # Format the number
        try:
            e164 = format_number(parsed, PhoneNumberFormat.E164)
            national = format_number(parsed, PhoneNumberFormat.NATIONAL)
            international = format_number(parsed, PhoneNumberFormat.INTERNATIONAL)
        except Exception:
            e164 = cleaned
            national = None
            international = None
        
        # Get country code
        country_code = None
        if hasattr(parsed, 'country_code') and parsed.country_code:
            country_code = f"+{parsed.country_code}"
        
        return PhoneValidationResult(
            original_number=original,
            cleaned_number=cleaned,
            e164_number=e164,
            country_code=country_code,
            parse_status=parse_status,
            validity_status=validity_status,
            error_message=error_message,
            formatted_national=national,
            formatted_international=international
        )
    
    def _handle_parse_error(
        self, 
        original: str, 
        cleaned: str, 
        error: NumberParseException
    ) -> PhoneValidationResult:
        """Handle phonenumbers parsing errors."""
        error_type = error.error_type if hasattr(error, 'error_type') else None
        
        if error_type == NumberParseException.TOO_SHORT_AFTER_IDD:
            parse_status = ParseStatus.TOO_SHORT
            error_msg = "Phone number is too short"
        elif error_type == NumberParseException.TOO_LONG:
            parse_status = ParseStatus.TOO_LONG
            error_msg = "Phone number is too long"
        elif error_type == NumberParseException.TOO_SHORT_NSN:
            parse_status = ParseStatus.TOO_SHORT
            error_msg = "Phone number is too short"
        else:
            parse_status = ParseStatus.INVALID_FORMAT
            error_msg = f"Invalid phone number format: {str(error)}"
        
        return PhoneValidationResult(
            original_number=original,
            cleaned_number=cleaned,
            e164_number=None,
            country_code=None,
            parse_status=parse_status,
            validity_status=ValidityStatus.UNPARSEABLE,
            error_message=error_msg
        )
    
    def batch_validate(
        self, 
        phone_numbers: list
    ) -> list:
        """
        Validate a batch of phone numbers.
        
        Args:
            phone_numbers: List of phone number strings
            
        Returns:
            List of PhoneValidationResult objects
        """
        results = []
        for phone in phone_numbers:
            result = self.validate(phone)
            results.append(result)
        return results