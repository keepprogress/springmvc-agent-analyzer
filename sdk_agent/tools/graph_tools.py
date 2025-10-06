"""
Graph Tools for SDK Agent Mode.

This module implements tools for building and exporting knowledge graphs
from analysis results.

Tools:
- build_graph: Build knowledge graph from analysis results
- export_graph: Export graph to visualization format (D3, Cytoscape, DOT, GraphML)

Note: @tool decorators will be added in Phase 5 when SDK is integrated.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

from sdk_agent.agent_factory import get_graph_builder
from sdk_agent.utils import expand_file_path, format_tool_result
from sdk_agent.constants import GRAPH_EXPORT_FORMATS
from sdk_agent.exceptions import SDKAgentError

logger = logging.getLogger("sdk_agent.tools.graph")


BUILD_GRAPH_META = {
    "name": "build_graph",
    "description": (
        "Build knowledge graph from analysis results.\n"
        "Constructs a directed graph connecting all analyzed components:\n"
        "- Controllers → Services → Mappers → Procedures\n"
        "- Controllers → JSPs (view rendering)\n"
        "- Services → Models (data flow)\n"
        "\n"
        "The graph enables:\n"
        "- Dependency tracking\n"
        "- Impact analysis\n"
        "- Architecture visualization\n"
        "- Code navigation"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "analysis_results": {
                "type": "array",
                "description": "List of analysis results from analyze_* tools",
                "items": {"type": "object"}
            },
            "clear_existing": {
                "type": "boolean",
                "description": "Clear existing graph before building (default: false)",
                "default": False
            }
        },
        "required": ["analysis_results"]
    }
}


async def build_graph(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build knowledge graph from analysis results.

    Args:
        args: Dictionary with keys:
            - analysis_results (List[Dict]): Analysis results to add to graph
            - clear_existing (bool): Clear existing graph (default: False)

    Returns:
        Dict with graph statistics
    """
    analysis_results = args["analysis_results"]
    clear_existing = args.get("clear_existing", False)

    logger.info(f"Building graph from {len(analysis_results)} analysis results")

    try:
        graph_builder = get_graph_builder()

        # Clear graph if requested
        if clear_existing:
            logger.info("Clearing existing graph")
            # Create new graph builder (reset)
            # Note: This requires factory support for reset
            # For now, we just log a warning
            logger.warning("Graph clearing not yet implemented - adding to existing graph")

        # Build graph from results
        nodes_added = 0
        edges_added = 0

        for result in analysis_results:
            # Each result should have "data" field with analysis
            if "data" not in result:
                logger.warning(f"Skipping result without 'data' field: {result}")
                continue

            data = result["data"]

            # Pass to GraphBuilder's build_from_analysis_results
            # This method expects a dict with file_path and analysis structure
            build_result = graph_builder.build_from_analysis_results([data])

            nodes_added += build_result.get("nodes_added", 0)
            edges_added += build_result.get("edges_added", 0)

        # Get graph stats
        stats = graph_builder.get_stats()

        summary_lines = [
            "Graph Build Complete",
            "=" * 60,
            f"Results Processed: {len(analysis_results)}",
            f"Nodes Added: {nodes_added}",
            f"Edges Added: {edges_added}",
            "",
            "Graph Statistics:",
            f"Total Nodes: {stats['total_nodes']}",
            f"Total Edges: {stats['total_edges']}",
            "",
            "Node Breakdown:"
        ]

        for node_type, count in stats.get("nodes_by_type", {}).items():
            summary_lines.append(f"  - {node_type}: {count}")

        summary = "\n".join(summary_lines)

        return {
            "content": [{"type": "text", "text": summary}],
            "data": {
                "nodes_added": nodes_added,
                "edges_added": edges_added,
                "stats": stats
            },
            "is_error": False
        }

    except Exception as e:
        logger.error(f"Error building graph: {e}", exc_info=True)
        return format_tool_result(
            {"error": str(e)},
            format_type="json",
            is_error=True
        )


EXPORT_GRAPH_META = {
    "name": "export_graph",
    "description": (
        "Export knowledge graph to visualization format.\n"
        "\n"
        "Supported formats:\n"
        "- d3: D3.js force-directed graph (JSON)\n"
        "- cytoscape: Cytoscape.js format (JSON)\n"
        "- dot: GraphViz DOT format (text)\n"
        "- graphml: GraphML XML format\n"
        "\n"
        "Export includes:\n"
        "- All nodes with metadata (type, name, file_path)\n"
        "- All edges with relationship types\n"
        "- Proper formatting for visualization libraries"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "output_path": {
                "type": "string",
                "description": "Path to save exported graph"
            },
            "format": {
                "type": "string",
                "description": "Export format: d3, cytoscape, dot, or graphml",
                "enum": ["d3", "cytoscape", "dot", "graphml"],
                "default": "d3"
            },
            "project_root": {
                "type": "string",
                "description": "Project root directory",
                "default": None
            }
        },
        "required": ["output_path"]
    }
}


async def export_graph(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Export knowledge graph to visualization format.

    Args:
        args: Dictionary with keys:
            - output_path (str): Path to save exported graph
            - format (str): Export format (d3, cytoscape, dot, graphml)
            - project_root (str, optional): Project root directory

    Returns:
        Dict with export confirmation
    """
    output_path = args["output_path"]
    export_format = args.get("format", "d3").lower()
    project_root = args.get("project_root")

    logger.info(f"Exporting graph to {output_path} (format: {export_format})")

    try:
        # Validate format
        if export_format not in GRAPH_EXPORT_FORMATS:
            return format_tool_result(
                {
                    "error": f"Invalid format: {export_format}",
                    "valid_formats": GRAPH_EXPORT_FORMATS
                },
                format_type="json",
                is_error=True
            )

        # Expand output path
        full_path = expand_file_path(output_path, project_root)

        # Ensure parent directory exists
        Path(full_path).parent.mkdir(parents=True, exist_ok=True)

        # Get graph builder
        graph_builder = get_graph_builder()

        # Check graph has data
        stats = graph_builder.get_stats()
        if stats["total_nodes"] == 0:
            return format_tool_result(
                {"error": "Graph is empty - run build_graph first"},
                format_type="json",
                is_error=True
            )

        # Export based on format
        if export_format == "d3":
            graph_builder.export_d3_json(full_path)
        elif export_format == "cytoscape":
            graph_builder.export_cytoscape_json(full_path)
        elif export_format == "dot":
            graph_builder.export_dot(full_path)
        elif export_format == "graphml":
            graph_builder.save_graph(full_path, format="graphml")

        # Get file size
        file_size = Path(full_path).stat().st_size

        summary_lines = [
            "Graph Export Complete",
            "=" * 60,
            f"Format: {export_format.upper()}",
            f"Output: {full_path}",
            f"File Size: {file_size:,} bytes",
            "",
            "Graph Contents:",
            f"Nodes: {stats['total_nodes']}",
            f"Edges: {stats['total_edges']}"
        ]

        summary = "\n".join(summary_lines)

        return {
            "content": [{"type": "text", "text": summary}],
            "data": {
                "output_path": full_path,
                "format": export_format,
                "file_size": file_size,
                "stats": stats
            },
            "is_error": False
        }

    except Exception as e:
        logger.error(f"Error exporting graph: {e}", exc_info=True)
        return format_tool_result(
            {"error": str(e), "output_path": output_path},
            format_type="json",
            is_error=True
        )


# Export all tools and metadata
ALL_TOOLS = [
    build_graph,
    export_graph
]

ALL_TOOL_META = [
    BUILD_GRAPH_META,
    EXPORT_GRAPH_META
]
