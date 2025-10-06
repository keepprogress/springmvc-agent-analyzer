"""
Common utilities for SDK Agent tools.

Provides shared validation, path handling, and formatting functions
to reduce code duplication across tool modules.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging

from sdk_agent.utils import expand_file_path
from sdk_agent.exceptions import SDKAgentError
from sdk_agent.error_formatter import ErrorFormatter, log_structured_error

logger = logging.getLogger("sdk_agent.tools.common")


def validate_and_expand_path(
    file_path: str,
    project_root: Optional[str] = None,
    must_exist: bool = True
) -> Path:
    """
    Common path validation and expansion for all tools.

    Args:
        file_path: Path to validate and expand
        project_root: Optional project root for relative path resolution
        must_exist: If True, raise error if file doesn't exist

    Returns:
        Expanded and validated Path object

    Raises:
        SDKAgentError: If file not found (when must_exist=True)

    Security:
        - Validates against path traversal attempts
        - Normalizes paths to prevent directory escaping
        - Checks file existence if required
    """
    try:
        # Expand path (handles relative paths, ~, etc.)
        if project_root:
            project_root_path = Path(project_root).resolve()
        else:
            project_root_path = Path.cwd()

        full_path = expand_file_path(file_path, project_root_path)

        # Validate existence if required
        if must_exist and not full_path.exists():
            error_msg = ErrorFormatter.format_file_error(
                file_path=file_path,
                error=FileNotFoundError(f"File does not exist: {full_path}"),
                operation="access",
                suggestions=[
                    "Check that the file exists at the specified path",
                    f"Resolved path: {full_path}",
                    f"Project root: {project_root_path}",
                    "Verify file permissions and accessibility"
                ]
            )
            raise SDKAgentError(error_msg)

        # Ensure path is within project root (security check)
        try:
            full_path.relative_to(project_root_path)
        except ValueError:
            # Path is outside project root - potential security issue
            error_msg = ErrorFormatter.format_error_message(
                error_type="SecurityWarning",
                component="path_validation",
                details="Path is outside project root",
                context={
                    "requested_path": file_path,
                    "resolved_path": str(full_path),
                    "project_root": str(project_root_path)
                },
                suggestions=[
                    "Ensure paths stay within project boundaries",
                    "Avoid using '..' to traverse directories",
                    "Use absolute paths within the project"
                ]
            )
            logger.warning(error_msg)

        return full_path

    except Exception as e:
        if isinstance(e, SDKAgentError):
            raise
        error_msg = ErrorFormatter.format_error_message(
            error_type="PathValidationError",
            component="path_validation",
            details="Path validation failed",
            context={
                "file_path": file_path,
                "error": str(e)
            }
        )
        raise SDKAgentError(error_msg)


def validate_tool_args(
    args: Dict[str, Any],
    required_fields: list,
    optional_fields: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate tool arguments with type checking and defaults.

    Args:
        args: Input arguments to validate
        required_fields: List of required field names
        optional_fields: Dict of {field_name: default_value}

    Returns:
        Validated and normalized arguments

    Raises:
        SDKAgentError: If required fields missing or validation fails
    """
    # Check required fields
    missing = [field for field in required_fields if field not in args]
    if missing:
        error_msg = ErrorFormatter.format_validation_error(
            field_name=", ".join(missing),
            value=list(args.keys()),
            expected=f"Required fields: {required_fields}",
            suggestions=[
                f"Add missing field(s): {', '.join(missing)}",
                "Check tool documentation for required parameters",
                f"Current fields provided: {list(args.keys())}"
            ]
        )
        raise SDKAgentError(error_msg)

    # Add optional fields with defaults
    if optional_fields:
        for field, default in optional_fields.items():
            if field not in args:
                args[field] = default

    return args


def format_analysis_summary(
    analysis: Dict[str, Any],
    file_type: str,
    include_details: bool = True
) -> str:
    """
    Format analysis results into human-readable summary.

    Args:
        analysis: Analysis result dictionary
        file_type: Type of file analyzed (controller, service, etc.)
        include_details: Include detailed information

    Returns:
        Formatted summary string
    """
    if file_type == "controller":
        return _format_controller_summary(analysis, include_details)
    elif file_type == "service":
        return _format_service_summary(analysis, include_details)
    elif file_type == "jsp":
        return _format_jsp_summary(analysis, include_details)
    elif file_type == "mapper":
        return _format_mapper_summary(analysis, include_details)
    elif file_type == "procedure":
        return _format_procedure_summary(analysis, include_details)
    else:
        return _format_generic_summary(analysis, include_details)


def _format_controller_summary(
    analysis: Dict[str, Any],
    include_details: bool
) -> str:
    """Format Controller analysis summary."""
    class_name = analysis.get("class_name", "Unknown")
    package = analysis.get("package", "N/A")
    base_url = analysis.get("base_url", "N/A")
    methods = analysis.get("methods", [])
    dependencies = analysis.get("dependencies", [])

    summary = f"""Controller Analysis: {class_name}
{'=' * 60}
Package: {package}
Base URL: {base_url}
Methods: {len(methods)}
Dependencies: {len(dependencies)}
"""

    if include_details and methods:
        summary += "\nEndpoints:\n"
        for method in methods:
            method_name = method.get("name", "unknown")
            http_method = method.get("http_method", "GET")
            url = method.get("url", "N/A")
            summary += f"  • {http_method} {url} → {method_name}()\n"

    return summary.strip()


def _format_service_summary(
    analysis: Dict[str, Any],
    include_details: bool
) -> str:
    """Format Service analysis summary."""
    class_name = analysis.get("class_name", "Unknown")
    package = analysis.get("package", "N/A")
    methods = analysis.get("methods", [])
    transactional = analysis.get("transactional_methods", [])

    summary = f"""Service Analysis: {class_name}
{'=' * 60}
Package: {package}
Methods: {len(methods)}
Transactional: {len(transactional)}
"""

    if include_details and transactional:
        summary += "\nTransactional Methods:\n"
        for method in transactional:
            summary += f"  • {method}\n"

    return summary.strip()


def _format_jsp_summary(
    analysis: Dict[str, Any],
    include_details: bool
) -> str:
    """Format JSP analysis summary."""
    file_name = analysis.get("file_name", "Unknown")
    includes = analysis.get("includes", [])
    forms = analysis.get("forms", [])
    ajax_calls = analysis.get("ajax_calls", [])

    summary = f"""JSP Analysis: {file_name}
{'=' * 60}
Includes: {len(includes)}
Forms: {len(forms)}
AJAX Calls: {len(ajax_calls)}
"""

    if include_details and includes:
        summary += "\nIncludes:\n"
        for inc in includes[:5]:  # Limit to first 5
            summary += f"  • {inc}\n"

    return summary.strip()


def _format_mapper_summary(
    analysis: Dict[str, Any],
    include_details: bool
) -> str:
    """Format Mapper analysis summary."""
    namespace = analysis.get("namespace", "Unknown")
    statements = analysis.get("statements", [])
    result_maps = analysis.get("result_maps", [])

    summary = f"""Mapper Analysis: {namespace}
{'=' * 60}
Statements: {len(statements)}
Result Maps: {len(result_maps)}
"""

    if include_details and statements:
        summary += "\nStatements:\n"
        for stmt in statements[:10]:  # Limit to first 10
            stmt_id = stmt.get("id", "unknown")
            stmt_type = stmt.get("type", "unknown")
            summary += f"  • {stmt_type}: {stmt_id}\n"

    return summary.strip()


def _format_procedure_summary(
    analysis: Dict[str, Any],
    include_details: bool
) -> str:
    """Format Procedure analysis summary."""
    proc_name = analysis.get("procedure_name", "Unknown")
    parameters = analysis.get("parameters", [])
    calls = analysis.get("calls", [])

    summary = f"""Procedure Analysis: {proc_name}
{'=' * 60}
Parameters: {len(parameters)}
Calls: {len(calls)}
"""

    if include_details and parameters:
        summary += "\nParameters:\n"
        for param in parameters:
            param_name = param.get("name", "unknown")
            param_type = param.get("type", "unknown")
            param_mode = param.get("mode", "IN")
            summary += f"  • {param_mode} {param_name} {param_type}\n"

    return summary.strip()


def _format_generic_summary(
    analysis: Dict[str, Any],
    include_details: bool
) -> str:
    """Format generic analysis summary."""
    return f"""Analysis Complete
{'=' * 60}
Results: {len(analysis)} fields
{analysis}
"""


def handle_analysis_error(
    error: Exception,
    file_path: str,
    tool_name: str
) -> Dict[str, Any]:
    """
    Handle analysis errors consistently across tools.

    Args:
        error: The exception that occurred
        file_path: Path to file being analyzed
        tool_name: Name of the tool that failed

    Returns:
        Formatted error response
    """
    # Use standardized error formatter
    error_message = ErrorFormatter.format_error_message(
        error_type=type(error).__name__,
        component=tool_name,
        details=str(error),
        context={
            "file_path": file_path,
            "error_type": type(error).__name__
        },
        suggestions=[
            "Check that the file exists and is readable",
            "Verify the file is the correct type for this tool",
            "Check logs for detailed error information"
        ]
    )

    # Use structured logging
    log_structured_error(
        logger,
        error,
        component=tool_name,
        context={"file_path": file_path}
    )

    return {
        "content": [{
            "type": "text",
            "text": error_message
        }],
        "is_error": True,
        "error": str(error)
    }
