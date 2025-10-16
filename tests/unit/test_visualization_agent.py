"""
Unit tests for the VisualizationAgent.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from agents.visualization_agent import VisualizationAgent
from core.model_router import ModelRouter
from core.prompt_manager import PromptManager

@pytest.fixture
def mock_dependencies():
    """Provides mock dependencies for the agent."""
    mock_llm_client = MagicMock()
    mock_llm_client.query = AsyncMock(return_value="flowchart TD\nA --> B")

    mock_prompt_manager = MagicMock()
    mock_prompt_manager.get_prompt.return_value = "Prompt for {process_description}"

    return {
        "llm_client": mock_llm_client,
        "prompt_manager": mock_prompt_manager,
    }

def test_visualization_agent_initialization(mock_dependencies):
    """Tests that the VisualizationAgent can be initialized."""
    agent = VisualizationAgent(
        llm_client=mock_dependencies["llm_client"],
        prompt_manager=mock_dependencies["prompt_manager"],
    )
    assert agent is not None
    assert agent.llm_client is not None
    assert agent.prompt_manager is not None

@pytest.mark.asyncio
async def test_generate_flowchart_returns_mermaid(mock_dependencies):
    """Tests that the generate_flowchart method returns valid Mermaid syntax."""
    agent = VisualizationAgent(
        llm_client=mock_dependencies["llm_client"],
        prompt_manager=mock_dependencies["prompt_manager"],
    )

    result = await agent.generate_flowchart("test process")

    assert "mermaid_code" in result
    assert "flowchart TD" in result["mermaid_code"]
    assert result["confidence"] > 0.8