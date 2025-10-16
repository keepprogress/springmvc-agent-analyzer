#!/usr/bin/env python3
"""
CLI entry point for SpringMVC Analyzer MCP Server.

This script starts the MCP server that can be integrated with Claude Code
or other MCP clients.

Usage:
    python run_mcp_server.py

    Or make it executable and run directly:
    chmod +x run_mcp_server.py
    ./run_mcp_server.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from analyzer_mcp.server import SpringMVCAnalyzerServer


def setup_logging():
    """Configure logging for the MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),  # MCP uses stderr for logs
            logging.FileHandler("mcp_server.log")
        ]
    )


async def main():
    """Main entry point."""
    setup_logging()
    logger = logging.getLogger("run_mcp_server")

    logger.info("=" * 60)
    logger.info("SpringMVC Agent Analyzer - MCP Server")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Starting MCP server...")
    logger.info("Server will communicate via stdio (stdin/stdout)")
    logger.info("Logs are written to stderr and mcp_server.log")
    logger.info("")

    try:
        server = SpringMVCAnalyzerServer()
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
