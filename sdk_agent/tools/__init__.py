"""
SDK Agent Tools Module.

This module contains @tool decorated functions that wrap existing agents
for use in SDK Agent mode. Each tool is automatically registered with the
SpringMVCAnalyzerAgent client.

Available Tools:

Analysis Tools:
- analyze_controller: Analyze Spring Controller files
- analyze_service: Analyze Service layer files
- analyze_mapper: Analyze MyBatis Mapper files
- analyze_jsp: Analyze JSP view files
- analyze_procedure: Analyze Oracle stored procedures
- analyze_directory: Batch analyze files in a directory

Graph Tools:
- build_graph: Build knowledge graph from analysis results
- export_graph: Export graph to visualization format

Query Tools:
- query_graph: Query the knowledge graph
- find_dependencies: Find dependencies of a component
- analyze_impact: Analyze impact of changes
"""

# Import all tools
from sdk_agent.tools.analysis_tools import (
    analyze_controller,
    analyze_jsp,
    analyze_service,
    analyze_mapper,
    analyze_procedure,
    analyze_directory,
    ALL_TOOLS as ANALYSIS_TOOLS,
    ALL_TOOL_META as ANALYSIS_TOOL_META,
)

from sdk_agent.tools.graph_tools import (
    build_graph,
    export_graph,
    ALL_TOOLS as GRAPH_TOOLS,
    ALL_TOOL_META as GRAPH_TOOL_META,
)

from sdk_agent.tools.query_tools import (
    query_graph,
    find_dependencies,
    analyze_impact,
    ALL_TOOLS as QUERY_TOOLS,
    ALL_TOOL_META as QUERY_TOOL_META,
)

# Combine all tools
ALL_TOOLS = ANALYSIS_TOOLS + GRAPH_TOOLS + QUERY_TOOLS
ALL_TOOL_META = ANALYSIS_TOOL_META + GRAPH_TOOL_META + QUERY_TOOL_META

# Tool categories for permissions
READ_ONLY_TOOLS = [
    analyze_controller,
    analyze_jsp,
    analyze_service,
    analyze_mapper,
    analyze_procedure,
    analyze_directory,
    query_graph,
    find_dependencies,
    analyze_impact,
]

EDIT_TOOLS = [
    build_graph,
    export_graph,
]

__all__ = [
    # Analysis tools
    "analyze_controller",
    "analyze_jsp",
    "analyze_service",
    "analyze_mapper",
    "analyze_procedure",
    "analyze_directory",
    # Graph tools
    "build_graph",
    "export_graph",
    # Query tools
    "query_graph",
    "find_dependencies",
    "analyze_impact",
    # Collections
    "ALL_TOOLS",
    "ALL_TOOL_META",
    "READ_ONLY_TOOLS",
    "EDIT_TOOLS",
    "ANALYSIS_TOOLS",
    "GRAPH_TOOLS",
    "QUERY_TOOLS",
]
