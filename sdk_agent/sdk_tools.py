"""
SDK Tool Wrappers for Claude Agent SDK.

This module wraps our existing tool functions with @tool decorators
from claude-agent-sdk to enable SDK integration.

All tools are exposed as MCP tools through create_sdk_mcp_server().
"""

from claude_agent_sdk import tool

# Import our existing tool functions and metadata
from sdk_agent.tools.analysis_tools import (
    analyze_controller as _analyze_controller,
    analyze_jsp as _analyze_jsp,
    analyze_service as _analyze_service,
    analyze_mapper as _analyze_mapper,
    analyze_procedure as _analyze_procedure,
    analyze_directory as _analyze_directory,
    ANALYZE_CONTROLLER_META,
    ANALYZE_JSP_META,
    ANALYZE_SERVICE_META,
    ANALYZE_MAPPER_META,
    ANALYZE_PROCEDURE_META,
    ANALYZE_DIRECTORY_META,
)

from sdk_agent.tools.graph_tools import (
    build_graph as _build_graph,
    export_graph as _export_graph,
    BUILD_GRAPH_META,
    EXPORT_GRAPH_META,
)

from sdk_agent.tools.query_tools import (
    query_graph as _query_graph,
    find_dependencies as _find_dependencies,
    analyze_impact as _analyze_impact,
    QUERY_GRAPH_META,
    FIND_DEPENDENCIES_META,
    ANALYZE_IMPACT_META,
)


# Wrap analysis tools with @tool decorator
@tool(
    ANALYZE_CONTROLLER_META["name"],
    ANALYZE_CONTROLLER_META["description"],
    ANALYZE_CONTROLLER_META["input_schema"]["properties"]
)
async def analyze_controller(args):
    """Analyze Spring MVC Controller - SDK wrapper."""
    return await _analyze_controller(args)


@tool(
    ANALYZE_JSP_META["name"],
    ANALYZE_JSP_META["description"],
    ANALYZE_JSP_META["input_schema"]["properties"]
)
async def analyze_jsp(args):
    """Analyze JSP view - SDK wrapper."""
    return await _analyze_jsp(args)


@tool(
    ANALYZE_SERVICE_META["name"],
    ANALYZE_SERVICE_META["description"],
    ANALYZE_SERVICE_META["input_schema"]["properties"]
)
async def analyze_service(args):
    """Analyze Service layer - SDK wrapper."""
    return await _analyze_service(args)


@tool(
    ANALYZE_MAPPER_META["name"],
    ANALYZE_MAPPER_META["description"],
    ANALYZE_MAPPER_META["input_schema"]["properties"]
)
async def analyze_mapper(args):
    """Analyze MyBatis Mapper - SDK wrapper."""
    return await _analyze_mapper(args)


@tool(
    ANALYZE_PROCEDURE_META["name"],
    ANALYZE_PROCEDURE_META["description"],
    ANALYZE_PROCEDURE_META["input_schema"]["properties"]
)
async def analyze_procedure(args):
    """Analyze stored procedure - SDK wrapper."""
    return await _analyze_procedure(args)


@tool(
    ANALYZE_DIRECTORY_META["name"],
    ANALYZE_DIRECTORY_META["description"],
    ANALYZE_DIRECTORY_META["input_schema"]["properties"]
)
async def analyze_directory(args):
    """Batch analyze directory - SDK wrapper."""
    return await _analyze_directory(args)


# Wrap graph tools
@tool(
    BUILD_GRAPH_META["name"],
    BUILD_GRAPH_META["description"],
    BUILD_GRAPH_META["input_schema"]["properties"]
)
async def build_graph(args):
    """Build knowledge graph - SDK wrapper."""
    return await _build_graph(args)


@tool(
    EXPORT_GRAPH_META["name"],
    EXPORT_GRAPH_META["description"],
    EXPORT_GRAPH_META["input_schema"]["properties"]
)
async def export_graph(args):
    """Export graph - SDK wrapper."""
    return await _export_graph(args)


# Wrap query tools
@tool(
    QUERY_GRAPH_META["name"],
    QUERY_GRAPH_META["description"],
    QUERY_GRAPH_META["input_schema"]["properties"]
)
async def query_graph(args):
    """Query knowledge graph - SDK wrapper."""
    return await _query_graph(args)


@tool(
    FIND_DEPENDENCIES_META["name"],
    FIND_DEPENDENCIES_META["description"],
    FIND_DEPENDENCIES_META["input_schema"]["properties"]
)
async def find_dependencies(args):
    """Find component dependencies - SDK wrapper."""
    return await _find_dependencies(args)


@tool(
    ANALYZE_IMPACT_META["name"],
    ANALYZE_IMPACT_META["description"],
    ANALYZE_IMPACT_META["input_schema"]["properties"]
)
async def analyze_impact(args):
    """Analyze change impact - SDK wrapper."""
    return await _analyze_impact(args)


# Export all SDK-wrapped tools
ALL_SDK_TOOLS = [
    analyze_controller,
    analyze_jsp,
    analyze_service,
    analyze_mapper,
    analyze_procedure,
    analyze_directory,
    build_graph,
    export_graph,
    query_graph,
    find_dependencies,
    analyze_impact,
]
