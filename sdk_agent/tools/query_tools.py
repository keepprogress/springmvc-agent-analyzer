"""
Query Tools for SDK Agent Mode.

This module implements tools for querying the knowledge graph to find
dependencies, analyze impact, and explore the codebase structure.

Tools:
- query_graph: Query graph by node type, name, or metadata
- find_dependencies: Find all dependencies of a component
- analyze_impact: Analyze impact of changes to a component

Note: @tool decorators will be added in Phase 5 when SDK is integrated.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

from sdk_agent.agent_factory import get_graph_builder
from sdk_agent.utils import expand_file_path, format_tool_result
from sdk_agent.constants import VALID_FILE_TYPES, FILE_TYPE_UNKNOWN
from sdk_agent.exceptions import SDKAgentError

logger = logging.getLogger("sdk_agent.tools.query")


QUERY_GRAPH_META = {
    "name": "query_graph",
    "description": (
        "Query the knowledge graph to find nodes matching criteria.\n"
        "\n"
        "Search by:\n"
        "- Node type (controller, service, mapper, jsp, procedure)\n"
        "- Node name (class name, file name)\n"
        "- Metadata (package, annotations, etc.)\n"
        "- File path patterns\n"
        "\n"
        "Returns matching nodes with their metadata and connections."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "node_type": {
                "type": "string",
                "description": "Filter by node type",
                "enum": ["controller", "service", "mapper", "jsp", "procedure", "model"],
                "default": None
            },
            "name_pattern": {
                "type": "string",
                "description": "Search by name (supports * wildcards)",
                "default": None
            },
            "metadata_filters": {
                "type": "object",
                "description": "Filter by metadata key-value pairs",
                "default": {}
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 50
            }
        }
    }
}


async def query_graph(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Query the knowledge graph.

    Args:
        args: Dictionary with keys:
            - node_type (str, optional): Filter by type
            - name_pattern (str, optional): Search by name pattern
            - metadata_filters (dict, optional): Metadata filters
            - limit (int): Max results (default: 50)

    Returns:
        Dict with matching nodes
    """
    node_type = args.get("node_type")
    name_pattern = args.get("name_pattern")
    metadata_filters = args.get("metadata_filters", {})
    limit = args.get("limit", 50)

    logger.info(f"Querying graph: type={node_type}, pattern={name_pattern}")

    try:
        graph_builder = get_graph_builder()

        # Check graph has data
        stats = graph_builder.get_stats()
        if stats["total_nodes"] == 0:
            return format_tool_result(
                {"error": "Graph is empty - run build_graph first"},
                format_type="json",
                is_error=True
            )

        results = []

        # Query by type
        if node_type:
            nodes = graph_builder.query_by_type(node_type)

            for node in nodes:
                # Apply name filter if provided
                if name_pattern and not _matches_pattern(node.name, name_pattern):
                    continue

                # Apply metadata filters
                if metadata_filters and not _matches_metadata(node, metadata_filters):
                    continue

                results.append({
                    "id": node.id,
                    "type": node.type.value,
                    "name": node.name,
                    "file_path": node.file_path,
                    "metadata": node.metadata
                })

                if len(results) >= limit:
                    break

        # Query by metadata if no type specified
        elif metadata_filters:
            nodes = graph_builder.query_by_metadata(metadata_filters)

            for node in nodes:
                if name_pattern and not _matches_pattern(node.name, name_pattern):
                    continue

                results.append({
                    "id": node.id,
                    "type": node.type.value,
                    "name": node.name,
                    "file_path": node.file_path,
                    "metadata": node.metadata
                })

                if len(results) >= limit:
                    break

        # Query all nodes if no filters
        else:
            all_nodes = graph_builder.nodes.values()

            for node in all_nodes:
                if name_pattern and not _matches_pattern(node.name, name_pattern):
                    continue

                results.append({
                    "id": node.id,
                    "type": node.type.value,
                    "name": node.name,
                    "file_path": node.file_path,
                    "metadata": node.metadata
                })

                if len(results) >= limit:
                    break

        # Format summary
        summary_lines = [
            "Graph Query Results",
            "=" * 60,
            f"Filters: type={node_type or 'any'}, pattern={name_pattern or 'any'}",
            f"Results Found: {len(results)}",
            ""
        ]

        if results:
            summary_lines.append("Matches:")
            for i, result in enumerate(results[:20], 1):  # Show first 20
                summary_lines.append(
                    f"{i}. [{result['type']}] {result['name']} - {result['file_path']}"
                )

            if len(results) > 20:
                summary_lines.append(f"... and {len(results) - 20} more")

        summary = "\n".join(summary_lines)

        return {
            "content": [{"type": "text", "text": summary}],
            "data": {
                "results": results,
                "total_found": len(results),
                "filters": {
                    "node_type": node_type,
                    "name_pattern": name_pattern,
                    "metadata_filters": metadata_filters
                }
            },
            "is_error": False
        }

    except Exception as e:
        logger.error(f"Error querying graph: {e}", exc_info=True)
        return format_tool_result(
            {"error": str(e)},
            format_type="json",
            is_error=True
        )


FIND_DEPENDENCIES_META = {
    "name": "find_dependencies",
    "description": (
        "Find all dependencies of a component.\n"
        "\n"
        "Discovers:\n"
        "- Direct dependencies (what this component uses)\n"
        "- Transitive dependencies (entire dependency tree)\n"
        "- Dependency paths (how components are connected)\n"
        "\n"
        "Useful for:\n"
        "- Understanding component dependencies\n"
        "- Finding circular dependencies\n"
        "- Planning refactoring"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "node_id": {
                "type": "string",
                "description": "Node ID or file path to analyze",
                "default": None
            },
            "node_name": {
                "type": "string",
                "description": "Node name (if node_id not provided)",
                "default": None
            },
            "max_depth": {
                "type": "integer",
                "description": "Maximum dependency depth to traverse (0 = all)",
                "default": 0
            },
            "include_paths": {
                "type": "boolean",
                "description": "Include dependency paths",
                "default": True
            }
        }
    }
}


async def find_dependencies(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Find all dependencies of a component.

    Args:
        args: Dictionary with keys:
            - node_id (str, optional): Node ID or file path
            - node_name (str, optional): Node name
            - max_depth (int): Max depth (default: 0 = all)
            - include_paths (bool): Include paths (default: True)

    Returns:
        Dict with dependency information
    """
    node_id = args.get("node_id")
    node_name = args.get("node_name")
    max_depth = args.get("max_depth", 0)
    include_paths = args.get("include_paths", True)

    logger.info(f"Finding dependencies: id={node_id}, name={node_name}")

    try:
        graph_builder = get_graph_builder()

        # Find node
        node = None
        if node_id:
            # Try as node ID first
            node = graph_builder.get_node(node_id)

            # Try as file path if not found
            if node is None:
                node = graph_builder.get_node_by_file_path(node_id)

        elif node_name:
            # Search by name
            for n in graph_builder.nodes.values():
                if n.name == node_name:
                    node = n
                    break

        if node is None:
            return format_tool_result(
                {"error": f"Node not found: {node_id or node_name}"},
                format_type="json",
                is_error=True
            )

        # Find all dependencies
        dependencies = graph_builder.find_all_dependencies(
            node.id,
            max_depth=max_depth if max_depth > 0 else None
        )

        # Get dependency paths if requested
        paths = []
        if include_paths and dependencies:
            for dep_id in list(dependencies)[:10]:  # Limit to 10 paths
                path = graph_builder.find_shortest_path(node.id, dep_id)
                if path:
                    paths.append({
                        "target": dep_id,
                        "path": path,
                        "length": len(path) - 1
                    })

        # Get details for each dependency
        dep_details = []
        for dep_id in dependencies:
            dep_node = graph_builder.get_node(dep_id)
            if dep_node:
                dep_details.append({
                    "id": dep_node.id,
                    "type": dep_node.type.value,
                    "name": dep_node.name,
                    "file_path": dep_node.file_path
                })

        # Format summary
        summary_lines = [
            f"Dependencies of: {node.name} ({node.type.value})",
            "=" * 60,
            f"File: {node.file_path}",
            f"Total Dependencies: {len(dependencies)}",
            ""
        ]

        if dep_details:
            # Group by type
            by_type = {}
            for dep in dep_details:
                dep_type = dep["type"]
                if dep_type not in by_type:
                    by_type[dep_type] = []
                by_type[dep_type].append(dep)

            summary_lines.append("Dependencies by Type:")
            for dep_type, deps in by_type.items():
                summary_lines.append(f"  {dep_type}: {len(deps)}")

            summary_lines.append("")
            summary_lines.append("Direct Dependencies:")
            for dep in dep_details[:15]:  # Show first 15
                summary_lines.append(f"  - [{dep['type']}] {dep['name']}")

        if paths:
            summary_lines.append("")
            summary_lines.append("Sample Dependency Paths:")
            for path_info in paths[:5]:
                path_str = " → ".join([graph_builder.get_node(nid).name for nid in path_info["path"]])
                summary_lines.append(f"  {path_str}")

        summary = "\n".join(summary_lines)

        return {
            "content": [{"type": "text", "text": summary}],
            "data": {
                "node": {
                    "id": node.id,
                    "type": node.type.value,
                    "name": node.name,
                    "file_path": node.file_path
                },
                "dependencies": dep_details,
                "total_count": len(dependencies),
                "paths": paths
            },
            "is_error": False
        }

    except Exception as e:
        logger.error(f"Error finding dependencies: {e}", exc_info=True)
        return format_tool_result(
            {"error": str(e)},
            format_type="json",
            is_error=True
        )


ANALYZE_IMPACT_META = {
    "name": "analyze_impact",
    "description": (
        "Analyze the impact of changes to a component.\n"
        "\n"
        "Discovers:\n"
        "- All components that depend on this one (dependents)\n"
        "- Impact radius (how many components affected)\n"
        "- Critical paths (important dependencies)\n"
        "\n"
        "Useful for:\n"
        "- Change impact analysis\n"
        "- Risk assessment before refactoring\n"
        "- Understanding component importance"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "node_id": {
                "type": "string",
                "description": "Node ID or file path to analyze",
                "default": None
            },
            "node_name": {
                "type": "string",
                "description": "Node name (if node_id not provided)",
                "default": None
            },
            "max_depth": {
                "type": "integer",
                "description": "Maximum depth to analyze (0 = all)",
                "default": 0
            }
        }
    }
}


async def analyze_impact(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze impact of changes to a component.

    Args:
        args: Dictionary with keys:
            - node_id (str, optional): Node ID or file path
            - node_name (str, optional): Node name
            - max_depth (int): Max depth (default: 0 = all)

    Returns:
        Dict with impact analysis
    """
    node_id = args.get("node_id")
    node_name = args.get("node_name")
    max_depth = args.get("max_depth", 0)

    logger.info(f"Analyzing impact: id={node_id}, name={node_name}")

    try:
        graph_builder = get_graph_builder()

        # Find node (same logic as find_dependencies)
        node = None
        if node_id:
            node = graph_builder.get_node(node_id)
            if node is None:
                node = graph_builder.get_node_by_file_path(node_id)
        elif node_name:
            for n in graph_builder.nodes.values():
                if n.name == node_name:
                    node = n
                    break

        if node is None:
            return format_tool_result(
                {"error": f"Node not found: {node_id or node_name}"},
                format_type="json",
                is_error=True
            )

        # Analyze impact using GraphBuilder's method
        impact_result = graph_builder.analyze_impact(
            node.id,
            max_depth=max_depth if max_depth > 0 else None
        )

        # Get details for affected components
        affected_details = []
        for affected_id in impact_result.get("affected_nodes", []):
            affected_node = graph_builder.get_node(affected_id)
            if affected_node:
                affected_details.append({
                    "id": affected_node.id,
                    "type": affected_node.type.value,
                    "name": affected_node.name,
                    "file_path": affected_node.file_path
                })

        # Format summary
        impact_level = impact_result.get("impact_level", "unknown")
        risk_score = impact_result.get("risk_score", 0.0)

        summary_lines = [
            f"Impact Analysis: {node.name} ({node.type.value})",
            "=" * 60,
            f"File: {node.file_path}",
            "",
            f"Impact Level: {impact_level.upper()}",
            f"Risk Score: {risk_score:.2f}/1.00",
            f"Affected Components: {len(affected_details)}",
            ""
        ]

        if affected_details:
            # Group by type
            by_type = {}
            for affected in affected_details:
                aff_type = affected["type"]
                if aff_type not in by_type:
                    by_type[aff_type] = []
                by_type[aff_type].append(affected)

            summary_lines.append("Affected Components by Type:")
            for aff_type, components in by_type.items():
                summary_lines.append(f"  {aff_type}: {len(components)}")

            summary_lines.append("")
            summary_lines.append("Direct Dependents:")
            for affected in affected_details[:15]:  # Show first 15
                summary_lines.append(f"  - [{affected['type']}] {affected['name']}")

        summary_lines.append("")
        summary_lines.append("Recommendation:")
        if impact_level == "high" or risk_score > 0.7:
            summary_lines.append("  ⚠️  HIGH IMPACT - Review all affected components carefully")
            summary_lines.append("  ⚠️  Consider creating comprehensive tests before changes")
        elif impact_level == "medium" or risk_score > 0.4:
            summary_lines.append("  ⚡ MEDIUM IMPACT - Review key affected components")
            summary_lines.append("  ⚡ Update related documentation")
        else:
            summary_lines.append("  ✓ LOW IMPACT - Changes should be relatively safe")

        summary = "\n".join(summary_lines)

        return {
            "content": [{"type": "text", "text": summary}],
            "data": {
                "node": {
                    "id": node.id,
                    "type": node.type.value,
                    "name": node.name,
                    "file_path": node.file_path
                },
                "impact_level": impact_level,
                "risk_score": risk_score,
                "affected_components": affected_details,
                "total_affected": len(affected_details),
                "raw_result": impact_result
            },
            "is_error": False
        }

    except Exception as e:
        logger.error(f"Error analyzing impact: {e}", exc_info=True)
        return format_tool_result(
            {"error": str(e)},
            format_type="json",
            is_error=True
        )


def _matches_pattern(text: str, pattern: str) -> bool:
    """Check if text matches pattern (supports * wildcards)."""
    import re
    # Convert wildcard pattern to regex
    regex_pattern = pattern.replace("*", ".*")
    return bool(re.match(f"^{regex_pattern}$", text, re.IGNORECASE))


def _matches_metadata(node, filters: Dict[str, Any]) -> bool:
    """Check if node metadata matches all filters."""
    for key, value in filters.items():
        if key not in node.metadata:
            return False
        if node.metadata[key] != value:
            return False
    return True


# Export all tools and metadata
ALL_TOOLS = [
    query_graph,
    find_dependencies,
    analyze_impact
]

ALL_TOOL_META = [
    QUERY_GRAPH_META,
    FIND_DEPENDENCIES_META,
    ANALYZE_IMPACT_META
]
