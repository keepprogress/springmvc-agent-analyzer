"""Tests for SDK Agent permissions."""

import pytest

from sdk_agent.permissions import PermissionManager, create_permission_manager
from sdk_agent.constants import (
    PERMISSION_MODE_ACCEPT_ALL,
    PERMISSION_MODE_ACCEPT_EDITS,
    PERMISSION_MODE_REJECT_ALL,
    PERMISSION_MODE_CUSTOM,
    PERMISSION_ALLOW,
    PERMISSION_CONFIRM,
    PERMISSION_DENY,
)


class TestPermissionManager:
    """Test PermissionManager class."""

    def test_initialization(self):
        """Test permission manager initialization."""
        pm = PermissionManager()
        assert pm.mode == PERMISSION_MODE_ACCEPT_EDITS

    def test_invalid_mode_initialization(self):
        """Test invalid mode raises error."""
        with pytest.raises(ValueError, match="Invalid permission mode"):
            PermissionManager(mode="invalid")

    def test_accept_all_mode(self):
        """Test acceptAll mode allows all tools."""
        pm = PermissionManager(mode=PERMISSION_MODE_ACCEPT_ALL)

        assert pm.can_use_tool("analyze_controller") == PERMISSION_ALLOW
        assert pm.can_use_tool("build_graph") == PERMISSION_ALLOW
        assert pm.can_use_tool("any_tool") == PERMISSION_ALLOW

    def test_reject_all_mode(self):
        """Test rejectAll mode confirms all tools."""
        pm = PermissionManager(mode=PERMISSION_MODE_REJECT_ALL)

        assert pm.can_use_tool("analyze_controller") == PERMISSION_CONFIRM
        assert pm.can_use_tool("build_graph") == PERMISSION_CONFIRM
        assert pm.can_use_tool("any_tool") == PERMISSION_CONFIRM

    def test_accept_edits_mode_read_tools(self):
        """Test acceptEdits mode allows read tools."""
        pm = PermissionManager(mode=PERMISSION_MODE_ACCEPT_EDITS)

        assert pm.can_use_tool("analyze_controller") == PERMISSION_ALLOW
        assert pm.can_use_tool("analyze_service") == PERMISSION_ALLOW
        assert pm.can_use_tool("query_graph") == PERMISSION_ALLOW
        assert pm.can_use_tool("read_file") == PERMISSION_ALLOW

    def test_accept_edits_mode_edit_tools(self):
        """Test acceptEdits mode confirms edit tools."""
        pm = PermissionManager(mode=PERMISSION_MODE_ACCEPT_EDITS)

        assert pm.can_use_tool("build_graph") == PERMISSION_CONFIRM
        assert pm.can_use_tool("export_graph") == PERMISSION_CONFIRM

    def test_custom_mode(self):
        """Test custom mode with custom permissions."""
        custom_perms = {
            "analyze_controller": PERMISSION_ALLOW,
            "build_graph": PERMISSION_DENY,
            "export_graph": PERMISSION_CONFIRM,
        }

        pm = PermissionManager(
            mode=PERMISSION_MODE_CUSTOM,
            custom_permissions=custom_perms
        )

        assert pm.can_use_tool("analyze_controller") == PERMISSION_ALLOW
        assert pm.can_use_tool("build_graph") == PERMISSION_DENY
        assert pm.can_use_tool("export_graph") == PERMISSION_CONFIRM

        # Unknown tool defaults to confirm
        assert pm.can_use_tool("unknown_tool") == PERMISSION_CONFIRM

    def test_set_mode(self):
        """Test changing permission mode."""
        pm = PermissionManager(mode=PERMISSION_MODE_ACCEPT_EDITS)

        pm.set_mode(PERMISSION_MODE_ACCEPT_ALL)
        assert pm.mode == PERMISSION_MODE_ACCEPT_ALL

        with pytest.raises(ValueError, match="Invalid permission mode"):
            pm.set_mode("invalid")

    def test_set_custom_permission(self):
        """Test setting custom permission."""
        pm = PermissionManager()

        pm.set_custom_permission("new_tool", PERMISSION_DENY)
        assert pm.custom_permissions["new_tool"] == PERMISSION_DENY

        with pytest.raises(ValueError, match="Invalid permission"):
            pm.set_custom_permission("tool", "invalid")

    def test_audit_logging(self):
        """Test audit logging with context."""
        pm = PermissionManager()

        # Should not raise, just log
        context = {"user": "test", "action": "analyze"}
        decision = pm.can_use_tool("analyze_controller", context=context)

        assert decision == PERMISSION_ALLOW

    def test_get_permissions_summary(self):
        """Test getting permissions summary."""
        pm = PermissionManager(mode=PERMISSION_MODE_ACCEPT_EDITS)
        summary = pm.get_permissions_summary()

        assert summary["mode"] == PERMISSION_MODE_ACCEPT_EDITS
        assert "read_tools" in summary
        assert "edit_tools" in summary

    def test_create_permission_manager_from_config(self):
        """Test creating permission manager from config."""
        config = {
            "permission_mode": PERMISSION_MODE_CUSTOM,
            "permissions": {
                "tool1": PERMISSION_ALLOW,
                "tool2": PERMISSION_DENY,
            }
        }

        pm = create_permission_manager(config)

        assert pm.mode == PERMISSION_MODE_CUSTOM
        assert pm.custom_permissions["tool1"] == PERMISSION_ALLOW
        assert pm.custom_permissions["tool2"] == PERMISSION_DENY
