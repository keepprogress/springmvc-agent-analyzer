"""
SDK Agent Permissions Module.

Fine-grained permission control for tool usage.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PermissionManager:
    """
    Manage tool usage permissions.

    Supports three modes:
    - acceptAll: Allow all tools automatically
    - acceptEdits: Allow read tools, confirm edit tools
    - rejectAll: Confirm all tools
    - custom: Use custom permission rules
    """

    def __init__(
        self,
        mode: str = "acceptEdits",
        custom_permissions: Optional[Dict[str, str]] = None
    ):
        """
        Initialize permission manager.

        Args:
            mode: Permission mode (acceptAll, acceptEdits, rejectAll, custom)
            custom_permissions: Custom permission rules (for custom mode)
        """
        self.mode = mode
        self.custom_permissions = custom_permissions or {}

        # Define read-only (safe) tools
        self.read_tools = {
            "analyze_controller",
            "analyze_service",
            "analyze_mapper",
            "analyze_jsp",
            "analyze_procedure",
            "query_graph",
            "find_dependencies",
            "analyze_impact",
            "list_files",
            "read_file",
        }

        # Define edit/write tools (require confirmation)
        self.edit_tools = {
            "build_graph",
            "export_graph",
        }

        logger.info(f"PermissionManager initialized with mode: {mode}")

    def can_use_tool(self, tool_name: str, **kwargs) -> str:
        """
        Check if tool can be used.

        Args:
            tool_name: Name of the tool
            **kwargs: Additional context

        Returns:
            Permission decision: "allow", "confirm", or "deny"
        """
        # Mode: acceptAll
        if self.mode == "acceptAll":
            logger.debug(f"Tool {tool_name}: ALLOW (acceptAll mode)")
            return "allow"

        # Mode: rejectAll
        if self.mode == "rejectAll":
            logger.debug(f"Tool {tool_name}: CONFIRM (rejectAll mode)")
            return "confirm"

        # Mode: acceptEdits
        if self.mode == "acceptEdits":
            if tool_name in self.read_tools:
                logger.debug(f"Tool {tool_name}: ALLOW (read tool)")
                return "allow"
            elif tool_name in self.edit_tools:
                logger.debug(f"Tool {tool_name}: CONFIRM (edit tool)")
                return "confirm"
            else:
                logger.warning(f"Unknown tool {tool_name}: defaulting to CONFIRM")
                return "confirm"

        # Mode: custom
        if self.mode == "custom":
            if tool_name in self.custom_permissions:
                decision = self.custom_permissions[tool_name]
                logger.debug(f"Tool {tool_name}: {decision.upper()} (custom rule)")
                return decision
            else:
                logger.debug(f"Tool {tool_name}: CONFIRM (no custom rule)")
                return "confirm"

        # Default: confirm
        logger.warning(f"Unknown permission mode {self.mode}: defaulting to CONFIRM")
        return "confirm"

    def set_mode(self, mode: str):
        """Set permission mode."""
        if mode not in ["acceptAll", "acceptEdits", "rejectAll", "custom"]:
            raise ValueError(f"Invalid permission mode: {mode}")

        self.mode = mode
        logger.info(f"Permission mode changed to: {mode}")

    def set_custom_permission(self, tool_name: str, permission: str):
        """
        Set custom permission for a tool.

        Args:
            tool_name: Name of the tool
            permission: Permission (allow, confirm, deny)
        """
        if permission not in ["allow", "confirm", "deny"]:
            raise ValueError(f"Invalid permission: {permission}")

        self.custom_permissions[tool_name] = permission
        logger.info(f"Custom permission set: {tool_name} = {permission}")

    def get_permissions_summary(self) -> Dict[str, Any]:
        """
        Get summary of current permissions.

        Returns:
            Permission summary
        """
        if self.mode == "custom":
            return {
                "mode": self.mode,
                "custom_permissions": self.custom_permissions
            }
        else:
            return {
                "mode": self.mode,
                "read_tools": list(self.read_tools),
                "edit_tools": list(self.edit_tools)
            }


def create_permission_manager(
    config: Dict[str, Any]
) -> PermissionManager:
    """
    Create permission manager from configuration.

    Args:
        config: SDK Agent configuration

    Returns:
        PermissionManager instance
    """
    mode = config.get("permission_mode", "acceptEdits")
    custom_permissions = config.get("permissions", {})

    return PermissionManager(
        mode=mode,
        custom_permissions=custom_permissions
    )
