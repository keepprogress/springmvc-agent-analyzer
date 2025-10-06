"""
Unit Tests for Error Formatter Module.

Tests standardized error message formatting for consistent
error reporting across all SDK Agent components.
"""

import pytest
from unittest.mock import Mock, patch, ANY
import logging

from sdk_agent.error_formatter import (
    ErrorFormatter,
    log_structured_error
)


class TestErrorFormatter:
    """Test ErrorFormatter class methods."""

    def test_format_error_message_basic(self):
        """Test basic error message formatting."""
        result = ErrorFormatter.format_error_message(
            error_type="TestError",
            component="test_component",
            details="Something went wrong"
        )

        assert "[TestError] test_component: Something went wrong" in result
        assert isinstance(result, str)

    def test_format_error_message_with_context(self):
        """Test error message with context information."""
        result = ErrorFormatter.format_error_message(
            error_type="FileError",
            component="file_processor",
            details="File processing failed",
            context={
                "file_path": "/path/to/file.java",
                "error_code": 404
            }
        )

        assert "[FileError]" in result
        assert "file_processor" in result
        assert "Context:" in result
        assert "file_path: /path/to/file.java" in result
        assert "error_code: 404" in result

    def test_format_error_message_with_suggestions(self):
        """Test error message with suggestions."""
        result = ErrorFormatter.format_error_message(
            error_type="ValidationError",
            component="validator",
            details="Invalid input",
            suggestions=[
                "Check input format",
                "Verify data types",
                "Read documentation"
            ]
        )

        assert "Suggestions:" in result
        assert "Check input format" in result
        assert "Verify data types" in result
        assert "Read documentation" in result

    def test_format_error_message_complete(self):
        """Test error message with all fields."""
        result = ErrorFormatter.format_error_message(
            error_type="CompleteError",
            component="test_module",
            details="Full error test",
            context={"key": "value"},
            suggestions=["Fix it", "Try again"]
        )

        # All sections should be present
        assert "[CompleteError]" in result
        assert "test_module" in result
        assert "Full error test" in result
        assert "Context:" in result
        assert "key: value" in result
        assert "Suggestions:" in result
        assert "Fix it" in result
        assert "Try again" in result


class TestFileErrorFormatting:
    """Test file-specific error formatting."""

    def test_format_file_error_basic(self):
        """Test basic file error formatting."""
        error = FileNotFoundError("File does not exist")

        result = ErrorFormatter.format_file_error(
            file_path="/path/to/missing.java",
            error=error,
            operation="read"
        )

        assert "FileNotFoundError" in result
        assert "/path/to/missing.java" in result
        assert "Failed to read file" in result
        assert "Suggestions:" in result

    def test_format_file_error_with_custom_suggestions(self):
        """Test file error with custom suggestions."""
        error = PermissionError("Access denied")

        result = ErrorFormatter.format_file_error(
            file_path="/restricted/file.java",
            error=error,
            operation="write",
            suggestions=[
                "Check file permissions",
                "Run as administrator"
            ]
        )

        assert "PermissionError" in result
        assert "/restricted/file.java" in result
        assert "Check file permissions" in result
        assert "Run as administrator" in result

    def test_format_file_error_default_suggestions(self):
        """Test that default suggestions are provided."""
        error = IOError("I/O error")

        result = ErrorFormatter.format_file_error(
            file_path="/some/file.java",
            error=error,
            operation="analyze"
        )

        # Default suggestions should be present
        assert "Check that the file exists" in result
        assert "Verify the file path is correct" in result
        assert "Ensure you have necessary permissions" in result


class TestValidationErrorFormatting:
    """Test validation error formatting."""

    def test_format_validation_error(self):
        """Test validation error formatting."""
        result = ErrorFormatter.format_validation_error(
            field_name="batch_size",
            value=0,
            expected="Must be >= 1"
        )

        assert "ValidationError" in result
        assert "batch_size" in result
        assert "provided: 0" in result
        assert "expected: Must be >= 1" in result

    def test_format_validation_error_with_suggestions(self):
        """Test validation error with custom suggestions."""
        result = ErrorFormatter.format_validation_error(
            field_name="max_concurrency",
            value=-5,
            expected="1-50",
            suggestions=[
                "Use a value between 1 and 50",
                "Recommended: 5-10 for optimal performance"
            ]
        )

        assert "max_concurrency" in result
        assert "provided: -5" in result
        assert "expected: 1-50" in result
        assert "Use a value between 1 and 50" in result
        assert "Recommended: 5-10" in result


class TestConfigurationErrorFormatting:
    """Test configuration error formatting."""

    def test_format_configuration_error(self):
        """Test configuration error formatting."""
        result = ErrorFormatter.format_configuration_error(
            parameter="timeout",
            value=-1,
            valid_range="0-3600"
        )

        assert "ConfigurationError" in result
        assert "timeout" in result
        assert "provided_value: -1" in result
        assert "valid_range: 0-3600" in result

    def test_format_configuration_error_with_suggestions(self):
        """Test configuration error with custom suggestions."""
        result = ErrorFormatter.format_configuration_error(
            parameter="cache_size",
            value=999999,
            valid_range="1-10000",
            suggestions=[
                "Reduce cache_size to a reasonable value",
                "Consider system memory limits"
            ]
        )

        assert "cache_size" in result
        assert "Reduce cache_size" in result
        assert "Consider system memory limits" in result


class TestProcessingErrorFormatting:
    """Test batch processing error formatting."""

    def test_format_processing_error(self):
        """Test processing error formatting."""
        error = ValueError("Invalid data format")

        result = ErrorFormatter.format_processing_error(
            item="/path/to/file.java",
            error=error
        )

        assert "ProcessingError" in result
        assert "/path/to/file.java" in result
        assert "ValueError" in result
        assert "Invalid data format" in result

    def test_format_processing_error_with_batch_info(self):
        """Test processing error with batch context."""
        error = RuntimeError("Processing failed")

        result = ErrorFormatter.format_processing_error(
            item="/path/to/file.java",
            error=error,
            batch_info={
                "batch": 3,
                "total_batches": 10,
                "files_in_batch": 20
            }
        )

        assert "ProcessingError" in result
        assert "/path/to/file.java" in result
        assert "RuntimeError" in result
        assert "batch: 3" in result
        assert "total_batches: 10" in result
        assert "files_in_batch: 20" in result


class TestStructuredLogging:
    """Test structured error logging functionality."""

    @patch('sdk_agent.error_formatter.ErrorFormatter.format_error_message')
    def test_log_structured_error(self, mock_format):
        """Test structured error logging."""
        mock_format.return_value = "Formatted error message"

        logger = Mock(spec=logging.Logger)
        error = ValueError("Test error")
        context = {"key": "value"}

        log_structured_error(
            logger_obj=logger,
            error=error,
            component="test_component",
            context=context,
            level=logging.ERROR
        )

        # Verify formatter was called with correct arguments
        mock_format.assert_called_once_with(
            error_type="ValueError",
            component="test_component",
            details="Test error",
            context=context
        )

        # Verify logger was called
        logger.log.assert_called_once_with(
            logging.ERROR,
            "Formatted error message",
            exc_info=True
        )

    def test_log_structured_error_different_levels(self):
        """Test logging at different levels."""
        logger = Mock(spec=logging.Logger)
        error = Warning("Warning message")

        # Test with WARNING level
        log_structured_error(
            logger_obj=logger,
            error=error,
            component="test",
            level=logging.WARNING
        )

        logger.log.assert_called_with(
            logging.WARNING,
            ANY,
            exc_info=True
        )


class TestErrorMessageConsistency:
    """Test consistency of error message formats."""

    def test_all_error_types_include_type_marker(self):
        """Test that all error types include the error type marker."""
        # Test each formatting method
        file_error = ErrorFormatter.format_file_error(
            "test.java",
            FileNotFoundError("not found"),
            "read"
        )
        assert file_error.startswith("[FileNotFoundError]")

        validation_error = ErrorFormatter.format_validation_error(
            "field", "value", "expected"
        )
        assert validation_error.startswith("[ValidationError]")

        config_error = ErrorFormatter.format_configuration_error(
            "param", "value", "range"
        )
        assert config_error.startswith("[ConfigurationError]")

        processing_error = ErrorFormatter.format_processing_error(
            "item", ValueError("error")
        )
        assert processing_error.startswith("[ProcessingError]")

    def test_consistent_structure(self):
        """Test that all errors have consistent structure."""
        errors = [
            ErrorFormatter.format_file_error(
                "test.java", IOError("error"), "read"
            ),
            ErrorFormatter.format_validation_error(
                "field", "value", "expected"
            ),
            ErrorFormatter.format_configuration_error(
                "param", "value", "range"
            ),
            ErrorFormatter.format_processing_error(
                "item", ValueError("error")
            )
        ]

        for error_msg in errors:
            # All should have error type marker
            assert error_msg.startswith("[")
            assert "]" in error_msg

            # All should have context or suggestions
            assert "Context:" in error_msg or "Suggestions:" in error_msg


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_context(self):
        """Test error formatting with empty context."""
        result = ErrorFormatter.format_error_message(
            error_type="TestError",
            component="test",
            details="Test",
            context={}
        )

        # Should not include Context section if empty
        assert "[TestError]" in result
        assert "test" in result

    def test_empty_suggestions(self):
        """Test error formatting with empty suggestions."""
        result = ErrorFormatter.format_error_message(
            error_type="TestError",
            component="test",
            details="Test",
            suggestions=[]
        )

        # Should not include Suggestions section if empty
        assert "[TestError]" in result
        assert "test" in result

    def test_none_context_and_suggestions(self):
        """Test error formatting with None context and suggestions."""
        result = ErrorFormatter.format_error_message(
            error_type="TestError",
            component="test",
            details="Test",
            context=None,
            suggestions=None
        )

        # Should handle None gracefully
        assert "[TestError] test: Test" in result

    def test_complex_context_values(self):
        """Test error formatting with complex context values."""
        result = ErrorFormatter.format_error_message(
            error_type="TestError",
            component="test",
            details="Test",
            context={
                "list_value": [1, 2, 3],
                "dict_value": {"nested": "data"},
                "none_value": None
            }
        )

        assert "list_value:" in result
        assert "dict_value:" in result
        assert "none_value:" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
