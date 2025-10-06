"""Tests for SDK Agent utilities."""

import pytest
import tempfile
import os
from pathlib import Path

from sdk_agent.utils import (
    expand_file_path,
    detect_file_type,
    format_tool_result,
    validate_confidence,
    load_system_prompt,
    get_file_list,
)
from sdk_agent.exceptions import SDKAgentError
from sdk_agent.constants import (
    FILE_TYPE_CONTROLLER,
    FILE_TYPE_SERVICE,
    FILE_TYPE_JSP,
    FILE_TYPE_UNKNOWN,
    MIN_CONFIDENCE_THRESHOLD,
)


class TestExpandFilePath:
    """Test file path expansion."""

    def test_absolute_path(self):
        """Test absolute path remains unchanged."""
        path = "/absolute/path/to/file.java"
        result = expand_file_path(path)
        assert Path(result).is_absolute()

    def test_relative_path_with_root(self):
        """Test relative path expansion with project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = expand_file_path("src/main/java/Test.java", tmpdir)
            # Normalize paths for comparison (handles Windows short/long paths)
            result_normalized = Path(result).resolve()
            tmpdir_normalized = Path(tmpdir).resolve()
            assert str(tmpdir_normalized) in str(result_normalized)
            assert "src" in result and "main" in result and "java" in result and "Test.java" in result

    def test_path_traversal_attack(self):
        """Test path traversal prevention."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Try to escape project root
            malicious_path = "../../../etc/passwd"

            with pytest.raises(SDKAgentError, match="Security error"):
                expand_file_path(malicious_path, tmpdir)


class TestDetectFileType:
    """Test file type detection."""

    def test_jsp_file(self):
        """Test JSP file detection."""
        with tempfile.NamedTemporaryFile(
            suffix=".jsp", delete=False
        ) as f:
            file_path = f.name

        try:
            assert detect_file_type(file_path) == FILE_TYPE_JSP
        finally:
            os.unlink(file_path)

    def test_controller_by_name(self):
        """Test controller detection by filename."""
        with tempfile.NamedTemporaryFile(
            suffix="Controller.java", delete=False
        ) as f:
            f.write(b"public class UserController {}")
            file_path = f.name

        try:
            assert detect_file_type(file_path) == FILE_TYPE_CONTROLLER
        finally:
            os.unlink(file_path)

    def test_controller_by_annotation(self):
        """Test controller detection by @Controller annotation."""
        java_code = b"""
package com.example;

import org.springframework.stereotype.Controller;

@Controller
public class MyHandler {
}
"""
        with tempfile.NamedTemporaryFile(
            suffix=".java", delete=False
        ) as f:
            f.write(java_code)
            file_path = f.name

        try:
            assert detect_file_type(file_path) == FILE_TYPE_CONTROLLER
        finally:
            os.unlink(file_path)

    def test_service_by_annotation(self):
        """Test service detection by @Service annotation."""
        java_code = b"""
@Service
public class UserService {
}
"""
        with tempfile.NamedTemporaryFile(
            suffix=".java", delete=False
        ) as f:
            f.write(java_code)
            file_path = f.name

        try:
            assert detect_file_type(file_path) == FILE_TYPE_SERVICE
        finally:
            os.unlink(file_path)

    def test_unknown_file(self):
        """Test unknown file type."""
        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False
        ) as f:
            file_path = f.name

        try:
            assert detect_file_type(file_path) == FILE_TYPE_UNKNOWN
        finally:
            os.unlink(file_path)


class TestFormatToolResult:
    """Test tool result formatting."""

    def test_format_json(self):
        """Test JSON formatting."""
        data = {"status": "success", "count": 5}
        result = format_tool_result(data, "json")

        assert "content" in result
        assert "data" in result
        assert result["data"] == data
        assert "success" in result["content"][0]["text"]

    def test_format_markdown(self):
        """Test markdown formatting."""
        data = {"name": "UserController", "endpoints": 3}
        result = format_tool_result(data, "markdown")

        assert "content" in result
        assert "name" in result["content"][0]["text"]
        assert "UserController" in result["content"][0]["text"]


class TestValidateConfidence:
    """Test confidence validation."""

    def test_valid_confidence(self):
        """Test valid confidence scores."""
        assert validate_confidence(0.8) is True
        assert validate_confidence(0.7) is True
        assert validate_confidence(1.0) is True

    def test_invalid_confidence(self):
        """Test invalid confidence scores."""
        assert validate_confidence(0.6) is False
        assert validate_confidence(0.5) is False
        assert validate_confidence(0.0) is False

    def test_custom_threshold(self):
        """Test custom threshold."""
        assert validate_confidence(0.6, min_threshold=0.5) is True
        assert validate_confidence(0.4, min_threshold=0.5) is False


class TestLoadSystemPrompt:
    """Test system prompt loading."""

    def test_load_prompt(self):
        """Test loading system prompt."""
        prompt_content = "You are an expert analyzer."

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(prompt_content)
            prompt_path = f.name

        try:
            result = load_system_prompt(prompt_path)
            assert result == prompt_content

            # Test caching - load again
            result2 = load_system_prompt(prompt_path)
            assert result2 == prompt_content

        finally:
            os.unlink(prompt_path)


class TestGetFileList:
    """Test file listing."""

    def test_get_java_files(self):
        """Test getting Java files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir, "Test1.java").write_text("class Test1 {}")
            Path(tmpdir, "Test2.java").write_text("class Test2 {}")
            Path(tmpdir, "README.md").write_text("# Readme")

            files = get_file_list(tmpdir, pattern="**/*.java")

            assert len(files) == 2
            assert all(f.endswith(".java") for f in files)

    def test_exclude_pattern(self):
        """Test excluding files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir, "Test.java").write_text("class Test {}")
            Path(tmpdir, "TestGenerated.java").write_text("class TestGenerated {}")

            files = get_file_list(
                tmpdir,
                pattern="**/*.java",
                exclude=["*Generated.java"]
            )

            assert len(files) == 1
            assert "TestGenerated.java" not in files[0]
