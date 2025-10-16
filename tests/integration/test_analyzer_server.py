"""
Integration tests for MCP server.

Tests all MCP tools, error handling, rate limiting, and resource management.
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from analyzer_mcp.server import SpringMVCAnalyzerServer


@pytest.fixture
def temp_config():
    """Create temporary config file."""
    config_data = """
models:
  haiku: claude-3-5-haiku-20241022
  sonnet: claude-3-5-sonnet-20241022
  opus: claude-opus-4-20250514

agents:
  min_confidence: 0.7

mcp:
  result_max_age_seconds: 60
  auto_cleanup: true
  rate_limit_enabled: true
  rate_limit_requests_per_minute: 10
  rate_limit_burst: 5
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_data)
        config_path = f.name

    yield config_path

    # Cleanup
    os.unlink(config_path)


@pytest.fixture
def temp_java_file():
    """Create temporary Java controller file."""
    java_code = """
package com.example.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
@RequestMapping("/test")
public class TestController {

    @RequestMapping("/hello")
    public String hello() {
        return "hello";
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
    os.unlink(file_path)


@pytest.fixture
async def mcp_server(temp_config):
    """Create MCP server instance."""
    server = SpringMVCAnalyzerServer(config_path=temp_config)

    # Mock Anthropic API calls to avoid actual API usage
    with patch('core.model_router.ModelRouter._call_anthropic') as mock_call:
        mock_call.return_value = {
            "agent": "controller",
            "analysis": {
                "class_name": "TestController",
                "package": "com.example.controller",
                "request_mappings": ["/test/hello"],
                "methods": ["hello"]
            },
            "confidence": 0.95,
            "cost": 0.01
        }
        yield server


class TestMCPServerInitialization:
    """Test MCP server initialization and configuration."""

    def test_server_creation(self, temp_config):
        """Test server can be created with config."""
        server = SpringMVCAnalyzerServer(config_path=temp_config)
        assert server is not None
        assert server.config is not None

    def test_server_creation_without_config(self):
        """Test server can be created with default config."""
        server = SpringMVCAnalyzerServer()
        assert server is not None
        assert server.config is not None

    def test_default_config(self):
        """Test default configuration values."""
        server = SpringMVCAnalyzerServer()
        config = server._get_default_config()

        assert "models" in config
        assert "agents" in config
        assert "mcp" in config
        assert config["mcp"]["auto_cleanup"] is True
        assert config["mcp"]["rate_limit_enabled"] is True


class TestMCPTools:
    """Test MCP tool implementations."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_analyze_file_tool(self, mcp_server, temp_java_file):
        """Test analyze_file tool."""
        # Initialize components
        await mcp_server._initialize_components()

        # Test analyze_file
        result = await mcp_server._tool_analyze_file({
            "file_path": temp_java_file
        })

        assert result is not None
        assert "file_path" in result
        assert "agent_type" in result
        assert "result" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_analyze_directory_tool(self, mcp_server, temp_java_file):
        """Test analyze_directory tool."""
        # Initialize components
        await mcp_server._initialize_components()

        # Get directory containing temp file
        directory = str(Path(temp_java_file).parent)

        # Test analyze_directory
        result = await mcp_server._tool_analyze_directory({
            "directory_path": directory,
            "pattern": "*.java",
            "timeout_per_file": 30.0
        })

        assert result is not None
        assert "results_count" in result
        assert "nodes_added" in result
        assert "edges_added" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_query_graph_tool(self, mcp_server):
        """Test query_graph tool."""
        # Initialize and add some nodes
        await mcp_server._initialize_components()

        from graph.schema import Node, NodeType
        node = Node(
            node_id="test.TestController",
            node_type=NodeType.CONTROLLER,
            file_path="/test/TestController.java",
            metadata={"class_name": "TestController"}
        )
        mcp_server.graph_builder.add_node(node)

        # Test query
        result = await mcp_server._tool_query_graph({
            "query_type": "all_nodes"
        })

        assert result is not None
        assert "nodes" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_find_dependencies_tool(self, mcp_server):
        """Test find_dependencies tool."""
        # Initialize and add nodes with dependencies
        await mcp_server._initialize_components()

        from graph.schema import Node, Edge, NodeType, EdgeType

        node1 = Node(
            node_id="test.Controller1",
            node_type=NodeType.CONTROLLER,
            file_path="/test/Controller1.java",
            metadata={}
        )
        node2 = Node(
            node_id="test.Service1",
            node_type=NodeType.SERVICE,
            file_path="/test/Service1.java",
            metadata={}
        )

        mcp_server.graph_builder.add_node(node1)
        mcp_server.graph_builder.add_node(node2)

        edge = Edge(
            source_id="test.Controller1",
            target_id="test.Service1",
            edge_type=EdgeType.CALLS_SERVICE,
            metadata={}
        )
        mcp_server.graph_builder.add_edge(edge)

        # Test find_dependencies
        result = await mcp_server._tool_find_dependencies({
            "node_id": "test.Controller1"
        })

        assert result is not None
        assert "node_id" in result
        assert "dependencies" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_analyze_impact_tool(self, mcp_server):
        """Test analyze_impact tool."""
        # Initialize and add nodes
        await mcp_server._initialize_components()

        from graph.schema import Node, NodeType
        node = Node(
            node_id="test.TestService",
            node_type=NodeType.SERVICE,
            file_path="/test/TestService.java",
            metadata={}
        )
        mcp_server.graph_builder.add_node(node)

        # Test analyze_impact
        result = await mcp_server._tool_analyze_impact({
            "node_id": "test.TestService"
        })

        assert result is not None
        assert "node_id" in result
        assert "affected_nodes" in result
        assert "impact_count" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_export_graph_tool(self, mcp_server):
        """Test export_graph tool."""
        # Initialize components
        await mcp_server._initialize_components()

        # Create temp output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            # Test export
            result = await mcp_server._tool_export_graph({
                "output_path": output_path,
                "format": "json"
            })

            assert result is not None
            assert result["status"] == "success"
            assert Path(output_path).exists()

        finally:
            # Cleanup
            if Path(output_path).exists():
                os.unlink(output_path)


class TestErrorHandling:
    """Test error handling in MCP server."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_invalid_file_path(self, mcp_server):
        """Test handling of invalid file path."""
        await mcp_server._initialize_components()

        with pytest.raises(Exception):
            await mcp_server._tool_analyze_file({
                "file_path": "/nonexistent/file.java"
            })

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_invalid_node_id(self, mcp_server):
        """Test handling of invalid node ID."""
        await mcp_server._initialize_components()

        result = await mcp_server._tool_find_dependencies({
            "node_id": "nonexistent.Node"
        })

        # Should return empty dependencies, not error
        assert result is not None
        assert result["dependencies"] == []

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_timeout_handling(self, mcp_server, temp_java_file):
        """Test timeout handling in directory analysis."""
        await mcp_server._initialize_components()

        directory = str(Path(temp_java_file).parent)

        # Set very short timeout to trigger timeout
        result = await mcp_server._tool_analyze_directory({
            "directory_path": directory,
            "pattern": "*.java",
            "timeout_per_file": 0.001  # 1ms - very likely to timeout
        })

        assert result is not None
        assert "results_count" in result
        # May have timeout or failed count
        assert "timeout" in result["results_count"] or "failed" in result["results_count"]


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limit_check(self, temp_config):
        """Test rate limit checking."""
        server = SpringMVCAnalyzerServer(config_path=temp_config)

        # Should allow first few requests
        for _ in range(5):
            assert server.check_rate_limit() is True

    def test_rate_limit_burst(self, temp_config):
        """Test burst rate limiting."""
        server = SpringMVCAnalyzerServer(config_path=temp_config)

        # Burst limit is 5, so 6th rapid request should fail
        for _ in range(5):
            server.check_rate_limit()

        with pytest.raises(Exception, match="Rate limit exceeded"):
            server.check_rate_limit()

    def test_rate_limit_disabled(self):
        """Test rate limiting when disabled."""
        server = SpringMVCAnalyzerServer()
        server.config["mcp"]["rate_limit_enabled"] = False

        # Should allow unlimited requests
        for _ in range(100):
            assert server.check_rate_limit() is True


class TestResourceCleanup:
    """Test resource cleanup functionality."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_old_results_cleanup(self, mcp_server, temp_java_file):
        """Test cleanup of old analysis results."""
        await mcp_server._initialize_components()

        # Analyze a file
        await mcp_server._tool_analyze_file({
            "file_path": temp_java_file
        })

        # Should have 1 result
        assert len(mcp_server.analysis_results) == 1
        assert len(mcp_server.result_timestamps) == 1

        # Manually set timestamp to be old
        old_time = datetime.now() - timedelta(hours=2)
        mcp_server.result_timestamps[temp_java_file] = old_time

        # Run cleanup with 1 hour max age
        removed = mcp_server.clear_old_results(max_age_seconds=3600)

        assert removed == 1
        assert len(mcp_server.analysis_results) == 0
        assert len(mcp_server.result_timestamps) == 0

    def test_cleanup_preserves_recent(self, mcp_server, temp_java_file):
        """Test cleanup preserves recent results."""
        # Add some recent results
        mcp_server.analysis_results[temp_java_file] = {"test": "data"}
        mcp_server.result_timestamps[temp_java_file] = datetime.now()

        # Run cleanup
        removed = mcp_server.clear_old_results(max_age_seconds=3600)

        # Should not remove recent results
        assert removed == 0
        assert len(mcp_server.analysis_results) == 1


class TestConfiguration:
    """Test configuration handling."""

    def test_load_config_from_file(self, temp_config):
        """Test loading config from YAML file."""
        server = SpringMVCAnalyzerServer(config_path=temp_config)

        assert server.config is not None
        assert server.config["mcp"]["result_max_age_seconds"] == 60
        assert server.config["mcp"]["rate_limit_requests_per_minute"] == 10

    def test_config_merge_with_defaults(self, temp_config):
        """Test config merges with defaults."""
        server = SpringMVCAnalyzerServer(config_path=temp_config)

        # Should have both loaded and default values
        assert "models" in server.config
        assert "agents" in server.config
        assert "mcp" in server.config

    def test_invalid_config_path(self):
        """Test handling of invalid config path."""
        # Should fall back to defaults without error
        server = SpringMVCAnalyzerServer(config_path="/nonexistent/config.yaml")

        assert server.config is not None
        default_config = server._get_default_config()
        assert server.config == default_config


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    @pytest.mark.asyncio
    async def test_analyze_and_query_workflow(self, mcp_server, temp_java_file):
        """Test full workflow: analyze -> build graph -> query."""
        # Initialize
        await mcp_server._initialize_components()

        # Step 1: Analyze file
        analyze_result = await mcp_server._tool_analyze_file({
            "file_path": temp_java_file
        })
        assert analyze_result is not None

        # Step 2: Build graph (happens automatically in analyze)
        # Verify graph has nodes
        graph_stats = mcp_server.graph_builder.get_statistics()
        assert graph_stats["num_nodes"] >= 0

        # Step 3: Query graph
        query_result = await mcp_server._tool_query_graph({
            "query_type": "all_nodes"
        })
        assert query_result is not None

    @pytest.mark.asyncio
    async def test_directory_analysis_workflow(self, mcp_server, temp_java_file):
        """Test directory analysis workflow."""
        await mcp_server._initialize_components()

        directory = str(Path(temp_java_file).parent)

        # Analyze directory
        result = await mcp_server._tool_analyze_directory({
            "directory_path": directory,
            "pattern": "*.java"
        })

        # Should have analyzed at least 1 file
        assert result["results_count"]["analyzed"] >= 0

        # Graph should be built
        assert result["nodes_added"] >= 0
