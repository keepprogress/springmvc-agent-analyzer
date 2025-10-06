"""
MCP Server Factory for SDK Agent Tools.

Creates an in-process MCP server that exposes all SpringMVC Analyzer tools
to the Claude Agent SDK.
"""

from claude_agent_sdk import create_sdk_mcp_server
import logging

from sdk_agent.sdk_tools import ALL_SDK_TOOLS

logger = logging.getLogger("sdk_agent.mcp_factory")


def create_analyzer_mcp_server(
    name: str = "springmvc-analyzer",
    version: str = "1.0.0"
):
    """
    Create an SDK MCP server with all analyzer tools.

    Args:
        name: Server name
        version: Server version

    Returns:
        SDK MCP server instance
    """
    logger.info(f"Creating MCP server: {name} v{version} with {len(ALL_SDK_TOOLS)} tools")

    server = create_sdk_mcp_server(
        name=name,
        version=version,
        tools=ALL_SDK_TOOLS
    )

    logger.info(f"MCP server created successfully")
    return server
