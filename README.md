# WhatsApp Number Validation Tool

A practical data-processing tool to clean, validate, and check phone numbers for potential WhatsApp availability.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Testing](#testing)
- [Architecture](#architecture)

## ✨ Features

- ✅ **Multi-format support**: CSV and Excel input/output
- ✅ **Smart cleaning**: Removes separators, normalizes formats
- ✅ **E.164 conversion**: International standard phone format
- ✅ **Structural validation**: Uses Google's `phonenumbers` library
- ✅ **WhatsApp check**: Three modes (API, mock, estimated)
- ✅ **Batch processing**: Handles thousands of numbers efficiently
- ✅ **Robust error handling**: Never crashes on bad data
- ✅ **Detailed logging**: Track processing stats and errors
- ✅ **Configurable**: YAML config + CLI options + env vars

## 🚀 Quick Start

```bash
# Install
pip install -r requirements.txt

# Basic usage
python __main__.py input.csv output.csv

# Or using the CLI
wa-validator input.csv output.csv --country US
```

## 📦 Installation

### Requirements

- Python 3.8 or higher
- pip package manager

### Install Dependencies

```bash
pip install -r requirements.txt
```

Dependencies:
- `pandas` - Data processing
- `phonenumbers` - Phone number parsing and validation
- `openpyxl` - Excel file handling
- `requests` - API calls
- `python-dotenv` - Environment variable management
- `pyyaml` - YAML configuration (usually included with Python)

### Optional: Install as Package

```bash
pip install -e .
```

## 💻 Usage

### Command Line Interface

```bash
# Basic validation
python __main__.py input.csv output.csv

# Specify country code
python __main__.py input.csv output.csv --country CN

# Use API mode for WhatsApp check
python __main__.py input.csv output.csv --mode api --api-endpoint https://api.example.com/check --api-key YOUR_KEY

# Excel input/output
python __main__.py input.xlsx output.xlsx --output-format xlsx

# Use configuration file
python __main__.py --config config.yaml

# Advanced options
python __main__.py input.csv output.csv \
  --country US \
  --mode mock \
  --rate-limit 10 \
  --retry-count 5 \
  --log-level DEBUG \
  --log-file logs/validation.log
```

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `input` | Input file path | Required |
| `output` | Output file path | Required |
| `-c, --config` | YAML configuration file | None |
| `--country` | Default country code | US |
| `--mode` | WhatsApp check mode (api/mock/estimated) | mock |
| `--api-endpoint` | API endpoint for WhatsApp check | None |
| `--api-key` | API key for authentication | None |
| `--rate-limit` | API requests per second | 5.0 |
| `--retry-count` | Number of retries for API failures | 3 |
| `--log-level` | Logging level | INFO |
| `--log-file` | Log file path | None |
| `--quiet` | Suppress console output | False |

### Python API

```python
from src import Config, PhoneValidator, WhatsAppChecker, DataLoader, DataExporter

# Create configuration
config = Config()
config.validation.default_country = "US"
config.whatsapp.mode = "mock"

# Validate phone number
validator = PhoneValidator(config)
result = validator.validate("+1 415-555-1234")

print(f"Valid: {result.validity_status}")
print(f"E164: {result.e164_number}")

# Batch validation
numbers = ["+14155551234", "+8618823880046", "invalid"]
results = validator.batch_validate(numbers)

# WhatsApp check
checker = WhatsAppChecker(config)
wa_result = checker.check("+14155551234")
print(f"WhatsApp: {wa_result.status}")
```

## ⚙️ Configuration

### YAML Configuration

Create `config.yaml`:

```yaml
input:
  path: "data/input.csv"
  format: "csv"
  phone_column: "phone"

output:
  path: "data/output.csv"
  format: "csv"

validation:
  default_country: "US"
  strict_mode: false

whatsapp:
  mode: "mock"  # api, mock, or estimated
  api_endpoint: ""
  api_key: ""
  timeout: 10
  retry_count: 3
  retry_delay: 1

rate_limit:
  requests_per_second: 5
  burst_limit: 10

logging:
  level: "INFO"
  file: "logs/validator.log"
  console: true
```

### Environment Variables

Override settings with environment variables:

```bash
export WA_VALIDATOR_INPUT_PATH="data/my_numbers.csv"
export WA_VALIDATOR_OUTPUT_PATH="data/results.csv"
export WA_VALIDATOR_DEFAULT_COUNTRY="CN"
export WA_VALIDATOR_WHATSAPP_MODE="api"
export WA_VALIDATOR_WHATSAPP_API_KEY="your_api_key"
export WA_VALIDATOR_LOG_LEVEL="DEBUG"
```

## 📖 API Reference

### PhoneValidator

```python
from src import PhoneValidator, Config

config = Config()
validator = PhoneValidator(config)

# Single validation
result = validator.validate("+1 415-555-1234")

# Result attributes:
# - original_number: str
# - cleaned_number: Optional[str]
# - e164_number: Optional[str]
# - country_code: Optional[str]
# - parse_status: ParseStatus (success, invalid_format, etc.)
# - validity_status: ValidityStatus (valid, invalid, unparseable)
# - error_message: Optional[str]
```

### WhatsAppChecker

```python
from src import WhatsAppChecker, Config

config = Config()
config.whatsapp.mode = "mock"
checker = WhatsAppChecker(config)

# Single check
result = checker.check("+14155551234")

# Result attributes:
# - phone_number: str
# - status: WhatsAppStatus (yes, no, unknown)
# - source: str (api, mock, estimated)
# - error_message: Optional[str]
```

### DataLoader

```python
from src import DataLoader, Config

config = Config()
config.input.path = "input.csv"
loader = DataLoader(config)

# Load data
data = loader.load()

# Data attributes:
# - df: pandas DataFrame
# - phone_column: str
# - total_rows: int
# - extra_columns: List[str]
```

## 📝 Examples

### Input Format

**CSV:**
```csv
phone,name,country
+1 415-555-1234,John,US
18823880046,Jane,CN
0755-12345678,Bob,CN
```

**Excel:**
Same structure as CSV, saved as .xlsx

### Output Format

**CSV:**
```csv
original_number,cleaned_number,e164_number,validity_status,whatsapp_status,country_code,parse_status,error_message
+1 415-555-1234,+14155551234,+14155551234,valid,no,+1,success,
18823880046,18823880046,+18823880046,invalid,no,+1,invalid_format,Number is possible but not valid (incorrect length or format)
,,,unparseable,unknown,,empty,Empty or null phone number
```

### Processing Pipeline

```python
from src import (
    Config, PhoneValidator, WhatsAppChecker,
    DataLoader, ResultAggregator, DataExporter,
    setup_logging, ProcessingStats
)

# Setup
config = Config()
logger = setup_logging(level="INFO")
stats = ProcessingStats(logger)

# Step 1: Load data
loader = DataLoader(config)
data = loader.load()
stats.start(data.total_rows)

# Step 2: Validate phone numbers
validator = PhoneValidator(config)
phone_results = validator.batch_validate(
    data.df[data.phone_column].tolist()
)

# Step 3: Check WhatsApp
checker = WhatsAppChecker(config, stats)
wa_results = checker.batch_check(
    [r.e164_number for r in phone_results]
)

# Step 4: Aggregate results
aggregator = ResultAggregator(stats)
aggregated = aggregator.aggregate(phone_results, wa_results)

# Step 5: Export
exporter = DataExporter(config)
output_path = exporter.export(aggregated, config.output.path)

# Summary
summary = stats.finish()
```

## 🧪 Testing

### Run All Tests

```bash
.venv/bin/python -m pytest -q tests test_quick.py test_comprehensive.py
```

### Run Specific Tests

```bash
.venv/bin/python -m pytest tests/test_validator.py::TestPhoneValidator -v
```

### Test Coverage

```bash
.venv/bin/python -m pytest tests/ --cov=src --cov-report=html
```

## 🏗 Architecture

### Project Structure

```
whatsapp-validator/
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── logger.py          # Logging and stats
│   ├── data_loader.py     # CSV/Excel loading
│   ├── phone_validator.py # Phone number validation
│   ├── whatsapp_checker.py# WhatsApp availability check
│   ├── result_aggregator.py# Result aggregation
│   ├── data_exporter.py   # CSV/Excel export
│   ├── cli.py             # Command-line interface
│   └── main.py            # Entry point
├── tests/
│   ├── conftest.py        # pytest configuration
│   └── test_validator.py  # Test cases
├── config.example.yaml    # Example configuration
├── requirements.txt       # Dependencies
├── README.md              # Documentation
└── LICENSE                # MIT License
```

### Data Flow

```
Input File (CSV/Excel)
        ↓
    DataLoader
        ↓
    PhoneValidator
        ↓
    WhatsAppChecker
        ↓
    ResultAggregator
        ↓
    DataExporter
        ↓
Output File (CSV/Excel)
```

### Core Modules

| Module | Responsibility |
|--------|---------------|
| `config.py` | Configuration management (YAML + env vars) |
| `logger.py` | Logging setup and processing statistics |
| `data_loader.py` | Load CSV/Excel files, auto-detect columns |
| `phone_validator.py` | Clean, normalize, validate phone numbers |
| `whatsapp_checker.py` | Check WhatsApp availability (3 modes) |
| `result_aggregator.py` | Combine validation + WhatsApp results |
| `data_exporter.py` | Export to CSV/Excel with formatting |
| `cli.py` | Command-line interface |

## 🔧 WhatsApp Check Modes

### Mode A: API (True Lookup)

Requires a third-party API that can check WhatsApp registration.

```yaml
whatsapp:
  mode: api
  api_endpoint: https://api.example.com/check
  api_key: your_api_key
```

### Mode B: Mock (Development)

Returns mock results based on phone number patterns. Useful for testing.

```yaml
whatsapp:
  mode: mock
```

### Mode C: Estimated (Best Guess)

No actual check - estimates based on phone validity.

```yaml
whatsapp:
  mode: estimated
```

## 📊 Requirements Coverage

| Requirement | Status |
|------------|--------|
| FR-1: CSV/Excel input | ✅ |
| FR-2: Input schema | ✅ |
| FR-3: Phone cleaning | ✅ |
| FR-4: Number validation | ✅ |
| FR-5: WhatsApp check | ✅ (3 modes) |
| FR-6: Batch processing | ✅ |
| FR-7: Output generation | ✅ |
| FR-8: Error handling | ✅ |
| FR-9: Logging | ✅ |
| FR-10: Configurability | ✅ |
| NFR-1: Simplicity | ✅ |
| NFR-2: Reliability | ✅ |
| NFR-3: Scalability | ✅ |
| NFR-4: Maintainability | ✅ |
| NFR-5: Transparency | ✅ |
| NFR-6: Reusability | ✅ |

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📞 Support

For issues and questions:
- Create an issue in the repository
- Check the documentation in README.md
