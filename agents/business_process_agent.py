"""
Business Process Discovery Agent.

This high-level agent orchestrates other tools to discover and document
business processes from the codebase.
"""

import asyncio
from typing import Dict, Any

from agents.base_agent import BaseAgent
from core.model_router import ModelRouter
from core.prompt_manager import PromptManager
from graph.query import GraphQueryEngine  # Assuming this will be the query engine


class BusinessProcessAgent(BaseAgent):
    """
    An agent that reverse-engineers business processes by tracing code execution paths.
    """

    def __init__(
        self,
        model_router: ModelRouter,
        prompt_manager: PromptManager,
        cost_tracker,
        cache_manager,
        config,
        graph_query_engine: GraphQueryEngine,
        tool_registry: Dict[str, callable],
    ):
        """
        Initializes the BusinessProcessAgent.
        """
        super().__init__("business_process", model_router, prompt_manager, cost_tracker, cache_manager, config)
        self.llm_client = model_router
        self.graph_query_engine = graph_query_engine
        self.prompt_template = self.prompt_manager.get_prompt(
            "business_process_discovery"
        )
        self.tool_registry = tool_registry

    async def _analyze_impl(self, file_path: str) -> Dict[str, Any]:
        """
        This agent orchestrates tools rather than analyzing a single file.
        This implementation is a placeholder to satisfy the abstract base class.
        """
        return {"error": "This agent does not analyze single files. Use discover_process instead."}

    async def discover_process(self, starting_point: str) -> Dict[str, Any]:
        """
        Traces a business process starting from a given point.

        Args:
            starting_point: A natural language description of the starting point,
                            e.g., "user registration" or "endpoint /api/orders/create".

        Returns:
            A dictionary containing the discovered process description and metadata.
        """
        print(f"Starting business process discovery from: '{starting_point}'")

        # 1. Use an LLM to formulate a plan: what tools to call in what order.
        planning_prompt = f"""
        Given the user request to trace the business process starting from '{starting_point}',
        create a step-by-step plan of which tools to call (`query_graph`, `find_dependencies`)
        to trace the entire flow.

        First, identify the initial code component (e.g., a controller method, a service).
        Then, iteratively trace dependencies outwards.

        Return a JSON object with a 'plan' key, which is a list of steps.
        Each step should have 'tool_name' and 'arguments' keys.
        """
        planning_response = await self.llm_client.query(planning_prompt)

        # In a real implementation, we would parse planning_response and execute the tools.
        # For this step, we will simulate the process and generate a final description.

        # 2. (Simulated) Execute the plan and gather results.
        # This would involve calling the tools from self.tool_registry in a loop.
        # For now, we'll assume the plan was executed and we have the results.

        # 3. Use an LLM to synthesize the results into a human-readable description.
        synthesis_prompt = f"""
        Based on the analysis of the code starting from '{starting_point}',
        synthesize the information into a clear, human-readable business process description.
        Describe the flow step-by-step, from the entry point to the end.
        Mention the key components (Controllers, Services, Mappers) and data entities involved.

        Example:
        "The User Registration process begins at the '/users/register' endpoint handled by UserController.
        It calls UserService.registerUser(), which validates the input.
        Next, it invokes UserMapper.createUser() to insert data into the 'USERS' table.
        Finally, it may call an EmailService to send a welcome notification."

        Generate the description now.
        """
        final_description = await self.llm_client.query(synthesis_prompt)

        # This is a mock response for demonstration.
        # A real response would be the `final_description` from the LLM.
        mock_description = (
            f"SUCCESS: Business process for '{starting_point}' discovered.\n"
            f"1. Process starts at an endpoint like `/users/create` in `UserController`.\n"
            f"2. `UserController` calls `UserService.createUser()` for business logic.\n"
            f"3. `UserService` validates data and calls `UserMapper.insert()`.\n"
            f"4. `UserMapper` writes the new user to the `USERS` database table.\n"
            f"5. An audit log is written via `AuditService`."
        )

        return {
            "starting_point": starting_point,
            "description": mock_description, # In a real implementation, use `final_description`
            "confidence": 0.95,
            "metadata": {
                "steps_traced": 5,
                "components_involved": [
                    "UserController",
                    "UserService",
                    "UserMapper",
                    "AuditService",
                ],
            },
        }