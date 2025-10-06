"""
Standardized Error Formatting for SDK Agent.

Provides consistent error message formatting across all modules
for better debugging and user experience.
"""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger("sdk_agent.error_formatter")


class ErrorFormatter:
    """Standardized error message formatter."""

    @staticmethod
    def format_error_message(
        error_type: str,
        component: str,
        details: str,
        context: Optional[Dict[str, Any]] = None,
        suggestions: Optional[list] = None
    ) -> str:
        """
        Format error message with consistent structure.

        Args:
            error_type: Type of error (e.g., "FileNotFound", "ValidationError")
            component: Component where error occurred (e.g., "batch_processor")
            details: Detailed error description
            context: Optional context information (e.g., file paths, parameters)
            suggestions: Optional list of suggestions to fix the error

        Returns:
            Formatted error message string

        Format:
            [ERROR_TYPE] component: details
            Context:
              - key: value
            Suggestions:
              - suggestion 1
              - suggestion 2
        """
        lines = [f"[{error_type}] {component}: {details}"]

        if context:
            lines.append("\nContext:")
            for key, value in context.items():
                lines.append(f"  - {key}: {value}")

        if suggestions:
            lines.append("\nSuggestions:")
            for suggestion in suggestions:
                lines.append(f"  - {suggestion}")

        return "\n".join(lines)

    @staticmethod
    def format_file_error(
        file_path: str,
        error: Exception,
        operation: str,
        suggestions: Optional[list] = None
    ) -> str:
        """
        Format file operation error.

        Args:
            file_path: Path to file that caused error
            error: The exception that occurred
            operation: Operation being performed (e.g., "read", "analyze")
            suggestions: Optional suggestions to fix the error

        Returns:
            Formatted error message
        """
        return ErrorFormatter.format_error_message(
            error_type=type(error).__name__,
            component="file_operation",
            details=f"Failed to {operation} file",
            context={
                "file_path": file_path,
                "error_message": str(error)
            },
            suggestions=suggestions or [
                "Check that the file exists and is readable",
                "Verify the file path is correct",
                "Ensure you have necessary permissions"
            ]
        )

    @staticmethod
    def format_validation_error(
        field_name: str,
        value: Any,
        expected: str,
        suggestions: Optional[list] = None
    ) -> str:
        """
        Format validation error.

        Args:
            field_name: Name of field that failed validation
            value: Actual value provided
            expected: Expected value or format
            suggestions: Optional suggestions to fix

        Returns:
            Formatted error message
        """
        return ErrorFormatter.format_error_message(
            error_type="ValidationError",
            component="validation",
            details=f"Invalid value for '{field_name}'",
            context={
                "field": field_name,
                "provided": value,
                "expected": expected
            },
            suggestions=suggestions
        )

    @staticmethod
    def format_configuration_error(
        parameter: str,
        value: Any,
        valid_range: str,
        suggestions: Optional[list] = None
    ) -> str:
        """
        Format configuration parameter error.

        Args:
            parameter: Parameter name
            value: Invalid value
            valid_range: Valid range or values
            suggestions: Optional suggestions

        Returns:
            Formatted error message
        """
        return ErrorFormatter.format_error_message(
            error_type="ConfigurationError",
            component="configuration",
            details=f"Invalid configuration parameter '{parameter}'",
            context={
                "parameter": parameter,
                "provided_value": value,
                "valid_range": valid_range
            },
            suggestions=suggestions or [
                f"Set '{parameter}' to a value within {valid_range}",
                "Check configuration documentation for valid values"
            ]
        )

    @staticmethod
    def format_processing_error(
        item: str,
        error: Exception,
        batch_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format batch processing error.

        Args:
            item: Item being processed (e.g., file path)
            error: Exception that occurred
            batch_info: Optional batch context (batch number, total, etc.)

        Returns:
            Formatted error message
        """
        context = {
            "item": item,
            "error_type": type(error).__name__,
            "error_message": str(error)
        }

        if batch_info:
            context.update(batch_info)

        return ErrorFormatter.format_error_message(
            error_type="ProcessingError",
            component="batch_processor",
            details=f"Failed to process item",
            context=context,
            suggestions=[
                "Check if the item exists and is accessible",
                "Verify the item format is correct",
                "Review logs for detailed error information"
            ]
        )


def log_structured_error(
    logger_obj: logging.Logger,
    error: Exception,
    component: str,
    context: Optional[Dict[str, Any]] = None,
    level: int = logging.ERROR
) -> None:
    """
    Log error with structured format.

    Args:
        logger_obj: Logger instance
        error: Exception to log
        component: Component where error occurred
        context: Optional context information
        level: Logging level (default: ERROR)
    """
    error_msg = ErrorFormatter.format_error_message(
        error_type=type(error).__name__,
        component=component,
        details=str(error),
        context=context
    )

    logger_obj.log(level, error_msg, exc_info=True)
