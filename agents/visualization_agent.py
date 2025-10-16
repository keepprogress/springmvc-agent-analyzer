"""
Visualization Agent for Business Process Flowcharts.

This agent takes a description of a business process and converts it
into a graphical flowchart using Mermaid.js syntax.
"""

from typing import Dict, Any

from core.model_router import ModelRouter
from core.prompt_manager import PromptManager


class VisualizationAgent:
    """
    Agent that generates Mermaid.js flowcharts from business process descriptions.
    """

    def __init__(self, llm_client: ModelRouter, prompt_manager: PromptManager):
        """
        Initializes the VisualizationAgent.

        Args:
            llm_client: The language model client for generating the flowchart.
            prompt_manager: The manager for fetching prompts.
        """
        self.llm_client = llm_client
        self.prompt_manager = prompt_manager
        self.prompt_template = self.prompt_manager.get_prompt("generate_mermaid_flowchart")

    async def generate_flowchart(self, process_description: str) -> Dict[str, Any]:
        """
        Generates a Mermaid.js flowchart from a business process description.

        Args:
            process_description: A textual, step-by-step description of the business process.

        Returns:
            A dictionary containing the Mermaid syntax for the flowchart.
        """
        print("Generating Mermaid.js flowchart from process description...")

        # Use an LLM to convert the text description to Mermaid syntax.
        prompt = self.prompt_template.format(
            process_description=process_description
        )

        mermaid_syntax = await self.llm_client.query(prompt)

        # Basic validation to ensure the response looks like Mermaid syntax
        if "graph TD" not in mermaid_syntax and "flowchart TD" not in mermaid_syntax:
            # Fallback or error handling
            mermaid_syntax = """
flowchart TD
    A[Error] --> B(Could not generate flowchart);
"""
            return {
                "mermaid_code": mermaid_syntax,
                "confidence": 0.3,
                "error": "Failed to generate valid Mermaid syntax."
            }


        return {
            "mermaid_code": mermaid_syntax,
            "confidence": 0.9,
            "message": "Flowchart generated successfully."
        }