"""Command-line interface for WhatsApp Validator."""

import argparse
import os
import sys
from typing import Optional

from .config import ConfigManager, Config
from .logger import setup_logging, ProcessingStats
from .data_loader import DataLoader
from .phone_validator import PhoneValidator
from .whatsapp_checker import WhatsAppChecker
from .result_aggregator import ResultAggregator
from .data_exporter import DataExporter


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog='wa-validator',
        description='WhatsApp Number Validation Tool - Clean, validate, and check phone numbers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic validation with default config
  wa-validator input.csv output.csv
  
  # Use config file
  wa-validator --config config.yaml
  
  # Specify country code
  wa-validator input.csv output.csv --country CN
  
  # Use API mode for WhatsApp check
  wa-validator input.csv output.csv --mode api --api-endpoint https://api.example.com/check
  
  # Process Excel files
  wa-validator input.xlsx output.xlsx --format xlsx
"""
    )
    
    # Positional arguments
    parser.add_argument(
        'input',
        nargs='?',
        help='Input file path (CSV or Excel)'
    )
    
    parser.add_argument(
        'output',
        nargs='?',
        help='Output file path (CSV or Excel)'
    )
    
    # Configuration
    parser.add_argument(
        '-c', '--config',
        help='Path to configuration file (YAML)'
    )
    
    # Input options
    parser.add_argument(
        '--input-format',
        choices=['csv', 'xlsx'],
        help='Input file format (auto-detected from extension by default)'
    )
    
    parser.add_argument(
        '--phone-column',
        default=None,
        help='Name of the phone number column (default: phone)'
    )
    
    # Output options
    parser.add_argument(
        '--output-format',
        choices=['csv', 'xlsx'],
        help='Output file format (auto-detected from extension by default)'
    )
    
    # Validation options
    parser.add_argument(
        '--country',
        default=None,
        help='Default country code for phone number parsing (default: US)'
    )
    
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Enable strict mode (reject numbers without country code)'
    )
    
    # WhatsApp check options
    parser.add_argument(
        '--mode',
        choices=['api', 'mock', 'estimated'],
        default=None,
        help='WhatsApp check mode (default: mock)'
    )
    
    parser.add_argument(
        '--api-endpoint',
        help='API endpoint for WhatsApp check (required for api mode)'
    )
    
    parser.add_argument(
        '--api-key',
        help='API key for WhatsApp check'
    )
    
    # Rate limiting
    parser.add_argument(
        '--rate-limit',
        type=float,
        default=None,
        help='API requests per second (default: 5.0)'
    )
    
    parser.add_argument(
        '--retry-count',
        type=int,
        default=None,
        help='Number of API retries (default: 3)'
    )
    
    # Logging
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default=None,
        help='Log level (default: INFO)'
    )
    
    parser.add_argument(
        '--log-file',
        help='Path to log file'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress console output'
    )
    
    # Version
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    return parser


def validate_args(args: argparse.Namespace) -> list:
    """
    Validate command-line arguments.
    
    Args:
        args: Parsed arguments
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Check required arguments (unless config file is provided)
    if not args.config:
        if not args.input:
            errors.append("Input file is required (or use --config)")
        if not args.output:
            errors.append("Output file is required (or use --config)")
    
    # Validate API mode
    if args.mode == 'api' and not args.api_endpoint:
        errors.append("--api-endpoint is required when using api mode")
    
    # Validate input file exists
    if args.input and not os.path.exists(args.input):
        errors.append(f"Input file not found: {args.input}")
    
    return errors


def build_config(args: argparse.Namespace) -> Config:
    """
    Build configuration from CLI arguments.
    
    Args:
        args: Parsed arguments
        
    Returns:
        Config object
    """
    # Start with config file if provided
    if args.config:
        manager = ConfigManager(args.config)
    else:
        manager = ConfigManager()
    
    config = manager.config
    
    # Override with CLI arguments
    if args.input:
        config.input.path = args.input
        config.input.format = args.input_format or detect_format(args.input)
    
    if args.output:
        config.output.path = args.output
        config.output.format = args.output_format or detect_format(args.output)
    
    if args.phone_column is not None:
        config.input.phone_column = args.phone_column
    
    if args.country is not None:
        config.validation.default_country = args.country
    
    if args.strict:
        config.validation.strict_mode = True
    
    if args.mode is not None:
        config.whatsapp.mode = args.mode
    
    if args.api_endpoint:
        config.whatsapp.api_endpoint = args.api_endpoint
    
    if args.api_key:
        config.whatsapp.api_key = args.api_key
    
    if args.rate_limit is not None:
        config.rate_limit.requests_per_second = args.rate_limit
    
    if args.retry_count is not None:
        config.whatsapp.retry_count = args.retry_count
    
    if args.log_level is not None:
        config.logging.level = args.log_level
    
    if args.log_file:
        config.logging.file = args.log_file
    
    if args.quiet:
        config.logging.console = False
    
    return config


def detect_format(filepath: str) -> str:
    """
    Detect file format from extension.
    
    Args:
        filepath: File path
        
    Returns:
        Format string (csv or xlsx)
    """
    ext = os.path.splitext(filepath)[1].lower().replace('.', '')
    return ext if ext in ['csv', 'xlsx'] else 'csv'


def run_validation(config: Config) -> dict:
    """
    Run the validation pipeline.
    
    Args:
        config: Configuration object
        
    Returns:
        Dictionary with results and statistics
    """
    # Setup logging
    logger = setup_logging(
        level=config.logging.level,
        log_file=config.logging.file,
        console=config.logging.console
    )
    
    logger.info("=" * 60)
    logger.info("WhatsApp Validator - Starting")
    logger.info("=" * 60)
    
    # Initialize stats
    stats = ProcessingStats(logger)
    
    try:
        # Step 1: Load data
        logger.info("Step 1: Loading input data...")
        loader = DataLoader(config)
        loaded_data = loader.load()
        stats.start(loaded_data.total_rows)
        
        # Step 2: Validate phone numbers
        logger.info("Step 2: Validating phone numbers...")
        validator = PhoneValidator(config)
        phone_numbers = loaded_data.df[loaded_data.phone_column].tolist()
        phone_results = validator.batch_validate(phone_numbers)
        
        # Step 3: Check WhatsApp availability
        logger.info("Step 3: Checking WhatsApp availability...")
        wa_checker = WhatsAppChecker(config, stats)
        e164_numbers = [r.e164_number for r in phone_results]
        wa_results = wa_checker.batch_check(e164_numbers)
        
        # Step 4: Aggregate results
        logger.info("Step 4: Aggregating results...")
        aggregator = ResultAggregator(stats)
        aggregated_results = aggregator.aggregate(
            phone_results,
            wa_results,
            loaded_data.df,
            loaded_data.extra_columns
        )
        
        # Step 5: Export results
        logger.info("Step 5: Exporting results...")
        exporter = DataExporter(config)
        output_path = exporter.export(aggregated_results, config.output.path)
        
        logger.info(f"Results exported to: {output_path}")
        
        # Generate summary
        summary = stats.finish()
        
        return {
            'success': True,
            'output_path': output_path,
            'total_rows': loaded_data.total_rows,
            'summary': summary
        }
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Validate arguments
    errors = validate_args(args)
    if errors:
        print("Error:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Build configuration
        config = build_config(args)
        
        # Run validation
        result = run_validation(config)
        
        if result['success']:
            print(f"\n✅ Validation complete!")
            print(f"   Processed: {result['total_rows']} numbers")
            print(f"   Valid: {result['summary']['valid']}")
            print(f"   Invalid: {result['summary']['invalid']}")
            print(f"   Output: {result['output_path']}")
            sys.exit(0)
        else:
            print("❌ Validation failed", file=sys.stderr)
            sys.exit(1)
            
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Invalid input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
