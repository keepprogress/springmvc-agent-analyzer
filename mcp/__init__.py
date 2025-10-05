"""
MCP (Model Context Protocol) Server for SpringMVC Agent Analyzer.

Provides Claude Code integration through MCP protocol, exposing analysis
tools and resources for interactive code understanding.
"""

from mcp.server import SpringMVCAnalyzerServer

__all__ = ["SpringMVCAnalyzerServer"]
