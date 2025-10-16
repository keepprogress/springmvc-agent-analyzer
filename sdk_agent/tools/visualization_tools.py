"""
Visualization Tools for SDK Agent Mode.

This module provides tools for generating visualizations like flowcharts.
"""

import logging
from typing import Dict, Any

from agents.visualization_agent import VisualizationAgent
from sdk_agent.agent_factory import get_agent_factory_and_dependencies
from sdk_agent.utils import format_tool_result

logger = logging.getLogger("sdk_agent.tools.visualization")

GENERATE_BUSINESS_FLOWCHART_META = {
    "name": "generate_business_flowchart",
    "description": (
        "Takes a textual description of a business process and converts it "
        "into a graphical flowchart using Mermaid.js syntax."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "process_description": {
                "type": "string",
                "description": "A step-by-step textual description of the business process.",
            },
            "output_format": {
                "type": "string",
                "description": "The desired output format. Use 'mermaid' for the raw code or 'url' to get a link to a rendered image.",
                "default": "mermaid",
            },
        },
        "required": ["process_description"],
    },
}


async def generate_business_flowchart(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool to generate a Mermaid.js flowchart from a process description.

    Args:
        args: Dictionary with keys:
            - process_description (str): The text description of the process.
            - output_format (str): 'mermaid' or 'url'.

    Returns:
        A dictionary with the Mermaid syntax or a URL to the rendered image.
    """
    process_description: str = args["process_description"]
    output_format: str = args.get("output_format", "mermaid")

    logger.info("Generating business flowchart.")

    try:
        # Get dependencies from the factory
        dependencies = get_agent_factory_and_dependencies()
        llm_client = dependencies["llm_client"]
        prompt_manager = dependencies["prompt_manager"]

        # Instantiate the visualization agent
        agent = VisualizationAgent(llm_client=llm_client, prompt_manager=prompt_manager)

        # Generate the flowchart
        result = await agent.generate_flowchart(process_description)
        mermaid_code = result.get("mermaid_code", "")

        # Handle different output formats
        if output_format == "url":
            # In a real implementation, we would use a service to render this.
            # For now, we can use a public service like mermaid.ink for demonstration.
            import base64
            encoded_code = base64.b64encode(mermaid_code.encode("utf-8")).decode("utf-8")
            url = f"https://mermaid.ink/img/{encoded_code}"
            output_content = f"Rendered flowchart available at: {url}"
        else:
            # Return the raw Mermaid code block
            output_content = f"```mermaid\n{mermaid_code}\n```"

        return {
            "content": [{"type": "text", "text": output_content}],
            "data": {
                "message": "Flowchart generated successfully.",
                "format": output_format,
                "mermaid_code": mermaid_code,
            },
            "is_error": False,
        }

    except Exception as e:
        logger.error(f"Error generating flowchart: {e}", exc_info=True)
        return format_tool_result(
            {"error": str(e)},
            format_type="json",
            is_error=True
        )