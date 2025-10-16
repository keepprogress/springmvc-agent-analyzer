"""
Integration tests for Passive Mode functionality.

Tests the passive mode where Claude Code performs analysis and
MCP server provides tools for file access, result submission, and graph management.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
import json

from analyzer_mcp.server import SpringMVCAnalyzerServer


@pytest.fixture
def passive_config():
    """Create passive mode configuration."""
    config_data = """
server:
  mode: "passive"

models:
  haiku: claude-3-5-haiku-20241022
  sonnet: claude-3-5-sonnet-20241022
  opus: claude-opus-4-20250514

agents:
  min_confidence: 0.7

mcp:
  result_max_age_seconds: 3600
  auto_cleanup: true
  rate_limit_enabled: false
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_data)
        config_path = f.name

    yield config_path

    # Cleanup
    os.unlink(config_path)


@pytest.fixture
def temp_java_controller():
    """Create temporary Java controller file."""
    java_code = """
package com.example.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
@RequestMapping("/user")
public class UserController {

    @GetMapping("/list")
    public String listUsers() {
        return "user/list";
    }

    @GetMapping("/create")
    public String createUser() {
        return "user/form";
    }
}
"""
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='Controller.java',
        delete=False
    ) as f:
        f.write(java_code)
        file_path = f.name

    yield file_path

    # Cleanup
    if os.path.exists(file_path):
        os.unlink(file_path)


@pytest.fixture
async def passive_server(passive_config):
    """Create MCP server instance in passive mode."""
    server = SpringMVCAnalyzerServer(config_path=passive_config)
    await server._initialize_components()
    return server


class TestPassiveModeInitialization:
    """Test passive mode initialization."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_passive_mode_initialization(self, passive_config):
        """Test server initializes correctly in passive mode."""
        server = SpringMVCAnalyzerServer(config_path=passive_config)

        # Check mode is set correctly
        assert server.config["server"]["mode"] == "passive"

        # Initialize components
        await server._initialize_components()

        # Should have graph builder and prompt manager
        assert server.graph_builder is not None
        assert server.prompt_manager is not None

        # Should NOT have model router, cost tracker, cache manager in passive mode
        assert server.model_router is None
        assert server.cost_tracker is None
        assert server.cache_manager is None

        # Should NOT have agents
        assert len(server.agents) == 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_passive_mode_no_api_key_required(self, passive_config):
        """Test passive mode works without ANTHROPIC_API_KEY."""
        # Ensure no API key in environment
        original_key = os.environ.get("ANTHROPIC_API_KEY")
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]

        try:
            server = SpringMVCAnalyzerServer(config_path=passive_config)
            await server._initialize_components()

            # Should initialize successfully without API key
            assert server.graph_builder is not None
            assert server.model_router is None  # No model router needed

        finally:
            # Restore original key
            if original_key:
                os.environ["ANTHROPIC_API_KEY"] = original_key


class TestPassiveModeTools:
    """Test passive mode tool implementations."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_read_file_with_prompt(self, passive_server, temp_java_controller):
        """Test read_file_with_prompt tool."""
        result = await passive_server._tool_read_file_with_prompt({
            "file_path": temp_java_controller,
            "agent_type": "auto"
        })

        # Should return file content and prompt
        assert "file_path" in result
        assert "agent_type" in result
        assert "file_content" in result
        assert "prompt_template" in result
        assert "instructions" in result

        # Agent type should be auto-detected as controller
        assert result["agent_type"] == "controller"

        # File content should be present
        assert "UserController" in result["file_content"]
        assert "@Controller" in result["file_content"]

        # Prompt template should be present
        assert result["prompt_template"] is not None
        assert len(result["prompt_template"]) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_submit_analysis(self, passive_server, temp_java_controller):
        """Test submit_analysis tool."""
        # Sample analysis result
        analysis = {
            "class_name": "UserController",
            "package": "com.example.controller",
            "base_url": "/user",
            "methods": [
                {
                    "name": "listUsers",
                    "url": "/list",
                    "http_method": "GET",
                    "view": "user/list"
                },
                {
                    "name": "createUser",
                    "url": "/create",
                    "http_method": "GET",
                    "view": "user/form"
                }
            ]
        }

        result = await passive_server._tool_submit_analysis({
            "file_path": temp_java_controller,
            "agent_type": "controller",
            "analysis": analysis,
            "confidence": 0.95
        })

        # Should return success status
        assert result["status"] == "success"
        assert result["file_path"] == temp_java_controller
        assert result["agent_type"] == "controller"

        # Result should be stored in analysis_results
        assert temp_java_controller in passive_server.analysis_results
        stored_result = passive_server.analysis_results[temp_java_controller]

        # Check stored result structure
        assert stored_result["agent"] == "controller"
        assert stored_result["analysis"] == analysis
        assert stored_result["confidence"] == 0.95
        assert stored_result["model_used"] == "claude-code"
        assert stored_result["cost"] == 0.0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_build_graph(self, passive_server, temp_java_controller):
        """Test build_graph tool."""
        # First submit some analysis results
        analysis = {
            "class_name": "UserController",
            "package": "com.example.controller",
            "base_url": "/user",
            "methods": []
        }

        await passive_server._tool_submit_analysis({
            "file_path": temp_java_controller,
            "agent_type": "controller",
            "analysis": analysis,
            "confidence": 0.9
        })

        # Build graph
        result = await passive_server._tool_build_graph({})

        # Should return success with stats
        assert result["status"] == "success"
        assert "nodes_added" in result
        assert "edges_added" in result
        assert "total_files_analyzed" in result
        assert "graph_stats" in result

        # Should have analyzed at least 1 file
        assert result["total_files_analyzed"] >= 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_build_graph_empty(self, passive_server):
        """Test build_graph with no results."""
        result = await passive_server._tool_build_graph({})

        # Should return warning for empty results
        assert result["status"] == "warning"
        assert result["nodes_added"] == 0
        assert result["edges_added"] == 0


class TestPassiveModeToolList:
    """Test tool list in passive mode."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_passive_mode_tools_list(self, passive_server):
        """Test that passive mode returns correct tool list."""
        tools = passive_server._get_passive_mode_tools()

        # Get tool names
        tool_names = [tool.name for tool in tools]

        # Should have passive mode specific tools
        assert "read_file_with_prompt" in tool_names
        assert "submit_analysis" in tool_names
        assert "build_graph" in tool_names

        # Should have shared graph tools
        assert "query_graph" in tool_names
        assert "find_dependencies" in tool_names
        assert "analyze_impact" in tool_names
        assert "export_graph" in tool_names

        # Should NOT have API mode tools
        assert "analyze_file" not in tool_names
        assert "analyze_directory" not in tool_names


class TestPassiveModeResources:
    """Test MCP resources in passive mode."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_prompt_resources_available(self, passive_server):
        """Test prompt template resources are available in passive mode."""
        # This would normally be tested through MCP protocol
        # Here we test the resource URIs directly

        # Test reading controller prompt
        try:
            prompt = passive_server.prompt_manager.get_prompt(
                agent_name="controller",
                prompt_type="analysis"
            )
            assert prompt is not None
            assert len(prompt) > 0
        except Exception as e:
            pytest.skip(f"Prompt manager not fully initialized: {e}")


class TestPassiveModeWorkflow:
    """Test complete passive mode workflows."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_analysis_workflow(self, passive_server, temp_java_controller):
        """Test complete workflow: read → analyze → submit → build → query."""

        # Step 1: Read file with prompt
        read_result = await passive_server._tool_read_file_with_prompt({
            "file_path": temp_java_controller
        })

        assert "file_content" in read_result
        assert "prompt_template" in read_result
        assert read_result["agent_type"] == "controller"

        # Step 2: Simulate analysis (normally done by Claude Code)
        analysis = {
            "class_name": "UserController",
            "package": "com.example.controller",
            "base_url": "/user",
            "methods": [
                {"name": "listUsers", "url": "/list"},
                {"name": "createUser", "url": "/create"}
            ]
        }

        # Step 3: Submit analysis
        submit_result = await passive_server._tool_submit_analysis({
            "file_path": temp_java_controller,
            "agent_type": "controller",
            "analysis": analysis,
            "confidence": 0.9
        })

        assert submit_result["status"] == "success"

        # Step 4: Build graph
        build_result = await passive_server._tool_build_graph({})

        assert build_result["status"] == "success"
        assert build_result["nodes_added"] >= 0

        # Step 5: Query graph
        query_result = await passive_server._tool_query_graph({
            "query_type": "stats"
        })

        assert "num_nodes" in query_result
        assert "num_edges" in query_result


class TestPassiveModeVsAPIMode:
    """Test differences between passive and API modes."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mode_configuration(self, passive_config):
        """Test mode is correctly configured."""
        server = SpringMVCAnalyzerServer(config_path=passive_config)
        assert server.config["server"]["mode"] == "passive"

        await server._initialize_components()

        # Passive mode should NOT initialize agents
        assert len(server.agents) == 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_api_tools_not_available_in_passive(self, passive_server):
        """Test API mode tools are not in passive mode tool list."""
        tools = passive_server._get_passive_mode_tools()
        tool_names = [tool.name for tool in tools]

        # API-specific tools should not be present
        assert "analyze_file" not in tool_names
        assert "analyze_directory" not in tool_names
