"""
SDK Agent Permissions Module.

Fine-grained permission control for tool usage with audit logging.
"""

from typing import Dict, Any, Optional
import logging

from sdk_agent.constants import (
    PERMISSION_MODE_ACCEPT_ALL,
    PERMISSION_MODE_ACCEPT_EDITS,
    PERMISSION_MODE_REJECT_ALL,
    PERMISSION_MODE_CUSTOM,
    VALID_PERMISSION_MODES,
    PERMISSION_ALLOW,
    PERMISSION_CONFIRM,
    PERMISSION_DENY,
    VALID_PERMISSION_DECISIONS,
    READ_ONLY_TOOLS,
    EDIT_TOOLS,
)

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
        mode: str = PERMISSION_MODE_ACCEPT_EDITS,
        custom_permissions: Optional[Dict[str, str]] = None
    ):
        """
        Initialize permission manager with audit logging.

        Args:
            mode: Permission mode (acceptAll, acceptEdits, rejectAll, custom)
            custom_permissions: Custom permission rules (for custom mode)

        Raises:
            ValueError: If mode is invalid
        """
        if mode not in VALID_PERMISSION_MODES:
            raise ValueError(
                f"Invalid permission mode: {mode}. "
                f"Must be one of {VALID_PERMISSION_MODES}"
            )

        self.mode = mode
        self.custom_permissions = custom_permissions or {}

        # Use constants for tool categories
        self.read_tools = READ_ONLY_TOOLS
        self.edit_tools = EDIT_TOOLS

        logger.info(f"PermissionManager initialized with mode: {mode}")

    def can_use_tool(
        self,
        tool_name: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Check if tool can be used with full audit logging.

        Args:
            tool_name: Name of the tool
            context: Optional context information for audit
            **kwargs: Additional context (deprecated, use context dict)

        Returns:
            Permission decision: "allow", "confirm", or "deny"
        """
        # Compute decision
        decision = self._compute_decision(tool_name)

        # Audit log - important for security and debugging
        audit_context = context or kwargs
        logger.info(
            f"Permission check: tool={tool_name}, decision={decision}, "
            f"mode={self.mode}, context={audit_context}"
        )

        return decision

    def _compute_decision(self, tool_name: str) -> str:
        """
        Compute permission decision based on mode and tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Permission decision
        """
        # Mode: acceptAll
        if self.mode == PERMISSION_MODE_ACCEPT_ALL:
            logger.debug(f"Tool {tool_name}: ALLOW (acceptAll mode)")
            return PERMISSION_ALLOW

        # Mode: rejectAll
        if self.mode == PERMISSION_MODE_REJECT_ALL:
            logger.debug(f"Tool {tool_name}: CONFIRM (rejectAll mode)")
            return PERMISSION_CONFIRM

        # Mode: acceptEdits
        if self.mode == PERMISSION_MODE_ACCEPT_EDITS:
            if tool_name in self.read_tools:
                logger.debug(f"Tool {tool_name}: ALLOW (read tool)")
                return PERMISSION_ALLOW
            elif tool_name in self.edit_tools:
                logger.debug(f"Tool {tool_name}: CONFIRM (edit tool)")
                return PERMISSION_CONFIRM
            else:
                logger.warning(f"Unknown tool {tool_name}: defaulting to CONFIRM")
                return PERMISSION_CONFIRM

        # Mode: custom
        if self.mode == PERMISSION_MODE_CUSTOM:
            if tool_name in self.custom_permissions:
                decision = self.custom_permissions[tool_name]
                logger.debug(f"Tool {tool_name}: {decision.upper()} (custom rule)")
                return decision
            else:
                logger.debug(f"Tool {tool_name}: CONFIRM (no custom rule)")
                return PERMISSION_CONFIRM

        # Default: confirm
        logger.warning(f"Unknown permission mode {self.mode}: defaulting to CONFIRM")
        return PERMISSION_CONFIRM

    def set_mode(self, mode: str):
        """
        Set permission mode.

        Args:
            mode: Permission mode

        Raises:
            ValueError: If mode is invalid
        """
        if mode not in VALID_PERMISSION_MODES:
            raise ValueError(
                f"Invalid permission mode: {mode}. "
                f"Must be one of {VALID_PERMISSION_MODES}"
            )

        self.mode = mode
        logger.info(f"Permission mode changed to: {mode}")

    def set_custom_permission(self, tool_name: str, permission: str):
        """
        Set custom permission for a tool.

        Args:
            tool_name: Name of the tool
            permission: Permission (allow, confirm, deny)

        Raises:
            ValueError: If permission is invalid
        """
        if permission not in VALID_PERMISSION_DECISIONS:
            raise ValueError(
                f"Invalid permission: {permission}. "
                f"Must be one of {VALID_PERMISSION_DECISIONS}"
            )

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
