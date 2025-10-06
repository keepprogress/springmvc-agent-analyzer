"""
MCP Server Factory for SDK Agent Tools.

Creates an in-process MCP server that exposes all SpringMVC Analyzer tools
to the Claude Agent SDK.
"""

import logging

from sdk_agent.sdk_imports import import_sdk

# Import SDK components with error handling
_, create_sdk_mcp_server, _, _ = import_sdk()

from sdk_agent.sdk_tools import ALL_SDK_TOOLS
from sdk_agent.constants import DEFAULT_MCP_SERVER_NAME, DEFAULT_MCP_SERVER_VERSION

logger = logging.getLogger("sdk_agent.mcp_factory")


def create_analyzer_mcp_server(
    name: str = DEFAULT_MCP_SERVER_NAME,
    version: str = DEFAULT_MCP_SERVER_VERSION
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
