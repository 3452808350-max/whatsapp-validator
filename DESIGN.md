# WhatsApp Number Validation Tool - 需求设计框架

## 📋 项目概述

基于用户提供的 README 和 requirements 文档，本项目实现了一个完整的 WhatsApp 号码验证工具。

---

## 1. 需求覆盖矩阵

### 1.1 功能需求 (FR)

| ID | 需求描述 | 实现状态 | 实现位置 |
|----|---------|---------|---------|
| FR-1 | CSV/Excel 输入支持 | ✅ | `data_loader.py` |
| FR-2 | 输入 schema 支持 (phone, name, country, source, notes) | ✅ | `data_loader.py` |
| FR-3 | 电话号码清洗和标准化 (E.164) | ✅ | `phone_validator.py` |
| FR-4 | 号码结构验证 (valid/invalid/unparseable) | ✅ | `phone_validator.py` |
| FR-5 | WhatsApp 可用性检查 (3种模式) | ✅ | `whatsapp_checker.py` |
| FR-6 | 批处理支持 | ✅ | 所有模块的 batch_* 方法 |
| FR-7 | CSV/Excel 输出生成 | ✅ | `data_exporter.py` |
| FR-8 | 错误处理 (不崩溃，保留错误详情) | ✅ | 全模块 try/except |
| FR-9 | 日志记录 (处理统计) | ✅ | `logger.py` |
| FR-10 | 可配置性 (路径、模式、重试等) | ✅ | `config.py` + CLI |

### 1.2 非功能需求 (NFR)

| ID | 需求描述 | 实现状态 | 说明 |
|----|---------|---------|------|
| NFR-1 | 简单性 | ✅ | 模块化设计，单一职责 |
| NFR-2 | 可靠性 | ✅ | 错误隔离，继续处理 |
| NFR-3 | 可扩展性 | ✅ | 支持数千行批处理 |
| NFR-4 | 可维护性 | ✅ | 清晰模块边界，类型提示 |
| NFR-5 | 透明性 | ✅ | 详细的错误信息和状态 |
| NFR-6 | 可复用性 | ✅ | 独立模块，API 可用 |

---

## 2. 系统架构

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI / API Entry                        │
│                      (cli.py / __main__.py)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Configuration Layer                      │
│              (config.py - YAML/Env/Defaults)                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Processing Pipeline                      │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  DataLoader  │───▶│PhoneValidator│───▶│WhatsAppChecker│ │
│  │              │    │              │    │               │  │
│  │ CSV/Excel    │    │ E.164 Format │    │ API/Mock/Est  │  │
│  │ Auto-detect  │    │ Valid/Invalid│    │ Rate Limiting │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                              │                    │         │
│                              ▼                    ▼         │
│                     ┌──────────────────────────────────┐   │
│                     │     ResultAggregator             │   │
│                     │  (合并验证结果和 WhatsApp 状态)   │   │
│                     └──────────────────────────────────┘   │
│                                         │                   │
│                                         ▼                   │
│                     ┌──────────────────────────────────┐   │
│                     │       DataExporter               │   │
│                     │    (CSV/Excel + Summary)         │   │
│                     └──────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Logging & Stats                        │
│              (logger.py - ProcessingStats)                  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 模块职责

| 模块 | 职责 | 关键类/函数 |
|-----|------|------------|
| `config.py` | 配置管理 | `Config`, `ConfigManager` |
| `logger.py` | 日志和统计 | `setup_logging()`, `ProcessingStats` |
| `data_loader.py` | 数据加载 | `DataLoader`, `LoadedData` |
| `phone_validator.py` | 号码验证 | `PhoneValidator`, `PhoneValidationResult` |
| `whatsapp_checker.py` | WhatsApp 检查 | `WhatsAppChecker`, `WhatsAppCheckResult` |
| `result_aggregator.py` | 结果聚合 | `ResultAggregator`, `AggregatedResult` |
| `data_exporter.py` | 数据导出 | `DataExporter` |
| `cli.py` | 命令行接口 | `main()`, `run_validation()` |

---

## 3. 数据流

### 3.1 输入 → 输出流程

```
Input File (CSV/Excel)
    │
    ├── 原始列: phone, name, country, source, notes
    │
    ▼
DataLoader.load()
    │
    ├── 自动检测 phone 列
    ├── 保留额外列
    └── 返回 DataFrame
    │
    ▼
PhoneValidator.batch_validate()
    │
    ├── 清洗: 移除空格、括号、横线
    ├── 标准化: E.164 格式
    └── 验证: valid/invalid/unparseable
    │
    ▼
WhatsAppChecker.batch_check()
    │
    ├── Mode: api / mock / estimated
    ├── Rate limiting
    └── 返回: yes/no/unknown
    │
    ▼
ResultAggregator.aggregate()
    │
    └── 合并所有结果
    │
    ▼
DataExporter.export()
    │
    ├── CSV 或 Excel 格式
    ├── 包含 Summary sheet (Excel)
    └── 自动调整列宽
    │
    ▼
Output File
    │
    ├── original_number
    ├── cleaned_number
    ├── e164_number
    ├── validity_status
    ├── whatsapp_status
    ├── country_code
    ├── error_message
    └── [原始额外列]
```

### 3.2 状态流转

```
Phone Number Input
       │
       ├──▶ Empty/None ────────▶ UNPARSEABLE
       │
       ├──▶ Clean Failed ──────▶ UNPARSEABLE
       │
       ├──▶ Parse Failed ──────▶ INVALID
       │
       └──▶ Parse Success ─────┬──▶ is_valid_number() == True ──▶ VALID
                               │
                               └──▶ is_valid_number() == False ─▶ INVALID
```

---

## 4. WhatsApp 检查模式

### 4.1 三种模式对比

| 模式 | 用途 | 实现 | 准确性 |
|-----|------|------|--------|
| **API** | 生产环境真实检查 | HTTP POST 到第三方 API | 高 |
| **Mock** | 开发和测试 | 基于号码末位数字模拟 | 低 |
| **Estimated** | 无 API 时的最佳估计 | 有效号码标记为 unknown | 中 |

### 4.2 API 模式配置

```yaml
whatsapp:
  mode: "api"
  api_endpoint: "https://api.example.com/v1/check"
  api_key: "your_api_key"
  timeout: 10
  retry_count: 3
  retry_delay: 1.0
```

### 4.3 Rate Limiting

```python
class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, requests_per_second: float, burst_limit: int):
        self.min_interval = 1.0 / requests_per_second
        ...
    
    def wait(self) -> None:
        """Wait if necessary to respect rate limits."""
        ...
```

---

## 5. 配置系统

### 5.1 配置优先级 (高 → 低)

1. **命令行参数** (CLI args)
2. **环境变量** (WA_VALIDATOR_*)
3. **配置文件** (config.yaml)
4. **默认值** (代码中定义)

### 5.2 配置示例

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
  mode: "mock"
  api_endpoint: ""
  api_key: ""

rate_limit:
  requests_per_second: 5.0
  burst_limit: 10

logging:
  level: "INFO"
  file: "logs/validator.log"
  console: true
```

### 5.3 环境变量映射

| 环境变量 | 配置路径 |
|---------|---------|
| WA_VALIDATOR_INPUT_PATH | input.path |
| WA_VALIDATOR_DEFAULT_COUNTRY | validation.default_country |
| WA_VALIDATOR_WHATSAPP_MODE | whatsapp.mode |
| WA_VALIDATOR_WHATSAPP_API_KEY | whatsapp.api_key |
| WA_VALIDATOR_LOG_LEVEL | logging.level |

---

## 6. 错误处理策略

### 6.1 错误分类

| 错误类型 | 处理方式 | 输出 |
|---------|---------|------|
| 文件不存在 | 抛出 FileNotFoundError | 终止程序 |
| 格式不支持 | 抛出 ValueError | 终止程序 |
| 解析失败 | 记录错误，继续处理 | 标记为 unparseable |
| 验证失败 | 记录错误，继续处理 | 标记为 invalid |
| API 失败 | 重试后标记为 unknown | 继续处理 |
| 编码问题 | 尝试多种编码 | 自动处理 |

### 6.2 错误输出示例

```csv
original_number,cleaned_number,e164_number,validity_status,whatsapp_status,error_message
123,123,+1123,invalid,no,Number is not a possible phone number
,,,unparseable,no,Empty or null phone number
+999999999,+999999999,,invalid,no,Invalid phone number format
```

---

## 7. 测试策略

### 7.1 测试覆盖

| 测试类别 | 文件 | 覆盖率 |
|---------|------|--------|
| 单元测试 | `tests/test_validator.py` | 核心模块 |
| 集成测试 | `validate.py` | 端到端流程 |
| 示例数据 | `data/sample_input.csv` | 真实场景 |

### 7.2 测试用例

```python
# 有效号码
test_valid_us_number: