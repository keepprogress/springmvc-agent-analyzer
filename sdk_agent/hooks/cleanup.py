"""Cleanup Hook - Session cleanup and finalization."""

from typing import Dict, Any, Optional
import logging

from sdk_agent.agent_factory import get_cost_tracker, get_graph_builder

logger = logging.getLogger("sdk_agent.hooks.cleanup")


class CleanupHook:
    """Stop hook for session cleanup."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        logger.info("CleanupHook initialized")

    async def __call__(
        self,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform cleanup when session stops."""
        if not self.enabled:
            return {}

        logger.info("Session stopping - performing cleanup...")

        try:
            # Get session statistics
            cost_tracker = get_cost_tracker()
            graph_builder = get_graph_builder()

            total_cost = cost_tracker.get_total_cost() if hasattr(cost_tracker, 'get_total_cost') else 0.0
            graph_stats = graph_builder.get_stats()

            summary = f"""
Session Summary:
- Total Cost: ${total_cost:.4f}
- Graph Nodes: {graph_stats.get('total_nodes', 0)}
- Graph Edges: {graph_stats.get('total_edges', 0)}
"""
            logger.info(summary)

            return {
                "summary": summary,
                "statistics": {
                    "total_cost": total_cost,
                    "graph_stats": graph_stats
                }
            }

        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return {}


default_cleanup_hook = CleanupHook()
