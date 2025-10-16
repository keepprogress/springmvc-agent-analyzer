"""
Unit tests for the BusinessProcessAgent.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from agents.business_process_agent import BusinessProcessAgent
from core.model_router import ModelRouter
from core.prompt_manager import PromptManager
from graph.query import GraphQueryEngine

@pytest.fixture
def mock_dependencies():
    """Provides mock dependencies for the agent."""
    mock_model_router = MagicMock()
    mock_model_router.query = AsyncMock(return_value="Mocked LLM response")

    mock_prompt_manager = MagicMock()
    mock_prompt_manager.get_prompt.return_value = "Prompt for {process_description}"

    mock_cost_tracker = MagicMock()
    mock_cache_manager = MagicMock()
    mock_config = MagicMock()
    mock_graph_engine = MagicMock()

    tool_registry = {
        "query_graph": AsyncMock(),
        "find_dependencies": AsyncMock(),
    }

    return {
        "model_router": mock_model_router,
        "prompt_manager": mock_prompt_manager,
        "cost_tracker": mock_cost_tracker,
        "cache_manager": mock_cache_manager,
        "config": mock_config,
        "graph_query_engine": mock_graph_engine,
        "tool_registry": tool_registry,
    }

def test_business_process_agent_initialization(mock_dependencies):
    """Tests that the BusinessProcessAgent can be initialized."""
    agent = BusinessProcessAgent(
        model_router=mock_dependencies["model_router"],
        prompt_manager=mock_dependencies["prompt_manager"],
        cost_tracker=mock_dependencies["cost_tracker"],
        cache_manager=mock_dependencies["cache_manager"],
        config=mock_dependencies["config"],
        graph_query_engine=mock_dependencies["graph_query_engine"],
        tool_registry=mock_dependencies["tool_registry"],
    )
    assert agent is not None
    assert agent.llm_client is not None
    assert agent.prompt_manager is not None

@pytest.mark.asyncio
async def test_discover_process_returns_description(mock_dependencies):
    """Tests that the discover_process method returns a valid description."""
    agent = BusinessProcessAgent(
        model_router=mock_dependencies["model_router"],
        prompt_manager=mock_dependencies["prompt_manager"],
        cost_tracker=mock_dependencies["cost_tracker"],
        cache_manager=mock_dependencies["cache_manager"],
        config=mock_dependencies["config"],
        graph_query_engine=mock_dependencies["graph_query_engine"],
        tool_registry=mock_dependencies["tool_registry"],
    )

    result = await agent.discover_process("test process")

    assert "description" in result
    assert "SUCCESS" in result["description"]
    assert result["confidence"] > 0.9