"""
SDK Agent Tools Module.

This module contains @tool decorated functions that wrap existing agents
for use in SDK Agent mode. Each tool is automatically registered with the
SpringMVCAnalyzerAgent client.

Available Tools:
- analyze_controller: Analyze Spring Controller files
- analyze_service: Analyze Service layer files
- analyze_mapper: Analyze MyBatis Mapper files
- analyze_jsp: Analyze JSP view files
- analyze_procedure: Analyze Oracle stored procedures
- build_graph: Build knowledge graph from analysis results
- query_graph: Query the knowledge graph
- find_dependencies: Find dependencies of a component
- analyze_impact: Analyze impact of changes
- export_graph: Export graph to visualization format
- list_files: List files in project
- read_file: Read file contents
"""

# Tools will be imported and registered automatically when used
__all__ = [
    "analyze_controller",
    "analyze_service",
    "analyze_mapper",
    "analyze_jsp",
    "analyze_procedure",
    "build_graph",
    "query_graph",
    "find_dependencies",
    "analyze_impact",
    "export_graph",
    "list_files",
    "read_file",
]
