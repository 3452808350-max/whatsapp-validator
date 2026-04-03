"""WhatsApp availability checking module."""

import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import requests
from requests.exceptions import RequestException, Timeout

from .config import Config
from .logger import setup_logging, ProcessingStats

logger = setup_logging()


class WhatsAppStatus(Enum):
    """WhatsApp availability status."""
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


@dataclass
class WhatsAppCheckResult:
    """Result of WhatsApp availability check."""
    phone_number: str
    status: WhatsAppStatus
    source: str  # api, mock, estimated
    error_message: Optional[str] = None
    api_response: Optional[Dict[str, Any]] = None
    checked_at: Optional[str] = None


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, requests_per_second: float, burst_limit: int):
        self.min_interval = 1.0 / requests_per_second
        self.burst_limit = burst_limit
        self.last_request_time = 0.0
        self.request_count = 0
    
    def wait(self) -> None:
        """Wait if necessary to respect rate limits."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        
        self.last_request_time = time.time()
        self.request_count += 1


class WhatsAppChecker:
    """
    Checks WhatsApp availability for phone numbers.
    
    Supports three modes:
    - API: True lookup through third-party API
    - Mock: Placeholder/mock mode for development
    - Estimated: Estimate based on phone validity only
    """
    
    def __init__(self, config: Config, stats: Optional[ProcessingStats] = None):
        """
        Initialize WhatsApp checker.
        
        Args:
            config: Configuration object
            stats: Processing stats tracker (optional)
        """
        self.config = config
        self.stats = stats
        self.mode = config.whatsapp.mode
        self.rate_limiter = RateLimiter(
            config.rate_limit.requests_per_second,
            config.rate_limit.burst_limit
        )
        
        # API configuration
        self.api_endpoint = config.whatsapp.api_endpoint
        self.api_key = config.whatsapp.api_key
        self.timeout = config.whatsapp.timeout
        self.retry_count = config.whatsapp.retry_count
        self.retry_delay = config.whatsapp.retry_delay
    
    def check(self, phone_number: Optional[str]) -> WhatsAppCheckResult:
        """
        Check WhatsApp availability for a phone number.
        
        Args:
            phone_number: Phone number in E.164 format
            
        Returns:
            WhatsAppCheckResult with availability status
        """
        if self.mode == 'api':
            return self._check_via_api(phone_number)
        elif self.mode == 'mock':
            return self._check_mock(phone_number)
        else:  # estimated
            return self._check_estimated(phone_number)
    
    def _check_via_api(self, phone_number: Optional[str]) -> WhatsAppCheckResult:
        """
        Check WhatsApp availability via API.
        
        Args:
            phone_number: Phone number in E.164 format
            
        Returns:
            WhatsAppCheckResult
        """
        if not phone_number:
            if self.stats:
                self.stats.record_skipped()
                self.stats.record_whatsapp(WhatsAppStatus.UNKNOWN.value)
            return WhatsAppCheckResult(
                phone_number=phone_number or "",
                status=WhatsAppStatus.UNKNOWN,
                source='api',
                error_message="Skipped WhatsApp API check for missing E.164 number"
            )

        if not self.api_endpoint:
            logger.error("API endpoint not configured")
            return WhatsAppCheckResult(
                phone_number=phone_number,
                status=WhatsAppStatus.UNKNOWN,
                source='api',
                error_message="API endpoint not configured"
            )
        
        # Apply rate limiting
        self.rate_limiter.wait()
        
        # Prepare request
        headers = {
            'Content-Type': 'application/json',
        }
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        payload = {
            'phone': phone_number
        }
        
        # Make request with retries
        for attempt in range(self.retry_count):
            try:
                response = requests.post(
                    self.api_endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Parse API response
                # Adjust this based on your API's response format
                is_registered = data.get('registered', data.get('has_whatsapp', False))
                
                status = WhatsAppStatus.YES if is_registered else WhatsAppStatus.NO
                
                if self.stats:
                    self.stats.record_whatsapp(status.value)
                
                return WhatsAppCheckResult(
                    phone_number=phone_number,
                    status=status,
                    source='api',
                    api_response=data,
                    checked_at=self._get_timestamp()
                )
                
            except Timeout:
                logger.warning(f"Timeout checking {phone_number} (attempt {attempt + 1}/{self.retry_count})")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
                continue
                
            except RequestException as e:
                logger.error(f"API error for {phone_number}: {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
                continue
                
            except Exception as e:
                logger.error(f"Unexpected error checking {phone_number}: {e}")
                break
        
        # All retries failed
        if self.stats:
            self.stats.record_api_failure()
        
        return WhatsAppCheckResult(
            phone_number=phone_number,
            status=WhatsAppStatus.UNKNOWN,
            source='api',
            error_message="API request failed after all retries"
        )
    
    def _check_mock(self, phone_number: Optional[str]) -> WhatsAppCheckResult:
        """
        Mock check for development/testing.
        
        Returns random-ish status based on number patterns.
        
        Args:
            phone_number: Phone number in E.164 format
            
        Returns:
            WhatsAppCheckResult
        """
        # Simple mock logic: use last digit to determine status
        # This is for testing only
        if not phone_number:
            status = WhatsAppStatus.UNKNOWN
        else:
            last_digit = phone_number[-1] if phone_number else '0'
            if last_digit in '0123':
                status = WhatsAppStatus.YES
            elif last_digit in '456':
                status = WhatsAppStatus.NO
            else:
                status = WhatsAppStatus.UNKNOWN
        
        if self.stats:
            self.stats.record_whatsapp(status.value)
        
        return WhatsAppCheckResult(
            phone_number=phone_number,
            status=status,
            source='mock',
            checked_at=self._get_timestamp()
        )
    
    def _check_estimated(self, phone_number: Optional[str]) -> WhatsAppCheckResult:
        """
        Estimate WhatsApp availability based on phone validity.
        
        This mode doesn't actually check WhatsApp - it just marks
        valid numbers as 'unknown' and invalid as 'no'.
        
        Args:
            phone_number: Phone number in E.164 format
            
        Returns:
            WhatsAppCheckResult
        """
        # In estimated mode, we can't actually know
        # If we have a valid E.164 number, mark as unknown
        # If not, mark as no
        
        if phone_number and phone_number.startswith('+'):
            status = WhatsAppStatus.UNKNOWN
        else:
            status = WhatsAppStatus.NO
        
        if self.stats:
            self.stats.record_whatsapp(status.value)
        
        return WhatsAppCheckResult(
            phone_number=phone_number,
            status=status,
            source='estimated',
            checked_at=self._get_timestamp()
        )
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    def batch_check(self, phone_numbers: list) -> list:
        """
        Check WhatsApp availability for multiple numbers.
        
        Args:
            phone_numbers: List of phone numbers in E.164 format
            
        Returns:
            List of WhatsAppCheckResult objects
        """
        results = []
        total = len(phone_numbers)
        
        for i, phone in enumerate(phone_numbers, 1):
            if i % 100 == 0:
                logger.info(f"WhatsApp check progress: {i}/{total}")
            
            result = self.check(phone)
            results.append(result)
        
        return results
