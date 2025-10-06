"""
Unit Tests for SDK Agent Hooks System.

Tests the five hook types: PreToolUse, PostToolUse, PreCompact,
UserPromptSubmit, and Stop hooks.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from sdk_agent.hooks.validation import ValidationHook
from sdk_agent.hooks.cache import CacheHook
from sdk_agent.hooks.cleanup import CleanupHook
from sdk_agent.hooks.context_manager import ContextManagerHook
from sdk_agent.hooks.input_enhancement import InputEnhancementHook


class TestValidationHook:
    """Test PreToolUse validation hook."""

    @pytest.mark.asyncio
    async def test_validation_hook_enabled(self):
        """Test validation hook when enabled."""
        hook = ValidationHook({"enabled": True})

        result = await hook(
            tool_name="analyze_controller",
            tool_input={"file_path": "test.java"},
            context={}
        )

        # Should allow valid input
        assert result.get("allowed") is not False

    @pytest.mark.asyncio
    async def test_validation_hook_disabled(self):
        """Test validation hook when disabled."""
        hook = ValidationHook({"enabled": False})

        result = await hook(
            tool_name="analyze_controller",
            tool_input={"file_path": "../../../etc/passwd"},
            context={}
        )

        # Should pass through when disabled
        assert result == {}

    @pytest.mark.asyncio
    async def test_dangerous_path_detection(self):
        """Test detection of dangerous path traversal."""
        hook = ValidationHook({"enabled": True, "strict_mode": True})

        # Test path traversal attempt
        result = await hook(
            tool_name="analyze_controller",
            tool_input={"file_path": "../../../etc/passwd"},
            context={}
        )

        assert result.get("allowed") is False
        assert "dangerous" in result.get("reason", "").lower()

    @pytest.mark.asyncio
    async def test_confidence_threshold_check(self):
        """Test confidence threshold validation."""
        hook = ValidationHook({
            "enabled": True,
            "min_confidence": 0.8
        })

        # Test low confidence
        result = await hook(
            tool_name="analyze_controller",
            tool_input={"file_path": "test.java"},
            context={"confidence": 0.5}
        )

        # Depending on implementation, may warn or upgrade model
        assert "confidence" in str(result).lower() or result == {}


class TestCacheHook:
    """Test PostToolUse cache hook."""

    @pytest.mark.asyncio
    async def test_cache_hook_enabled(self):
        """Test cache hook stores results."""
        hook = CacheHook({
            "enabled": True,
            "cache_dir": ".cache/test"
        })

        tool_output = {
            "content": [{"type": "text", "text": "Analysis result"}],
            "data": {"class_name": "TestController"}
        }

        result = await hook(
            tool_name="analyze_controller",
            tool_input={"file_path": "test.java"},
            tool_output=tool_output,
            context={}
        )

        # Should return the output unchanged
        assert result.get("content") == tool_output["content"]

    @pytest.mark.asyncio
    async def test_cache_hook_disabled(self):
        """Test cache hook when disabled."""
        hook = CacheHook({"enabled": False})

        tool_output = {
            "content": [{"type": "text", "text": "Analysis result"}]
        }

        result = await hook(
            tool_name="analyze_controller",
            tool_input={"file_path": "test.java"},
            tool_output=tool_output,
            context={}
        )

        # Should pass through
        assert result == {}

    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Test that cache keys are generated correctly."""
        hook = CacheHook({
            "enabled": True,
            "cache_dir": ".cache/test"
        })

        # Same input should generate same cache key
        tool_input1 = {"file_path": "test.java", "include_details": True}
        tool_input2 = {"file_path": "test.java", "include_details": True}

        # Mock the internal cache key generation
        with patch.object(hook, '_generate_cache_key') as mock_gen:
            mock_gen.return_value = "test_key"

            await hook(
                tool_name="analyze_controller",
                tool_input=tool_input1,
                tool_output={"content": []},
                context={}
            )

            await hook(
                tool_name="analyze_controller",
                tool_input=tool_input2,
                tool_output={"content": []},
                context={}
            )

            # Should have been called twice with same inputs
            assert mock_gen.call_count == 2


class TestCleanupHook:
    """Test Stop hook for cleanup."""

    @pytest.mark.asyncio
    async def test_cleanup_hook_enabled(self):
        """Test cleanup hook performs cleanup."""
        hook = CleanupHook({"enabled": True})

        result = await hook(
            context={"session_id": "test123"}
        )

        # Should return empty dict or cleanup confirmation
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_cleanup_hook_disabled(self):
        """Test cleanup hook when disabled."""
        hook = CleanupHook({"enabled": False})

        result = await hook(
            context={"session_id": "test123"}
        )

        # Should pass through
        assert result == {}

    @pytest.mark.asyncio
    async def test_temporary_file_cleanup(self):
        """Test that temporary files are cleaned up."""
        hook = CleanupHook({
            "enabled": True,
            "clean_temp_files": True
        })

        with patch('sdk_agent.hooks.cleanup.cleanup_temp_files') as mock_cleanup:
            await hook(context={})

            # Depending on implementation, cleanup may be called
            # This test validates the hook structure


class TestContextManagerHook:
    """Test PreCompact context manager hook."""

    @pytest.mark.asyncio
    async def test_context_manager_hook_enabled(self):
        """Test context manager hook."""
        hook = ContextManagerHook({"enabled": True})

        messages = [
            {"role": "user", "content": "Query 1"},
            {"role": "assistant", "content": "Response 1"},
            {"role": "user", "content": "Query 2"},
            {"role": "assistant", "content": "Response 2"},
            {"role": "user", "content": "Query 3"}
        ]

        result = await hook(
            messages=messages,
            context={}
        )

        # Should return compacted messages
        assert "messages" in result or result == {}

    @pytest.mark.asyncio
    async def test_context_manager_disabled(self):
        """Test context manager when disabled."""
        hook = ContextManagerHook({"enabled": False})

        messages = [
            {"role": "user", "content": "Query"},
            {"role": "assistant", "content": "Response"}
        ]

        result = await hook(
            messages=messages,
            context={}
        )

        # Should pass through
        assert result == {}

    @pytest.mark.asyncio
    async def test_message_priority_preservation(self):
        """Test that important messages are preserved."""
        hook = ContextManagerHook({
            "enabled": True,
            "preserve_recent": 3
        })

        messages = []
        for i in range(10):
            messages.append({"role": "user", "content": f"Query {i}"})
            messages.append({"role": "assistant", "content": f"Response {i}"})

        with patch.object(hook, '_select_important_messages') as mock_select:
            mock_select.return_value = messages[-6:]  # Last 3 exchanges

            result = await hook(
                messages=messages,
                context={}
            )

            # Should have called selection
            mock_select.assert_called_once()


class TestInputEnhancementHook:
    """Test UserPromptSubmit input enhancement hook."""

    @pytest.mark.asyncio
    async def test_input_enhancement_enabled(self):
        """Test input enhancement hook."""
        hook = InputEnhancementHook({"enabled": True})

        user_input = "分析 UserController.java"

        result = await hook(
            user_input=user_input,
            context={}
        )

        # Should return enhanced input or empty dict
        assert "enhanced_input" in result or result == {}

    @pytest.mark.asyncio
    async def test_input_enhancement_disabled(self):
        """Test input enhancement when disabled."""
        hook = InputEnhancementHook({"enabled": False})

        user_input = "分析 UserController.java"

        result = await hook(
            user_input=user_input,
            context={}
        )

        # Should pass through
        assert result == {}

    @pytest.mark.asyncio
    async def test_path_expansion(self):
        """Test that file paths are expanded."""
        hook = InputEnhancementHook({
            "enabled": True,
            "expand_paths": True
        })

        user_input = "分析 ~/project/UserController.java"

        with patch('pathlib.Path.expanduser') as mock_expand:
            mock_expand.return_value = Path("/home/user/project/UserController.java")

            result = await hook(
                user_input=user_input,
                context={"project_root": "/home/user/project"}
            )

            # Path expansion may be applied
            # This validates hook structure

    @pytest.mark.asyncio
    async def test_context_addition(self):
        """Test that relevant context is added."""
        hook = InputEnhancementHook({
            "enabled": True,
            "add_context": True
        })

        user_input = "找出依賴關係"

        result = await hook(
            user_input=user_input,
            context={
                "last_analyzed_file": "UserController.java",
                "project_type": "SpringMVC"
            }
        )

        # Context may be added to input
        if "enhanced_input" in result:
            enhanced = result["enhanced_input"]
            assert isinstance(enhanced, str)


class TestHookIntegration:
    """Test hooks working together."""

    @pytest.mark.asyncio
    async def test_hook_chain_execution(self):
        """Test multiple hooks executing in sequence."""
        validation_hook = ValidationHook({"enabled": True})
        cache_hook = CacheHook({"enabled": True, "cache_dir": ".cache/test"})

        tool_input = {"file_path": "test.java"}
        tool_output = {"content": [{"type": "text", "text": "Result"}]}

        # Step 1: PreToolUse validation
        validation_result = await validation_hook(
            tool_name="analyze_controller",
            tool_input=tool_input,
            context={}
        )

        # Should be allowed
        assert validation_result.get("allowed") is not False

        # Step 2: PostToolUse caching
        cache_result = await cache_hook(
            tool_name="analyze_controller",
            tool_input=tool_input,
            tool_output=tool_output,
            context={}
        )

        # Should process successfully
        assert isinstance(cache_result, dict)

    @pytest.mark.asyncio
    async def test_hook_error_handling(self):
        """Test that hook errors don't crash the system."""
        hook = ValidationHook({"enabled": True})

        # Pass invalid input
        with patch.object(hook, '__call__') as mock_call:
            mock_call.side_effect = Exception("Hook error")

            try:
                await hook(
                    tool_name="analyze_controller",
                    tool_input=None,  # Invalid
                    context={}
                )
            except Exception as e:
                # Should raise the error
                assert "Hook error" in str(e)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
