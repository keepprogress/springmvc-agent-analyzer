# Error Handling Guide

Comprehensive guide for using the standardized error formatting system in SDK Agent mode.

## Overview

The SDK Agent uses a **standardized error formatting system** (`ErrorFormatter`) to provide consistent, informative error messages across all components. This improves debugging efficiency and provides clear guidance for resolving issues.

## Error Format Structure

All errors follow this consistent structure:

```
[ERROR_TYPE] component: details

Context:
  - key1: value1
  - key2: value2

Suggestions:
  - suggestion 1
  - suggestion 2
```

### Components

- **ERROR_TYPE**: The type/class of the error (e.g., `FileNotFoundError`, `ValidationError`)
- **component**: The module/component where the error occurred (e.g., `batch_processor`, `file_operation`)
- **details**: A clear description of what went wrong
- **Context** *(optional)*: Relevant contextual information (file paths, parameter values, etc.)
- **Suggestions** *(optional)*: Actionable steps to resolve the error

## Usage Examples

### 1. File Operation Errors

Use `format_file_error()` for file-related errors:

```python
from sdk_agent.error_formatter import ErrorFormatter

try:
    with open(file_path, 'r') as f:
        content = f.read()
except FileNotFoundError as e:
    error_msg = ErrorFormatter.format_file_error(
        file_path="example.java",
        error=e,
        operation="read",
        suggestions=[
            "Check if the file exists",
            "Verify the file path is correct"
        ]
    )
    raise SDKAgentError(error_msg)
```

**Output:**
```
[FileNotFoundError] file_operation: Failed to read file

Context:
  - file_path: example.java
  - error_message: [Errno 2] No such file or directory: 'example.java'

Suggestions:
  - Check if the file exists
  - Verify the file path is correct
```

### 2. Validation Errors

Use `format_validation_error()` for input validation errors:

```python
from sdk_agent.error_formatter import ErrorFormatter

def validate_batch_size(batch_size: int):
    if batch_size < 1:
        error_msg = ErrorFormatter.format_validation_error(
            field_name="batch_size",
            value=batch_size,
            expected="Must be >= 1",
            suggestions=[
                "Use a batch_size of at least 1",
                "Recommended: 10-50 for optimal performance"
            ]
        )
        raise ValueError(error_msg)
```

**Output:**
```
[ValidationError] validation: Invalid value for 'batch_size'

Context:
  - field: batch_size
  - provided: 0
  - expected: Must be >= 1

Suggestions:
  - Use a batch_size of at least 1
  - Recommended: 10-50 for optimal performance
```

### 3. Configuration Errors

Use `format_configuration_error()` for configuration parameter errors:

```python
from sdk_agent.error_formatter import ErrorFormatter

def validate_config(max_concurrency: int):
    if not (1 <= max_concurrency <= 100):
        error_msg = ErrorFormatter.format_configuration_error(
            parameter="max_concurrency",
            value=max_concurrency,
            valid_range="1-100",
            suggestions=[
                "Set max_concurrency between 1 and 100",
                "Recommended: 5-10 for optimal performance"
            ]
        )
        raise ValueError(error_msg)
```

**Output:**
```
[ConfigurationError] configuration: Invalid configuration parameter 'max_concurrency'

Context:
  - parameter: max_concurrency
  - provided_value: 200
  - valid_range: 1-100

Suggestions:
  - Set max_concurrency between 1 and 100
  - Recommended: 5-10 for optimal performance
```

### 4. Batch Processing Errors

Use `format_processing_error()` for errors during batch operations:

```python
from sdk_agent.error_formatter import ErrorFormatter

async def process_file(file_path: Path, batch_num: int, total_batches: int):
    try:
        # Process file...
        pass
    except Exception as e:
        error_msg = ErrorFormatter.format_processing_error(
            item=str(file_path),
            error=e,
            batch_info={
                "batch": batch_num,
                "total_batches": total_batches,
                "files_in_batch": 20
            }
        )
        return {"success": False, "error": error_msg}
```

**Output:**
```
[ProcessingError] batch_processor: Failed to process item

Context:
  - item: /path/to/file.java
  - error_type: ValueError
  - error_message: Invalid Java syntax
  - batch: 3
  - total_batches: 10
  - files_in_batch: 20

Suggestions:
  - Check if the item exists and is accessible
  - Verify the item format is correct
  - Review logs for detailed error information
```

### 5. Generic Error Messages

Use `format_error_message()` for custom error scenarios:

```python
from sdk_agent.error_formatter import ErrorFormatter

error_msg = ErrorFormatter.format_error_message(
    error_type="ConnectionError",
    component="api_client",
    details="Failed to connect to Anthropic API",
    context={
        "endpoint": "https://api.anthropic.com",
        "timeout": 30,
        "retries": 3
    },
    suggestions=[
        "Check your internet connection",
        "Verify your API key is valid",
        "Try increasing the timeout value"
    ]
)
```

### 6. Structured Logging

Use `log_structured_error()` for consistent error logging:

```python
from sdk_agent.error_formatter import log_structured_error
import logging

logger = logging.getLogger(__name__)

try:
    # Some operation...
    pass
except Exception as e:
    log_structured_error(
        logger_obj=logger,
        error=e,
        component="my_component",
        context={
            "operation": "analyze_file",
            "file_path": "example.java"
        },
        level=logging.ERROR  # Optional, defaults to ERROR
    )
    raise
```

## Advanced Features

### Context Truncation

Large context values are automatically truncated to prevent log spam:

- **Individual values** are truncated at **500 characters**
- **Total context** is truncated at **2000 characters**

```python
# Large context is automatically handled
error_msg = ErrorFormatter.format_error_message(
    error_type="DataError",
    component="data_processor",
    details="Failed to process large dataset",
    context={
        "data": "x" * 10000,  # Will be truncated to 500 chars + "... [truncated]"
        "rows": 1000000
    }
)
```

**Output:**
```
[DataError] data_processor: Failed to process large dataset

Context:
  - data: xxxxx... [truncated]
  - rows: 1000000
```

### Type Aliases

The module provides type aliases for better code clarity:

```python
from sdk_agent.error_formatter import ErrorContext, SuggestionList

def my_error_handler(
    context: ErrorContext,  # Dict[str, Any]
    suggestions: SuggestionList  # List[str]
) -> str:
    return ErrorFormatter.format_error_message(
        error_type="CustomError",
        component="my_component",
        details="Something went wrong",
        context=context,
        suggestions=suggestions
    )
```

## Best Practices

### 1. Always Provide Context

Include relevant information to help diagnose the issue:

```python
# ❌ Bad: No context
error_msg = ErrorFormatter.format_error_message(
    error_type="ProcessingError",
    component="processor",
    details="Failed to process"
)

# ✅ Good: With context
error_msg = ErrorFormatter.format_error_message(
    error_type="ProcessingError",
    component="processor",
    details="Failed to process file",
    context={
        "file_path": file_path,
        "file_size": file_size,
        "encoding": encoding
    }
)
```

### 2. Provide Actionable Suggestions

Suggestions should be concrete and actionable:

```python
# ❌ Bad: Vague suggestions
suggestions=["Fix the error", "Try again"]

# ✅ Good: Actionable suggestions
suggestions=[
    "Ensure the file exists at /path/to/file",
    "Check file permissions (should be readable)",
    "Verify the file encoding is UTF-8"
]
```

### 3. Use Appropriate Error Types

Choose the most specific error type:

```python
# ❌ Less specific
error_type="Error"

# ✅ More specific
error_type="FileNotFoundError"
error_type="ValidationError"
error_type="ConfigurationError"
```

### 4. Use Specialized Formatters

Use the specialized formatter methods when applicable:

```python
# ❌ Using generic formatter
error_msg = ErrorFormatter.format_error_message(
    error_type="FileNotFoundError",
    component="file_operation",
    details="File not found",
    context={"file": path}
)

# ✅ Using specialized formatter
error_msg = ErrorFormatter.format_file_error(
    file_path=path,
    error=FileNotFoundError("File not found"),
    operation="read"
)
```

### 5. Log Errors with Structure

Always use structured logging for consistency:

```python
# ❌ Basic logging
logger.error(f"Error in {component}: {str(error)}")

# ✅ Structured logging
log_structured_error(
    logger_obj=logger,
    error=error,
    component=component,
    context={"additional": "info"}
)
```

## Integration with Exceptions

### Custom Exception Classes

Integrate ErrorFormatter with custom exceptions:

```python
from sdk_agent.exceptions import SDKAgentError
from sdk_agent.error_formatter import ErrorFormatter

class BatchProcessingError(SDKAgentError):
    """Error during batch processing."""

    def __init__(self, item: str, original_error: Exception, batch_info: dict):
        error_msg = ErrorFormatter.format_processing_error(
            item=item,
            error=original_error,
            batch_info=batch_info
        )
        super().__init__(error_msg)
        self.item = item
        self.original_error = original_error
        self.batch_info = batch_info
```

### Error Recovery

Use formatted errors to guide recovery:

```python
from sdk_agent.error_formatter import ErrorFormatter

def process_with_recovery(file_path: str):
    try:
        return process_file(file_path)
    except FileNotFoundError as e:
        error_msg = ErrorFormatter.format_file_error(
            file_path=file_path,
            error=e,
            operation="process",
            suggestions=[
                "Check if the file was moved or deleted",
                "Try using an absolute path",
                "Verify the file still exists"
            ]
        )
        logger.error(error_msg)
        # Attempt recovery
        return handle_missing_file(file_path)
```

## Testing Error Messages

Test your error messages for clarity:

```python
def test_error_message_format():
    """Test that error messages are properly formatted."""
    error_msg = ErrorFormatter.format_validation_error(
        field_name="batch_size",
        value=0,
        expected="Must be >= 1"
    )

    # Check format
    assert "[ValidationError]" in error_msg
    assert "batch_size" in error_msg
    assert "Context:" in error_msg
    assert "provided: 0" in error_msg
    assert "expected: Must be >= 1" in error_msg
```

## API Reference

### ErrorFormatter Class

#### `format_error_message()`

Generic error formatter.

**Parameters:**
- `error_type: str` - Error type/class name
- `component: str` - Component where error occurred
- `details: str` - Error description
- `context: Optional[ErrorContext]` - Contextual information (default: None)
- `suggestions: Optional[SuggestionList]` - Fix suggestions (default: None)

**Returns:** `str` - Formatted error message

#### `format_file_error()`

Format file operation errors.

**Parameters:**
- `file_path: str` - Path to the file
- `error: Exception` - The exception that occurred
- `operation: str` - Operation being performed (e.g., "read", "write")
- `suggestions: Optional[SuggestionList]` - Custom suggestions (default: None)

**Returns:** `str` - Formatted error message

#### `format_validation_error()`

Format validation errors.

**Parameters:**
- `field_name: str` - Name of the field that failed validation
- `value: Any` - The invalid value provided
- `expected: str` - Description of expected value
- `suggestions: Optional[SuggestionList]` - Fix suggestions (default: None)

**Returns:** `str` - Formatted error message

#### `format_configuration_error()`

Format configuration parameter errors.

**Parameters:**
- `parameter: str` - Parameter name
- `value: Any` - Invalid value
- `valid_range: str` - Valid range or values description
- `suggestions: Optional[SuggestionList]` - Fix suggestions (default: None)

**Returns:** `str` - Formatted error message

#### `format_processing_error()`

Format batch processing errors.

**Parameters:**
- `item: str` - Item being processed
- `error: Exception` - The exception that occurred
- `batch_info: Optional[ErrorContext]` - Batch context info (default: None)

**Returns:** `str` - Formatted error message

### Helper Functions

#### `log_structured_error()`

Log errors with structured formatting.

**Parameters:**
- `logger_obj: logging.Logger` - Logger instance
- `error: Exception` - Exception to log
- `component: str` - Component where error occurred
- `context: Optional[ErrorContext]` - Contextual information (default: None)
- `level: int` - Logging level (default: logging.ERROR)

**Returns:** `None`

### Type Aliases

```python
ErrorContext = Dict[str, Any]      # Context dictionary
SuggestionList = List[str]         # List of suggestion strings
```

### Constants

```python
MAX_CONTEXT_VALUE_LENGTH = 500     # Max length for individual context values
MAX_TOTAL_CONTEXT_LENGTH = 2000    # Max total length for all context
```

## Troubleshooting

### Context Not Showing

Ensure context is a dictionary:

```python
# ❌ Wrong
context="some string"

# ✅ Correct
context={"key": "value"}
```

### Suggestions Not Showing

Ensure suggestions is a list:

```python
# ❌ Wrong
suggestions="Try this"

# ✅ Correct
suggestions=["Try this", "And this"]
```

### Truncated Context

If context is truncated, reduce the amount of data:

```python
# Instead of logging entire file content
context={"content": file_content}  # Might be too large

# Log summary information
context={
    "file_size": len(file_content),
    "first_100_chars": file_content[:100],
    "encoding": "utf-8"
}
```

## See Also

- [SDK Agent Documentation](../README.md)
- [Exception Handling](../sdk_agent/exceptions.py)
- [Logging Configuration](../sdk_agent/logging_config.py)
