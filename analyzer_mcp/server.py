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
from datetime import datetime, timedelta

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
        self.result_timestamps = {}  # file_path -> timestamp
        self.current_project = None

        # Rate limiting
        self.request_history = []  # List of request timestamps

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
            "server": {
                "mode": "api"  # "api" or "passive"
            },
            "models": {
                "haiku": "claude-3-5-haiku-20241022",
                "sonnet": "claude-3-5-sonnet-20241022",
                "opus": "claude-opus-4-20250514"
            },
            "agents": {
                "min_confidence": 0.7
            },
            "mcp": {
                "result_max_age_seconds": 3600,  # 1 hour
                "auto_cleanup": True,
                "rate_limit_enabled": True,
                "rate_limit_requests_per_minute": 60,
                "rate_limit_burst": 10  # Allow burst of requests
            }
        }

    async def _initialize_components(self):
        """Initialize core components lazily."""
        # Check if already initialized (use graph_builder as marker)
        if self.graph_builder is not None:
            return  # Already initialized

        mode = self.config.get("server", {}).get("mode", "api")
        self.logger.info(f"Initializing core components in {mode} mode...")

        # Always initialize graph builder and prompt manager
        self.graph_builder = GraphBuilder()
        self.prompt_manager = PromptManager()

        if mode == "api":
            # API mode: Full initialization with LLM agents
            self.model_router = ModelRouter(self.config)
            self.cost_tracker = CostTracker()
            self.cache_manager = CacheManager()

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
            self.logger.info("Core components initialized (API mode)")

        elif mode == "passive":
            # Passive mode: No LLM agents, only tools for Claude Code
            self.logger.info(
                "Core components initialized (Passive mode) - "
                "LLM analysis will be performed by Claude Code"
            )

        else:
            raise ValueError(f"Invalid server mode: {mode}. Must be 'api' or 'passive'")

    def _register_handlers(self):
        """Register MCP protocol handlers."""

        # Tool handlers
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available MCP tools based on server mode."""
            mode = self.config.get("server", {}).get("mode", "api")

            if mode == "passive":
                # Passive mode tools: for Claude Code to read files and submit analysis
                return self._get_passive_mode_tools()
            else:
                # API mode tools: full autonomous analysis
                return self._get_api_mode_tools()

        def _get_api_mode_tools(self) -> List[types.Tool]:
            """Get tools for API mode (autonomous LLM analysis)."""
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
            try:
                # Check rate limits
                self.check_rate_limit()

                # Initialize components if needed
                await self._initialize_components()

                # Auto-cleanup old results if enabled
                if self.config.get("mcp", {}).get("auto_cleanup", True):
                    max_age = self.config.get("mcp", {}).get("result_max_age_seconds", 3600)
                    self.clear_old_results(max_age)

                # Execute tool
                # Passive mode tools
                if name == "read_file_with_prompt":
                    result = await self._tool_read_file_with_prompt(arguments)
                elif name == "submit_analysis":
                    result = await self._tool_submit_analysis(arguments)
                elif name == "build_graph":
                    result = await self._tool_build_graph(arguments)
                # API mode tools
                elif name == "analyze_file":
                    result = await self._tool_analyze_file(arguments)
                elif name == "analyze_directory":
                    result = await self._tool_analyze_directory(arguments)
                # Shared tools (both modes)
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
            resources = [
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

            # Add prompt template resources in passive mode
            mode = self.config.get("server", {}).get("mode", "api")
            if mode == "passive":
                resources.extend([
                    types.Resource(
                        uri="prompts://controller",
                        name="Controller Analysis Prompt",
                        description="Prompt template for analyzing Spring MVC Controllers",
                        mimeType="text/plain"
                    ),
                    types.Resource(
                        uri="prompts://jsp",
                        name="JSP Analysis Prompt",
                        description="Prompt template for analyzing JSP files",
                        mimeType="text/plain"
                    ),
                    types.Resource(
                        uri="prompts://service",
                        name="Service Analysis Prompt",
                        description="Prompt template for analyzing Service classes",
                        mimeType="text/plain"
                    ),
                    types.Resource(
                        uri="prompts://mapper",
                        name="MyBatis Mapper Analysis Prompt",
                        description="Prompt template for analyzing MyBatis Mapper XML files",
                        mimeType="text/plain"
                    ),
                    types.Resource(
                        uri="prompts://procedure",
                        name="Stored Procedure Analysis Prompt",
                        description="Prompt template for analyzing Oracle stored procedures",
                        mimeType="text/plain"
                    )
                ])

            return resources

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Handle resource read requests."""
            await self._initialize_components()

            if uri == "analysis://results":
                return json.dumps(self.analysis_results, indent=2)
            elif uri == "graph://stats":
                stats = self.graph_builder.get_statistics()
                return json.dumps(stats, indent=2)
            elif uri.startswith("prompts://"):
                # Extract agent type from URI
                agent_type = uri.replace("prompts://", "")
                if agent_type in ["controller", "jsp", "service", "mapper", "procedure"]:
                    try:
                        prompt = self.prompt_manager.get_prompt(
                            agent_name=agent_type,
                            prompt_type="analysis"
                        )
                        return prompt
                    except Exception as e:
                        raise ValueError(f"Failed to load prompt for {agent_type}: {str(e)}")
                else:
                    raise ValueError(f"Unknown agent type in prompt URI: {agent_type}")
            else:
                raise ValueError(f"Unknown resource: {uri}")

    # Tool implementation methods

    # Passive Mode Tool Implementations

    async def _tool_read_file_with_prompt(self, arguments: dict) -> Dict[str, Any]:
        """
        Implement read_file_with_prompt tool (Passive mode).

        Reads a file and returns its content along with the appropriate
        analysis prompt template for Claude Code to use.
        """
        file_path = arguments["file_path"]
        agent_type = arguments.get("agent_type", "auto")

        # Auto-detect agent type if needed
        if agent_type == "auto":
            agent_type = self._detect_agent_type(file_path)
            if not agent_type:
                return {
                    "error": f"Could not auto-detect agent type for {file_path}",
                    "file_path": file_path
                }

        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except Exception as e:
            return {
                "error": f"Failed to read file: {str(e)}",
                "file_path": file_path
            }

        # Get prompt template
        prompt_template = self.prompt_manager.get_prompt(
            agent_name=agent_type,
            prompt_type="analysis"
        )

        return {
            "file_path": file_path,
            "agent_type": agent_type,
            "file_content": file_content,
            "prompt_template": prompt_template,
            "instructions": (
                f"Please analyze this {agent_type} file using the prompt template provided. "
                "Return the analysis in the same JSON format as specified in the template. "
                "Then use submit_analysis tool to submit your results."
            )
        }

    async def _tool_submit_analysis(self, arguments: dict) -> Dict[str, Any]:
        """
        Implement submit_analysis tool (Passive mode).

        Stores analysis results submitted by Claude Code for later graph building.
        """
        file_path = arguments["file_path"]
        agent_type = arguments["agent_type"]
        analysis = arguments["analysis"]
        confidence = arguments.get("confidence", 0.9)

        # Store result in the same format as API mode
        result = {
            "agent": agent_type,
            "analysis": analysis,
            "confidence": confidence,
            "model_used": "claude-code",
            "cost": 0.0,  # No API cost in passive mode
            "cached": False,
            "timestamp": datetime.now().isoformat()
        }

        self.analysis_results[file_path] = result
        self.result_timestamps[file_path] = datetime.now()

        return {
            "status": "success",
            "file_path": file_path,
            "agent_type": agent_type,
            "message": f"Analysis results stored for {file_path}"
        }

    async def _tool_build_graph(self, arguments: dict) -> Dict[str, Any]:
        """
        Implement build_graph tool (Passive mode).

        Builds the knowledge graph from all submitted analysis results.
        """
        if not self.analysis_results:
            return {
                "status": "warning",
                "message": "No analysis results to build graph from",
                "nodes_added": 0,
                "edges_added": 0
            }

        # Build graph from results
        nodes_added, edges_added = self.graph_builder.build_from_analysis_results(
            self.analysis_results
        )

        # Get graph statistics
        stats = self.graph_builder.get_statistics()

        return {
            "status": "success",
            "nodes_added": nodes_added,
            "edges_added": edges_added,
            "total_files_analyzed": len(self.analysis_results),
            "graph_stats": stats
        }

    # API Mode Tool Implementations

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

        # Store result with timestamp
        self.analysis_results[file_path] = result
        self.result_timestamps[file_path] = datetime.now()

        return {
            "file_path": file_path,
            "agent_type": agent_type,
            "result": result
        }

    async def _tool_analyze_directory(self, arguments: dict) -> Dict[str, Any]:
        """Implement analyze_directory tool."""
        directory_path = arguments["directory_path"]
        pattern = arguments.get("pattern", "**/*.java")
        timeout_per_file = arguments.get("timeout_per_file", 300.0)  # 5 minutes default

        # Find files
        directory = Path(directory_path)
        files = list(directory.glob(pattern))
        total_files = len(files)

        self.logger.info(f"Starting directory analysis: {total_files} files matching '{pattern}'")

        results_count = {"analyzed": 0, "failed": 0, "timeout": 0}

        # Analyze each file with timeout
        for idx, file_path in enumerate(files, 1):
            try:
                agent_type = self._detect_agent_type(str(file_path))
                if agent_type:
                    agent = self.agents[agent_type]

                    # Add timeout to prevent hanging on large files
                    result = await asyncio.wait_for(
                        agent.analyze(str(file_path)),
                        timeout=timeout_per_file
                    )

                    self.analysis_results[str(file_path)] = result
                    results_count["analyzed"] += 1

                    # Log progress
                    if idx % 10 == 0 or idx == total_files:
                        self.logger.info(
                            f"Progress: {idx}/{total_files} files "
                            f"(analyzed: {results_count['analyzed']}, "
                            f"failed: {results_count['failed']})"
                        )

            except asyncio.TimeoutError:
                self.logger.error(f"Timeout analyzing {file_path} (>{timeout_per_file}s)")
                results_count["timeout"] += 1
                results_count["failed"] += 1

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

    def clear_old_results(self, max_age_seconds: int = 3600) -> int:
        """
        Clear analysis results older than specified age.

        Args:
            max_age_seconds: Maximum age of results to keep (default: 3600 = 1 hour)

        Returns:
            Number of results removed
        """
        cutoff = datetime.now() - timedelta(seconds=max_age_seconds)

        # Find old results
        old_results = [
            path for path, timestamp in self.result_timestamps.items()
            if timestamp < cutoff
        ]

        # Remove old results
        for path in old_results:
            del self.analysis_results[path]
            del self.result_timestamps[path]

        if old_results:
            self.logger.info(
                f"Cleaned up {len(old_results)} results older than {max_age_seconds}s"
            )

        return len(old_results)

    def check_rate_limit(self) -> bool:
        """
        Check if current request is within rate limits.

        Returns:
            True if request is allowed, False if rate limited

        Raises:
            Exception: If rate limit is exceeded
        """
        if not self.config.get("mcp", {}).get("rate_limit_enabled", True):
            return True

        now = datetime.now()
        window_start = now - timedelta(minutes=1)
        requests_per_minute = self.config.get("mcp", {}).get("rate_limit_requests_per_minute", 60)
        burst_limit = self.config.get("mcp", {}).get("rate_limit_burst", 10)

        # Clean old requests outside window
        self.request_history = [
            ts for ts in self.request_history
            if ts > window_start
        ]

        # Check burst limit (last 10 seconds)
        burst_window_start = now - timedelta(seconds=10)
        recent_requests = sum(1 for ts in self.request_history if ts > burst_window_start)

        if recent_requests >= burst_limit:
            raise Exception(
                f"Rate limit exceeded: {recent_requests} requests in 10 seconds "
                f"(burst limit: {burst_limit})"
            )

        # Check per-minute limit
        if len(self.request_history) >= requests_per_minute:
            raise Exception(
                f"Rate limit exceeded: {len(self.request_history)} requests per minute "
                f"(limit: {requests_per_minute})"
            )

        # Record this request
        self.request_history.append(now)
        return True

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