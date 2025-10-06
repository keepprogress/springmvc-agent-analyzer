"""
Validation Hook for SDK Agent Mode.

This hook validates tool inputs before execution to ensure security
and data integrity.

Hook Type: PreToolUse
Trigger: Before any tool is executed

Validations:
- File path security (path traversal prevention)
- File existence checks
- Input parameter validation
- Model selection based on confidence

Note: Hook decorators will be added in Phase 5 when SDK is integrated.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging

from sdk_agent.constants import (
    FILE_TYPE_CONTROLLER,
    MIN_CONFIDENCE_THRESHOLD,
    VALID_FILE_TYPES
)
from sdk_agent.utils import expand_file_path
from sdk_agent.exceptions import SDKAgentError

logger = logging.getLogger("sdk_agent.hooks.validation")


class ValidationHook:
    """
    Pre-tool validation hook.

    Validates inputs before tool execution to prevent security issues
    and ensure data quality.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize validation hook.

        Args:
            config: Hook configuration
        """
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.strict_mode = self.config.get("strict_mode", False)
        logger.info(f"ValidationHook initialized (enabled={self.enabled}, strict={self.strict_mode})")

    async def __call__(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate tool execution.

        Args:
            tool_name: Name of tool being called
            tool_input: Tool input parameters
            context: Execution context

        Returns:
            Validation result with optional permission decision
        """
        if not self.enabled:
            return {"allowed": True}

        logger.debug(f"Validating tool: {tool_name}")

        try:
            # Validate file paths in analysis tools
            if tool_name.startswith("analyze_"):
                result = self._validate_file_path(tool_input)
                if not result["allowed"]:
                    return result

            # Validate directory operations
            if tool_name == "analyze_directory":
                result = self._validate_directory_params(tool_input)
                if not result["allowed"]:
                    return result

            # Validate export operations
            if tool_name == "export_graph":
                result = self._validate_export_params(tool_input)
                if not result["allowed"]:
                    return result

            return {"allowed": True}

        except Exception as e:
            logger.error(f"Validation error for {tool_name}: {e}", exc_info=True)
            if self.strict_mode:
                return {
                    "allowed": False,
                    "reason": f"Validation error: {str(e)}"
                }
            return {"allowed": True}  # Allow in non-strict mode

    def _validate_file_path(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate file path security."""
        file_path = tool_input.get("file_path", "")

        if not file_path:
            return {
                "allowed": False,
                "reason": "file_path is required"
            }

        # Check for path traversal attempts
        dangerous_patterns = [
            "../", "..\\",
            "/etc/", "/sys/", "/root/", "/proc/",
            "C:\\Windows", "C:\\Program Files"
        ]

        for pattern in dangerous_patterns:
            if pattern in file_path:
                logger.warning(f"Path traversal attempt detected: {pattern} in {file_path}")
                return {
                    "allowed": False,
                    "reason": (
                        f"Security: Dangerous path pattern detected: {pattern}\n"
                        f"Path: {file_path}\n"
                        "Please use a safe file path within your workspace."
                    )
                }

        # Validate path can be expanded safely
        try:
            project_root = tool_input.get("project_root")
            expanded = expand_file_path(file_path, project_root)
            logger.debug(f"Path validated: {file_path} -> {expanded}")
        except SDKAgentError as e:
            logger.warning(f"Path validation failed: {e}")
            return {
                "allowed": False,
                "reason": f"Invalid file path: {str(e)}"
            }

        return {"allowed": True}

    def _validate_directory_params(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate directory analysis parameters."""
        directory_path = tool_input.get("directory_path", "")
        max_files = tool_input.get("max_files", 50)

        if not directory_path:
            return {
                "allowed": False,
                "reason": "directory_path is required"
            }

        # Check max_files limit
        if max_files > 100:
            logger.warning(f"max_files too large: {max_files}, limiting to 100")
            tool_input["max_files"] = 100

        return {"allowed": True}

    def _validate_export_params(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate graph export parameters."""
        output_path = tool_input.get("output_path", "")
        export_format = tool_input.get("format", "d3")

        if not output_path:
            return {
                "allowed": False,
                "reason": "output_path is required"
            }

        # Prevent overwriting system files
        system_paths = [
            "/etc/", "/sys/", "/root/", "/bin/", "/usr/",
            "C:\\Windows", "C:\\Program Files"
        ]

        for sys_path in system_paths:
            if output_path.startswith(sys_path):
                logger.warning(f"Attempt to write to system path: {output_path}")
                return {
                    "allowed": False,
                    "reason": f"Cannot write to system directory: {sys_path}"
                }

        return {"allowed": True}


# Create default instance
default_validation_hook = ValidationHook()
