"""
Unit Tests for SDK Agent Tools Common Utilities.

Tests validation, path handling, formatting, and error handling functions
used across all SDK agent tools.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile

from sdk_agent.tools.common import (
    validate_and_expand_path,
    validate_tool_args,
    format_analysis_summary,
    handle_analysis_error
)
from sdk_agent.exceptions import SDKAgentError


class TestValidateAndExpandPath:
    """Test path validation and expansion with security checks."""

    def test_valid_absolute_path(self, tmp_path):
        """Test validation with valid absolute path."""
        test_file = tmp_path / "test.java"
        test_file.write_text("test content")

        result = validate_and_expand_path(
            str(test_file),
            project_root=str(tmp_path),
            must_exist=True
        )

        assert result == test_file
        assert result.exists()

    def test_valid_relative_path(self, tmp_path):
        """Test validation with valid relative path."""
        test_file = tmp_path / "src" / "Controller.java"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("test content")

        result = validate_and_expand_path(
            "src/Controller.java",
            project_root=str(tmp_path),
            must_exist=True
        )

        assert result.exists()
        assert result.name == "Controller.java"

    def test_file_not_found_must_exist(self, tmp_path):
        """Test that missing file raises error when must_exist=True."""
        with pytest.raises(SDKAgentError) as exc_info:
            validate_and_expand_path(
                "nonexistent.java",
                project_root=str(tmp_path),
                must_exist=True
            )

        assert "File not found" in str(exc_info.value)

    def test_file_not_found_optional(self, tmp_path):
        """Test that missing file is allowed when must_exist=False."""
        result = validate_and_expand_path(
            "nonexistent.java",
            project_root=str(tmp_path),
            must_exist=False
        )

        # Should not raise error, just return the path
        assert isinstance(result, Path)

    def test_path_traversal_security(self, tmp_path):
        """Test security check for path traversal attempts."""
        # Create file outside project root
        outside_dir = tmp_path.parent / "outside"
        outside_dir.mkdir(exist_ok=True)
        outside_file = outside_dir / "malicious.java"
        outside_file.write_text("malicious content")

        # Try to access file outside project root
        with patch('sdk_agent.tools.common.logger') as mock_logger:
            result = validate_and_expand_path(
                str(outside_file),
                project_root=str(tmp_path),
                must_exist=True
            )

            # Should log warning about path outside project root
            mock_logger.warning.assert_called_once()
            warning_message = mock_logger.warning.call_args[0][0]
            assert "outside project root" in warning_message


    def test_home_directory_expansion(self, tmp_path):
        """Test that ~ is expanded correctly."""
        with patch('pathlib.Path.home') as mock_home:
            mock_home.return_value = tmp_path

            # Create test file in "home" directory
            test_file = tmp_path / "test.java"
            test_file.write_text("test")

            result = validate_and_expand_path(
                "~/test.java",
                project_root=str(tmp_path),
                must_exist=True
            )

            assert result.exists()


class TestValidateToolArgs:
    """Test tool argument validation."""

    def test_valid_args_all_required(self):
        """Test validation with all required fields present."""
        args = {
            "file_path": "test.java",
            "include_details": True
        }

        result = validate_tool_args(
            args,
            required_fields=["file_path"],
            optional_fields={"include_details": True}
        )

        assert result["file_path"] == "test.java"
        assert result["include_details"] is True

    def test_missing_required_field(self):
        """Test that missing required field raises error."""
        args = {"wrong_field": "value"}

        with pytest.raises(SDKAgentError) as exc_info:
            validate_tool_args(
                args,
                required_fields=["file_path"],
                optional_fields=None
            )

        assert "Missing required fields" in str(exc_info.value)
        assert "file_path" in str(exc_info.value)

    def test_optional_fields_with_defaults(self):
        """Test that optional fields are added with defaults."""
        args = {"file_path": "test.java"}

        result = validate_tool_args(
            args,
            required_fields=["file_path"],
            optional_fields={
                "include_details": True,
                "format": "json"
            }
        )

        assert result["file_path"] == "test.java"
        assert result["include_details"] is True
        assert result["format"] == "json"

    def test_multiple_missing_required_fields(self):
        """Test error message lists all missing fields."""
        args = {}

        with pytest.raises(SDKAgentError) as exc_info:
            validate_tool_args(
                args,
                required_fields=["file_path", "project_root", "output_format"]
            )

        error_message = str(exc_info.value)
        assert "file_path" in error_message
        assert "project_root" in error_message
        assert "output_format" in error_message


class TestFormatAnalysisSummary:
    """Test analysis result formatting."""

    def test_controller_summary(self):
        """Test formatting of controller analysis."""
        analysis = {
            "class_name": "UserController",
            "package": "com.example.controllers",
            "base_url": "/users",
            "methods": [
                {"name": "listUsers", "http_method": "GET", "url": "/users/list"},
                {"name": "saveUser", "http_method": "POST", "url": "/users/save"}
            ],
            "dependencies": ["UserService", "UserRepository"]
        }

        summary = format_analysis_summary(analysis, "controller", include_details=True)

        assert "UserController" in summary
        assert "com.example.controllers" in summary
        assert "/users" in summary
        assert "2" in summary  # 2 methods
        assert "2" in summary  # 2 dependencies
        assert "GET /users/list" in summary
        assert "POST /users/save" in summary

    def test_service_summary(self):
        """Test formatting of service analysis."""
        analysis = {
            "class_name": "UserService",
            "package": "com.example.services",
            "methods": ["findById", "save", "delete"],
            "transactional_methods": ["save", "delete"]
        }

        summary = format_analysis_summary(analysis, "service", include_details=True)

        assert "UserService" in summary
        assert "com.example.services" in summary
        assert "3" in summary  # 3 methods
        assert "2" in summary  # 2 transactional
        assert "save" in summary
        assert "delete" in summary

    def test_jsp_summary(self):
        """Test formatting of JSP analysis."""
        analysis = {
            "file_name": "user-list.jsp",
            "includes": ["header.jsp", "footer.jsp"],
            "forms": [{"action": "/users/save", "method": "POST"}],
            "ajax_calls": [{"url": "/api/users", "method": "GET"}]
        }

        summary = format_analysis_summary(analysis, "jsp", include_details=True)

        assert "user-list.jsp" in summary
        assert "2" in summary  # 2 includes
        assert "1" in summary  # 1 form
        assert "1" in summary  # 1 AJAX call

    def test_mapper_summary(self):
        """Test formatting of mapper analysis."""
        analysis = {
            "namespace": "com.example.mapper.UserMapper",
            "statements": [
                {"id": "selectAll", "type": "select"},
                {"id": "insert", "type": "insert"}
            ],
            "result_maps": ["UserResultMap"]
        }

        summary = format_analysis_summary(analysis, "mapper", include_details=True)

        assert "com.example.mapper.UserMapper" in summary
        assert "2" in summary  # 2 statements
        assert "1" in summary  # 1 result map

    def test_procedure_summary(self):
        """Test formatting of procedure analysis."""
        analysis = {
            "procedure_name": "sp_update_user",
            "parameters": [
                {"name": "p_user_id", "type": "NUMBER", "mode": "IN"},
                {"name": "p_result", "type": "NUMBER", "mode": "OUT"}
            ],
            "calls": ["sp_validate_user"]
        }

        summary = format_analysis_summary(analysis, "procedure", include_details=True)

        assert "sp_update_user" in summary
        assert "2" in summary  # 2 parameters
        assert "1" in summary  # 1 call

    def test_summary_without_details(self):
        """Test summary without detailed information."""
        analysis = {
            "class_name": "UserController",
            "package": "com.example",
            "base_url": "/users",
            "methods": [{"name": "listUsers"}] * 10,  # 10 methods
            "dependencies": []
        }

        summary = format_analysis_summary(analysis, "controller", include_details=False)

        # Should contain high-level info
        assert "UserController" in summary
        assert "10" in summary

        # Should NOT contain method details
        assert "listUsers" not in summary


class TestHandleAnalysisError:
    """Test error handling consistency."""

    def test_error_response_format(self):
        """Test that error response has correct format."""
        error = ValueError("Invalid Java syntax")
        file_path = "test.java"
        tool_name = "analyze_controller"

        result = handle_analysis_error(error, file_path, tool_name)

        assert "content" in result
        assert "is_error" in result
        assert "error" in result
        assert result["is_error"] is True
        assert isinstance(result["content"], list)
        assert result["content"][0]["type"] == "text"

    def test_error_message_content(self):
        """Test that error message contains helpful information."""
        error = FileNotFoundError("test.java not found")
        file_path = "test.java"
        tool_name = "analyze_controller"

        result = handle_analysis_error(error, file_path, tool_name)

        message = result["content"][0]["text"]

        # Should contain tool name
        assert "analyze_controller" in message

        # Should contain file path
        assert "test.java" in message

        # Should contain error
        assert "not found" in message

        # Should contain suggestions
        assert "Suggestions" in message or "Check" in message

    @patch('sdk_agent.tools.common.logger')
    def test_error_logging(self, mock_logger):
        """Test that errors are logged correctly."""
        error = RuntimeError("Analysis failed")
        file_path = "test.java"
        tool_name = "analyze_controller"

        handle_analysis_error(error, file_path, tool_name)

        # Should log error with exc_info
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "analyze_controller" in call_args[0][0]
        assert "test.java" in call_args[0][0]
        assert call_args[1]["exc_info"] is True


class TestPathSecurityChecks:
    """Test security checks for path manipulation."""

    def test_prevents_directory_traversal(self, tmp_path):
        """Test that .. path traversal is caught."""
        with patch('sdk_agent.tools.common.logger') as mock_logger:
            # Try to access parent directory
            validate_and_expand_path(
                "../../../etc/passwd",
                project_root=str(tmp_path),
                must_exist=False
            )

            # Should log warning
            assert mock_logger.warning.called

    def test_absolute_path_outside_project(self, tmp_path):
        """Test absolute path outside project root."""
        # Create file outside project
        outside_file = tmp_path.parent / "outside.java"
        outside_file.write_text("test")

        with patch('sdk_agent.tools.common.logger') as mock_logger:
            result = validate_and_expand_path(
                str(outside_file),
                project_root=str(tmp_path),
                must_exist=True
            )

            # Should warn about path outside root
            mock_logger.warning.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
