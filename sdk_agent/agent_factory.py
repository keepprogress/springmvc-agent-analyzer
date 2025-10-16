"""
Agent Factory for SDK Agent Mode.

This module provides a singleton factory for creating and managing agent instances
used by SDK tools. It handles lazy initialization and ensures agents are properly
configured with all required dependencies.
"""

from typing import Dict, Any, Optional
import logging
from pathlib import Path

from core.model_router import ModelRouter
from core.prompt_manager import PromptManager
from core.cost_tracker import CostTracker
from core.cache_manager import CacheManager
from graph.graph_builder import GraphBuilder
from graph.query import GraphQueryEngine
from agents.controller_agent import ControllerAgent
from agents.jsp_agent import JSPAgent
from agents.service_agent import ServiceAgent
from agents.mapper_agent import MapperAgent
from agents.procedure_agent import ProcedureAgent

logger = logging.getLogger("sdk_agent.factory")


class AgentFactory:
    """
    Singleton factory for creating and managing agents.

    This factory ensures that:
    1. Core components (ModelRouter, CostTracker, etc.) are initialized once
    2. Agents are created lazily on first use
    3. All agents share the same core components
    4. Configuration is properly propagated to all components

    Attributes:
        config: Configuration dictionary
        model_router: ModelRouter instance (shared)
        prompt_manager: PromptManager instance (shared)
        cost_tracker: CostTracker instance (shared)
        cache_manager: CacheManager instance (shared)
        graph_builder: GraphBuilder instance (shared)
        agents: Dictionary of initialized agents
    """

    _instance: Optional["AgentFactory"] = None
    _initialized: bool = False

    def __new__(cls, config: Optional[Dict[str, Any]] = None):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent factory.

        Args:
            config: Configuration dictionary (only used on first initialization)
        """
        # Only initialize once
        if self._initialized:
            return

        self.config = config or self._get_default_config()

        # Core components (initialized lazily)
        self.model_router: Optional[ModelRouter] = None
        self.prompt_manager: Optional[PromptManager] = None
        self.cost_tracker: Optional[CostTracker] = None
        self.cache_manager: Optional[CacheManager] = None
        self.graph_builder: Optional[GraphBuilder] = None
        self.graph_query_engine: Optional[GraphQueryEngine] = None

        # Agent instances (initialized lazily)
        self.agents: Dict[str, Any] = {}

        self._initialized = True
        logger.info("AgentFactory initialized")

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
            },
            "cache": {
                "cache_dir": ".cache",
                "max_size_mb": 1000,
                "ttl_seconds": 86400  # 24 hours
            }
        }

    def _initialize_core_components(self):
        """Initialize core components if not already done."""
        if self.model_router is not None:
            return  # Already initialized

        logger.info("Initializing core components...")

        self.model_router = ModelRouter(self.config)
        self.prompt_manager = PromptManager()
        self.cost_tracker = CostTracker()
        self.cache_manager = CacheManager()
        self.graph_builder = GraphBuilder()
        self.graph_query_engine = GraphQueryEngine(self.graph_builder.get_graph())

        logger.info("Core components initialized")

    def get_agent(self, agent_type: str) -> Any:
        """
        Get or create an agent of the specified type.

        Args:
            agent_type: Type of agent ("controller", "jsp", "service", "mapper", "procedure")

        Returns:
            Agent instance

        Raises:
            ValueError: If agent_type is invalid
        """
        # Ensure core components are initialized
        self._initialize_core_components()

        # Return cached agent if exists
        if agent_type in self.agents:
            return self.agents[agent_type]

        # Create new agent
        logger.info(f"Creating agent: {agent_type}")

        agent_classes = {
            "controller": ControllerAgent,
            "jsp": JSPAgent,
            "service": ServiceAgent,
            "mapper": MapperAgent,
            "procedure": ProcedureAgent
        }

        if agent_type not in agent_classes:
            raise ValueError(
                f"Invalid agent type: {agent_type}. "
                f"Valid types: {list(agent_classes.keys())}"
            )

        # Create agent with shared components
        agent_class = agent_classes[agent_type]
        agent = agent_class(
            model_router=self.model_router,
            prompt_manager=self.prompt_manager,
            cost_tracker=self.cost_tracker,
            cache_manager=self.cache_manager,
            config=self.config
        )

        # Cache the agent
        self.agents[agent_type] = agent
        logger.info(f"Agent created and cached: {agent_type}")

        return agent

    def get_graph_builder(self) -> GraphBuilder:
        """
        Get the shared GraphBuilder instance.

        Returns:
            GraphBuilder instance
        """
        self._initialize_core_components()
        return self.graph_builder

    def get_cost_tracker(self) -> CostTracker:
        """
        Get the shared CostTracker instance.

        Returns:
            CostTracker instance
        """
        self._initialize_core_components()
        return self.cost_tracker

    def reset(self):
        """
        Reset the factory (for testing purposes).

        Clears all cached agents and core components.
        """
        logger.warning("Resetting AgentFactory")
        self.agents.clear()
        self.model_router = None
        self.prompt_manager = None
        self.cost_tracker = None
        self.cache_manager = None
        self.graph_builder = None

    @classmethod
    def reset_singleton(cls):
        """Reset the singleton instance (for testing)."""
        if cls._instance is not None:
            cls._instance.reset()
            cls._instance = None
            cls._initialized = False


# Global factory instance (initialized on first import)
_factory: Optional[AgentFactory] = None


def get_factory(config: Optional[Dict[str, Any]] = None) -> AgentFactory:
    """
    Get the global AgentFactory instance.

    Args:
        config: Configuration dictionary (only used on first call)

    Returns:
        AgentFactory instance
    """
    global _factory
    if _factory is None:
        _factory = AgentFactory(config)
    return _factory


def get_agent(agent_type: str) -> Any:
    """
    Convenience function to get an agent.

    Args:
        agent_type: Type of agent

    Returns:
        Agent instance
    """
    return get_factory().get_agent(agent_type)


def get_graph_builder() -> GraphBuilder:
    """
    Convenience function to get the GraphBuilder.

    Returns:
        GraphBuilder instance
    """
    return get_factory().get_graph_builder()


def get_cost_tracker() -> CostTracker:
    """
    Convenience function to get the CostTracker.

    Returns:
        CostTracker instance
    """
    return get_factory().get_cost_tracker()


def get_agent_factory_and_dependencies() -> Dict[str, Any]:
    """
    Convenience function to get all dependencies needed for high-level agents.
    """
    factory = get_factory()
    factory._initialize_core_components()
    return {
        "llm_client": factory.model_router,  # Assuming ModelRouter acts as the client
        "prompt_manager": factory.prompt_manager,
        "graph_query_engine": factory.graph_query_engine,
    }
