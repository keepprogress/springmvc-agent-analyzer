"""
MCP Server implementation for SpringMVC Agent Analyzer.

This module implements an MCP (Model Context Protocol) server that exposes
the analyzer's capabilities as tools and resources for Claude Code integration.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

# MCP SDK imports
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Project imports (will be loaded dynamically to avoid circular imports)
from core.model_router import ModelRouter
from core.prompt_manager import PromptManager
from core.cost_tracker import CostTracker
from core.cache_manager import CacheManager
from graph.graph_builder import GraphBuilder
from agents.controller_agent import ControllerAgent
from agents.jsp_agent import JSPAgent
from agents.service_agent import ServiceAgent
from agents.mapper_agent import MapperAgent
from agents.procedure_agent import ProcedureAgent


class SpringMVCAnalyzerServer:
    """
    MCP Server for SpringMVC Agent Analyzer.

    Exposes analysis capabilities through MCP protocol:
    - Tools: analyze_file, analyze_directory, query_graph, etc.
    - Resources: analysis results, graph data
    - Prompts: Analysis templates

    Attributes:
        server: MCP Server instance
        config: Configuration dictionary
        agents: Dictionary of initialized agents
        graph_builder: GraphBuilder instance
        logger: Logger instance
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the MCP server.

        Args:
            config_path: Path to configuration file
        """
        self.logger = logging.getLogger("mcp.server")
        self.server = Server("springmvc-analyzer")

        # Load configuration
        self.config = self._load_config(config_path)

        # Initialize core components
        self.model_router = None
        self.prompt_manager = None
        self.cost_tracker = None
        self.cache_manager = None
        self.graph_builder = None
        self.agents = {}

        # Analysis state
        self.analysis_results = {}  # file_path -> result
        self.current_project = None

        # Register handlers
        self._register_handlers()

        self.logger.info("SpringMVC Analyzer MCP Server initialized")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        import yaml

        path = Path(config_path)
        if not path.exists():
            self.logger.warning(f"Config file not found: {config_path}, using defaults")
            return self._get_default_config()

        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "models": {
                "haiku": "claude-3-5-haiku-20241022",
                "sonnet": "claude-3-5-sonnet-20241022",
                "opus": "claude-opus-4-20250514"
            },
            "agents": {
                "min_confidence": 0.7
            }
        }

    async def _initialize_components(self):
        """Initialize core components lazily."""
        if self.model_router is not None:
            return  # Already initialized

        self.logger.info("Initializing core components...")

        # Initialize core services
        self.model_router = ModelRouter(self.config)
        self.prompt_manager = PromptManager()
        self.cost_tracker = CostTracker()
        self.cache_manager = CacheManager()
        self.graph_builder = GraphBuilder()

        # Initialize agents
        self.agents = {
            "controller": ControllerAgent(
                self.model_router,
                self.prompt_manager,
                self.cost_tracker,
                self.cache_manager,
                self.config
            ),
            "jsp": JSPAgent(
                self.model_router,
                self.prompt_manager,
                self.cost_tracker,
                self.cache_manager,
                self.config
            ),
            "service": ServiceAgent(
                self.model_router,
                self.prompt_manager,
                self.cost_tracker,
                self.cache_manager,
                self.config
            ),
            "mapper": MapperAgent(
                self.model_router,
                self.prompt_manager,
                self.cost_tracker,
                self.cache_manager,
                self.config
            ),
            "procedure": ProcedureAgent(
                self.model_router,
                self.prompt_manager,
                self.cost_tracker,
                self.cache_manager,
                self.config
            )
        }

        self.logger.info("Core components initialized")

    def _register_handlers(self):
        """Register MCP protocol handlers."""

        # Tool handlers
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available MCP tools."""
            return [
                types.Tool(
                    name="analyze_file",
                    description="Analyze a single file with appropriate agent (Controller, JSP, Service, Mapper, or Procedure)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file to analyze"
                            },
                            "agent_type": {
                                "type": "string",
                                "description": "Agent type to use (auto-detected if not specified)",
                                "enum": ["controller", "jsp", "service", "mapper", "procedure", "auto"]
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                types.Tool(
                    name="analyze_directory",
                    description="Analyze all files in a directory and build knowledge graph",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "directory_path": {
                                "type": "string",
                                "description": "Path to directory to analyze"
                            },
                            "pattern": {
                                "type": "string",
                                "description": "File pattern to match (e.g., '**/*.java')"
                            }
                        },
                        "required": ["directory_path"]
                    }
                ),
                types.Tool(
                    name="query_graph",
                    description="Query the knowledge graph for nodes, relationships, or statistics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query_type": {
                                "type": "string",
                                "description": "Type of query to perform",
                                "enum": ["stats", "find_node", "neighbors", "paths"]
                            },
                            "node_id": {
                                "type": "string",
                                "description": "Node ID for node-specific queries"
                            },
                            "target_id": {
                                "type": "string",
                                "description": "Target node ID for path queries"
                            }
                        },
                        "required": ["query_type"]
                    }
                ),
                types.Tool(
                    name="find_dependencies",
                    description="Find all dependencies of a node (transitive closure)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node_id": {
                                "type": "string",
                                "description": "Node ID to analyze"
                            },
                            "max_depth": {
                                "type": "number",
                                "description": "Maximum depth to traverse (optional)"
                            }
                        },
                        "required": ["node_id"]
                    }
                ),
                types.Tool(
                    name="analyze_impact",
                    description="Analyze the impact of changing a node (find dependencies and dependents)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node_id": {
                                "type": "string",
                                "description": "Node ID to analyze"
                            },
                            "max_depth": {
                                "type": "number",
                                "description": "Maximum depth to traverse (optional)"
                            }
                        },
                        "required": ["node_id"]
                    }
                ),
                types.Tool(
                    name="export_graph",
                    description="Export knowledge graph to various visualization formats",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "output_path": {
                                "type": "string",
                                "description": "Path to output file"
                            },
                            "format": {
                                "type": "string",
                                "description": "Export format",
                                "enum": ["graphml", "gexf", "json", "dot", "d3", "cytoscape"]
                            }
                        },
                        "required": ["output_path", "format"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict
        ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Handle tool calls."""
            await self._initialize_components()

            try:
                if name == "analyze_file":
                    result = await self._tool_analyze_file(arguments)
                elif name == "analyze_directory":
                    result = await self._tool_analyze_directory(arguments)
                elif name == "query_graph":
                    result = await self._tool_query_graph(arguments)
                elif name == "find_dependencies":
                    result = await self._tool_find_dependencies(arguments)
                elif name == "analyze_impact":
                    result = await self._tool_analyze_impact(arguments)
                elif name == "export_graph":
                    result = await self._tool_export_graph(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")

                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            except Exception as e:
                self.logger.error(f"Error executing tool {name}: {e}", exc_info=True)
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)}, indent=2)
                )]

        # Resource handlers
        @self.server.list_resources()
        async def handle_list_resources() -> List[types.Resource]:
            """List available MCP resources."""
            return [
                types.Resource(
                    uri="analysis://results",
                    name="Analysis Results",
                    description="All file analysis results",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="graph://stats",
                    name="Graph Statistics",
                    description="Knowledge graph statistics and metrics",
                    mimeType="application/json"
                )
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Handle resource read requests."""
            await self._initialize_components()

            if uri == "analysis://results":
                return json.dumps(self.analysis_results, indent=2)
            elif uri == "graph://stats":
                stats = self.graph_builder.get_stats()
                return json.dumps(stats, indent=2)
            else:
                raise ValueError(f"Unknown resource: {uri}")

    # Tool implementation methods

    async def _tool_analyze_file(self, arguments: dict) -> Dict[str, Any]:
        """Implement analyze_file tool."""
        file_path = arguments["file_path"]
        agent_type = arguments.get("agent_type", "auto")

        # Auto-detect agent type if needed
        if agent_type == "auto":
            agent_type = self._detect_agent_type(file_path)

        if agent_type not in self.agents:
            raise ValueError(f"Unknown agent type: {agent_type}")

        # Analyze file
        agent = self.agents[agent_type]
        result = await agent.analyze(file_path)

        # Store result
        self.analysis_results[file_path] = result

        return {
            "file_path": file_path,
            "agent_type": agent_type,
            "result": result
        }

    async def _tool_analyze_directory(self, arguments: dict) -> Dict[str, Any]:
        """Implement analyze_directory tool."""
        directory_path = arguments["directory_path"]
        pattern = arguments.get("pattern", "**/*.java")

        # Find files
        directory = Path(directory_path)
        files = list(directory.glob(pattern))

        results_count = {"analyzed": 0, "failed": 0}

        # Analyze each file
        for file_path in files:
            try:
                agent_type = self._detect_agent_type(str(file_path))
                if agent_type:
                    agent = self.agents[agent_type]
                    result = await agent.analyze(str(file_path))
                    self.analysis_results[str(file_path)] = result
                    results_count["analyzed"] += 1
            except Exception as e:
                self.logger.error(f"Failed to analyze {file_path}: {e}")
                results_count["failed"] += 1

        # Build graph
        nodes_added, edges_added = self.graph_builder.build_from_analysis_results(
            self.analysis_results
        )

        return {
            "directory": str(directory_path),
            "files_found": len(files),
            "results": results_count,
            "graph": {
                "nodes_added": nodes_added,
                "edges_added": edges_added
            }
        }

    async def _tool_query_graph(self, arguments: dict) -> Dict[str, Any]:
        """Implement query_graph tool."""
        query_type = arguments["query_type"]

        if query_type == "stats":
            return self.graph_builder.get_stats()

        elif query_type == "find_node":
            node_id = arguments.get("node_id")
            node = self.graph_builder.get_node(node_id)
            if node:
                return {
                    "id": node.id,
                    "type": node.type.value,
                    "name": node.name,
                    "file_path": node.file_path,
                    "metadata": node.metadata
                }
            return {"error": f"Node not found: {node_id}"}

        elif query_type == "neighbors":
            node_id = arguments.get("node_id")
            neighbors = self.graph_builder.get_neighbors(node_id)
            return {
                "node_id": node_id,
                "neighbors": [
                    {"id": n.id, "type": n.type.value, "name": n.name}
                    for n in neighbors
                ]
            }

        elif query_type == "paths":
            node_id = arguments.get("node_id")
            target_id = arguments.get("target_id")
            paths = self.graph_builder.find_paths(node_id, target_id)
            return {
                "source": node_id,
                "target": target_id,
                "paths": [
                    [{"id": n.id, "name": n.name} for n in path]
                    for path in paths
                ]
            }

        return {"error": f"Unknown query type: {query_type}"}

    async def _tool_find_dependencies(self, arguments: dict) -> Dict[str, Any]:
        """Implement find_dependencies tool."""
        node_id = arguments["node_id"]
        max_depth = arguments.get("max_depth")

        dependencies = self.graph_builder.find_all_dependencies(node_id, max_depth)

        return {
            "node_id": node_id,
            "dependencies": [
                {"id": d.id, "type": d.type.value, "name": d.name}
                for d in dependencies
            ],
            "total_dependencies": len(dependencies)
        }

    async def _tool_analyze_impact(self, arguments: dict) -> Dict[str, Any]:
        """Implement analyze_impact tool."""
        node_id = arguments["node_id"]
        max_depth = arguments.get("max_depth")

        impact = self.graph_builder.analyze_impact(node_id, max_depth)

        return {
            "node": {
                "id": impact["node"].id,
                "type": impact["node"].type.value,
                "name": impact["node"].name
            },
            "direct_dependencies": [
                {"id": n.id, "type": n.type.value, "name": n.name}
                for n in impact["direct_dependencies"]
            ],
            "direct_dependents": [
                {"id": n.id, "type": n.type.value, "name": n.name}
                for n in impact["direct_dependents"]
            ],
            "total_dependencies": len(impact["all_dependencies"]),
            "total_dependents": len(impact["all_dependents"]),
            "impact_score": impact["impact_score"]
        }

    async def _tool_export_graph(self, arguments: dict) -> Dict[str, Any]:
        """Implement export_graph tool."""
        output_path = arguments["output_path"]
        format = arguments["format"]

        self.graph_builder.save_graph(output_path, format)

        return {
            "output_path": output_path,
            "format": format,
            "status": "success"
        }

    def _detect_agent_type(self, file_path: str) -> Optional[str]:
        """
        Auto-detect appropriate agent type based on file path/extension.

        Args:
            file_path: Path to file

        Returns:
            Agent type string or None if not detectable
        """
        file_path = file_path.lower()

        if file_path.endswith(".jsp"):
            return "jsp"
        elif "controller" in file_path and file_path.endswith(".java"):
            return "controller"
        elif "service" in file_path and file_path.endswith(".java"):
            return "service"
        elif file_path.endswith(".xml") and "mapper" in file_path:
            return "mapper"
        elif file_path.endswith(".sql") or file_path.endswith(".prc"):
            return "procedure"

        return None

    async def run(self):
        """Run the MCP server."""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="springmvc-analyzer",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    )
                )
            )


async def main():
    """Main entry point for MCP server."""
    logging.basicConfig(level=logging.INFO)
    server = SpringMVCAnalyzerServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
