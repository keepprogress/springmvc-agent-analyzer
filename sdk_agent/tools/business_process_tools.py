"""
Business Process Discovery Tools for SDK Agent Mode.

This module provides high-level tools for reverse-engineering business processes.
"""

import logging
from typing import Dict, Any

# This is a conceptual import.
# In a real implementation, we would need to resolve the dependencies correctly.
from agents.business_process_agent import BusinessProcessAgent
from sdk_agent.agent_factory import get_agent_factory_and_dependencies
from sdk_agent.utils import format_tool_result

logger = logging.getLogger("sdk_agent.tools.business_process")

DISCOVER_BUSINESS_PROCESS_META = {
    "name": "discover_business_process",
    "description": (
        "Traces a business process from a starting point (e.g., a URL or user action).\n"
        "It uses the knowledge graph to follow dependencies and synthesizes the flow "
        "into a human-readable description."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "starting_point": {
                "type": "string",
                "description": "A natural language description of the process starting point, e.g., 'user registration' or 'the /orders/create endpoint'."
            },
            "project_root": {
                "type": "string",
                "description": "Project root directory for context.",
                "default": None
            }
        },
        "required": ["starting_point"]
    }
}


async def discover_business_process(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    High-level tool to discover and describe a business process.

    Args:
        args: Dictionary with keys:
            - starting_point (str): The entry point of the process to trace.
            - project_root (str, optional): The project root directory.

    Returns:
        A dictionary with the analysis results.
    """
    starting_point = args["starting_point"]
    logger.info(f"Discovering business process for: '{starting_point}'")

    try:
        # In a real application, we would get these from a dependency injection container.
        # For now, we get them from the factory helper.
        dependencies = get_agent_factory_and_dependencies()
        llm_client = dependencies["llm_client"]
        prompt_manager = dependencies["prompt_manager"]
        graph_query_engine = dependencies["graph_query_engine"]

        # In a real application, this would be a more sophisticated registry.
        from sdk_agent.sdk_tools import query_graph, find_dependencies
        tool_registry = {
            "query_graph": query_graph,
            "find_dependencies": find_dependencies,
        }

        # Instantiate our new agent
        agent = BusinessProcessAgent(
            llm_client=llm_client,
            prompt_manager=prompt_manager,
            graph_query_engine=graph_query_engine,
            tool_registry=tool_registry,
        )

        # Execute the discovery process
        result = await agent.discover_process(starting_point)

        # Format the output for the SDK client
        summary = result.get("description", "No description generated.")

        return {
            "content": [{"type": "text", "text": summary}],
            "data": result,
            "is_error": False
        }

    except Exception as e:
        logger.error(f"Error discovering business process for '{starting_point}': {e}", exc_info=True)
        return format_tool_result(
            {"error": str(e), "starting_point": starting_point},
            format_type="json",
            is_error=True
        )