"""Input Enhancement Hook - Enhance user prompts with context."""

from typing import Dict, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger("sdk_agent.hooks.input")


class InputEnhancementHook:
    """UserPromptSubmit hook to enhance user inputs."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.project_root = self.config.get("project_root")
        logger.info(f"InputEnhancementHook initialized")

    async def __call__(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Enhance user input with project context."""
        if not self.enabled:
            return {}

        enhancements = []

        # Add project root info if available
        if self.project_root and Path(self.project_root).exists():
            enhancements.append(f"Project root: {self.project_root}")

        # Expand relative paths mentioned in input
        enhanced_input = user_input
        if enhancements:
            enhanced_input = "\n".join(enhancements) + "\n\n" + user_input

        return {
            "enhanced_input": enhanced_input if enhancements else None
        }


default_input_hook = InputEnhancementHook()
