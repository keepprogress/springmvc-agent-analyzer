"""Context Manager Hook - Smart context compression."""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger("sdk_agent.hooks.context")


class ContextManagerHook:
    """PreCompact hook for intelligent context compression."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.keep_recent = self.config.get("keep_recent_messages", 10)
        logger.info(f"ContextManagerHook initialized (keep_recent={self.keep_recent})")

    async def __call__(
        self,
        messages: list,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Decide what to keep during context compression."""
        if not self.enabled:
            return {}

        logger.info(f"Context compression: {len(messages)} messages")
        # Keep recent messages and important tool results
        keep_indices = list(range(max(0, len(messages) - self.keep_recent), len(messages)))

        return {
            "keep_messages": keep_indices,
            "compression_summary": f"Kept {len(keep_indices)} recent messages"
        }


default_context_hook = ContextManagerHook()
