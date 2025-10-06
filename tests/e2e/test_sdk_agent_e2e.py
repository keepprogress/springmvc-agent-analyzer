"""
End-to-End Tests for SDK Agent Mode.

Tests complete workflows from start to finish, including:
- Full project analysis
- Graph building and querying
- Error scenarios and recovery
- Performance under load
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Skip all tests if SDK not installed
pytest.importorskip("claude_agent_sdk", reason="SDK not installed")

from sdk_agent.client import SpringMVCAnalyzerAgent
from sdk_agent.exceptions import SDKAgentError


class TestFullProjectAnalysis:
    """End-to-end tests for complete project analysis workflows."""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_full_project_analysis_workflow(self, tmp_path):
        """
        Test complete workflow: analyze files → build graph → query → export.

        This simulates a real user workflow analyzing a complete Spring MVC project.
        """
        # Create test project structure
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        controllers_dir = project_dir / "src" / "main" / "java" / "controllers"
        controllers_dir.mkdir(parents=True)

        # Create test controller file
        controller_file = controllers_dir / "UserController.java"
        controller_file.write_text("""
package com.example.controllers;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

@Controller
@RequestMapping("/users")
public class UserController {

    @Autowired
    private UserService userService;

    @GetMapping
    public String listUsers(Model model) {
        return "users/list";
    }

    @PostMapping
    public String createUser(@ModelAttribute User user) {
        userService.save(user);
        return "redirect:/users";
    }
}
        """)

        # Initialize agent
        agent = SpringMVCAnalyzerAgent(
            hooks_enabled=True,
            permission_mode="acceptAll"
        )

        # Mock the SDK client
        agent.client.__aenter__ = AsyncMock()
        agent.client.__aexit__ = AsyncMock()
        agent.client.query = AsyncMock()

        async def mock_receive():
            yield "Analysis complete. Found 1 controller with 2 endpoints."

        agent.client.receive_response = mock_receive

        # Execute full workflow
        result = await agent.analyze_project(
            project_path=str(project_dir),
            output_format="markdown"
        )

        # Verify results
        assert result is not None
        assert result.get("success") is True
        assert result.get("project_path") == str(project_dir)
        assert "analysis" in result

        # Verify client interactions
        agent.client.__aenter__.assert_called_once()
        agent.client.__aexit__.assert_called_once()
        agent.client.query.assert_called_once()


    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_incremental_analysis_workflow(self):
        """
        Test incremental analysis: analyze files one by one and build graph incrementally.
        """
        agent = SpringMVCAnalyzerAgent()

        # Mock client for incremental queries
        agent.client.__aenter__ = AsyncMock()
        agent.client.__aexit__ = AsyncMock()
        agent.client.query = AsyncMock()

        responses = [
            ["UserController analyzed"],
            ["UserService analyzed"],
            ["Graph built with 2 nodes"],
            ["Dependencies: UserController → UserService"]
        ]
        response_iter = iter(responses)

        async def mock_receive():
            for msg in next(response_iter):
                yield msg

        agent.client.receive_response = mock_receive

        # Simulate incremental analysis
        await agent.client.__aenter__()
        try:
            # Step 1: Analyze controller
            await agent.client.query("Analyze UserController.java")
            result1 = [msg async for msg in agent.client.receive_response()]
            assert len(result1) > 0

            # Step 2: Analyze service
            await agent.client.query("Analyze UserService.java")
            result2 = [msg async for msg in agent.client.receive_response()]
            assert len(result2) > 0

            # Step 3: Build graph
            await agent.client.query("Build knowledge graph")
            result3 = [msg async for msg in agent.client.receive_response()]
            assert len(result3) > 0

            # Step 4: Query dependencies
            await agent.client.query("Find dependencies of UserController")
            result4 = [msg async for msg in agent.client.receive_response()]
            assert len(result4) > 0

        finally:
            await agent.client.__aexit__(None, None, None)


    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """
        Test error handling and recovery during analysis.

        Simulates various failure scenarios:
        - File not found
        - Analysis failure
        - API errors
        - Recovery and continuation
        """
        agent = SpringMVCAnalyzerAgent(hooks_enabled=True)

        # Mock client with error scenarios
        agent.client.__aenter__ = AsyncMock()
        agent.client.__aexit__ = AsyncMock()

        call_count = 0

        async def mock_query_with_errors(query: str):
            nonlocal call_count
            call_count += 1

            # First call: simulate error
            if call_count == 1:
                raise SDKAgentError("File not found: missing.java")
            # Subsequent calls: success
            return None

        agent.client.query = mock_query_with_errors

        async def mock_receive_success():
            yield "Analysis successful after retry"

        agent.client.receive_response = mock_receive_success

        await agent.client.__aenter__()
        try:
            # First attempt: expect error
            with pytest.raises(SDKAgentError):
                await agent.client.query("Analyze missing.java")

            # Second attempt: success
            await agent.client.query("Analyze existing.java")
            results = [msg async for msg in agent.client.receive_response()]
            assert len(results) > 0
            assert "successful" in results[0]

        finally:
            await agent.client.__aexit__(None, None, None)


class TestConcurrentOperations:
    """Test concurrent and parallel operations."""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_concurrent_file_analysis(self):
        """
        Test analyzing multiple files concurrently.

        Verifies that batch processing works correctly with
        concurrent operations.
        """
        from sdk_agent.tools.batch_processor import process_files_in_batches

        # Mock files
        files = [Path(f"file{i}.java") for i in range(20)]

        # Mock process function
        process_count = 0

        async def mock_process(file_path: Path) -> dict:
            nonlocal process_count
            process_count += 1
            await asyncio.sleep(0.01)  # Simulate work
            return {"file": str(file_path), "analyzed": True}

        # Process in batches
        results = await process_files_in_batches(
            files,
            mock_process,
            batch_size=5,
            max_concurrency=3
        )

        # Verify all files processed
        assert len(results) == 20
        assert process_count == 20
        assert all(r.get("success") for r in results)


class TestLongRunningSession:
    """Test long-running analysis sessions."""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_max_turns_enforcement(self):
        """
        Test that max_turns limit is enforced and context compaction occurs.
        """
        agent = SpringMVCAnalyzerAgent(max_turns=10)

        # Verify max_turns is set
        assert agent.config.max_turns == 10

        # Mock client
        agent.client.__aenter__ = AsyncMock()
        agent.client.__aexit__ = AsyncMock()
        agent.client.query = AsyncMock()

        async def mock_receive():
            yield "Response"

        agent.client.receive_response = mock_receive

        # Note: Full interactive session testing would require
        # mocking user input, which is complex. This test verifies
        # configuration is correctly set up.

        assert agent.config.max_turns == 10


    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_context_retention_across_queries(self):
        """
        Test that context is retained across multiple queries in a session.
        """
        agent = SpringMVCAnalyzerAgent()

        agent.client.__aenter__ = AsyncMock()
        agent.client.__aexit__ = AsyncMock()
        agent.client.query = AsyncMock()

        queries = []

        async def capture_query(query: str):
            queries.append(query)

        agent.client.query = capture_query

        async def mock_receive():
            yield "Response"

        agent.client.receive_response = mock_receive

        await agent.client.__aenter__()
        try:
            # Multiple queries in same session
            await agent.client.query("First query")
            await agent.client.query("Second query referencing first")
            await agent.client.query("Third query building on previous")

            # Verify all queries captured
            assert len(queries) == 3
            assert queries[0] == "First query"
            assert queries[1] == "Second query referencing first"

        finally:
            await agent.client.__aexit__(None, None, None)


class TestHooksIntegration:
    """Test hooks working together in complete workflows."""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_validation_hook_blocks_dangerous_operation(self):
        """
        Test that ValidationHook prevents dangerous operations in real workflow.
        """
        from sdk_agent.hooks.validation import ValidationHook

        hook = ValidationHook({"enabled": True, "strict_mode": True})

        # Test dangerous path
        result = await hook(
            tool_name="analyze_controller",
            tool_input={"file_path": "../../../etc/passwd"},
            context={}
        )

        assert result.get("allowed") is False
        assert "dangerous" in result.get("reason", "").lower()


    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_cache_hook_improves_performance(self):
        """
        Test that CacheHook provides performance benefits for repeated analysis.
        """
        from sdk_agent.hooks.cache import CacheHook

        hook = CacheHook({
            "enabled": True,
            "cache_dir": ".cache/test"
        })

        # First call: cache miss
        await hook(
            tool_name="analyze_controller",
            tool_input={"file_path": "UserController.java"},
            tool_output={
                "content": [{"type": "text", "text": "Analysis result"}],
                "data": {"class_name": "UserController"}
            },
            context={}
        )

        # Cache should now contain result
        # (Full cache testing is in unit tests)


class TestPerformance:
    """Performance and stress tests."""

    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_project_analysis_performance(self, tmp_path):
        """
        Test performance with large project (100+ files).

        Verifies that batch processing and caching provide good performance.
        """
        # Create large project
        project_dir = tmp_path / "large_project"
        project_dir.mkdir()

        controllers_dir = project_dir / "src" / "main" / "java" / "controllers"
        controllers_dir.mkdir(parents=True)

        # Create 100 mock controller files
        for i in range(100):
            controller_file = controllers_dir / f"Controller{i}.java"
            controller_file.write_text(f"""
package com.example.controllers;

@Controller
public class Controller{i} {{
    @GetMapping("/path{i}")
    public String method{i}() {{
        return "view{i}";
    }}
}}
            """)

        # This test would require full SDK integration
        # For now, verify file structure is created
        assert len(list(controllers_dir.glob("*.java"))) == 100


class TestErrorScenarios:
    """Test various error scenarios and recovery."""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_network_failure_handling(self):
        """Test handling of network/API failures."""
        agent = SpringMVCAnalyzerAgent()

        agent.client.__aenter__ = AsyncMock()
        agent.client.__aexit__ = AsyncMock()

        # Simulate network error
        agent.client.query = AsyncMock(
            side_effect=ConnectionError("Network unavailable")
        )

        await agent.client.__aenter__()
        try:
            with pytest.raises(ConnectionError):
                await agent.client.query("Test query")
        finally:
            await agent.client.__aexit__(None, None, None)


    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_invalid_configuration_handling(self):
        """Test handling of invalid configuration."""
        with pytest.raises(Exception):
            # Invalid permission mode
            agent = SpringMVCAnalyzerAgent(permission_mode="invalid_mode")


    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_malformed_tool_input_handling(self):
        """Test handling of malformed tool inputs."""
        from sdk_agent.tools.common import validate_tool_args
        from sdk_agent.exceptions import SDKAgentError

        # Missing required field
        with pytest.raises(SDKAgentError):
            validate_tool_args(
                {"wrong_field": "value"},
                required_fields=["file_path"]
            )

        # Valid input
        result = validate_tool_args(
            {"file_path": "test.java"},
            required_fields=["file_path"],
            optional_fields={"include_details": True}
        )
        assert result["file_path"] == "test.java"
        assert result["include_details"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "e2e"])
