"""
SDK Agent Client Module.

Main client class for SDK Agent mode.
"""

from typing import Optional, Dict, Any
from pathlib import Path
import logging

from sdk_agent.config import SDKAgentConfig, load_config
from sdk_agent.exceptions import AgentNotInitializedError, ConfigurationError

logger = logging.getLogger(__name__)


class SpringMVCAnalyzerAgent:
    """
    Main SDK Agent client for SpringMVC analysis.

    This client provides interactive dialogue-driven analysis using
    Claude Agent SDK with autonomous tool selection and hooks system.

    Usage:
        agent = SpringMVCAnalyzerAgent(
            config_path="config/sdk_agent_config.yaml",
            hooks_enabled=True
        )

        # Interactive mode
        await agent.start_interactive()

        # Batch mode
        result = await agent.analyze_project(
            project_path="src/main/java",
            output_format="markdown"
        )
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        system_prompt: Optional[str] = None,
        hooks_enabled: bool = True,
        permission_mode: str = "acceptEdits",
        max_turns: int = 20
    ):
        """
        Initialize SpringMVCAnalyzerAgent.

        Args:
            config_path: Path to configuration file
            system_prompt: Custom system prompt (overrides config)
            hooks_enabled: Enable hooks system
            permission_mode: Permission mode (acceptAll, acceptEdits, rejectAll)
            max_turns: Maximum conversation turns
        """
        # Load configuration
        self.config = load_config(config_path)

        # Override config with parameters
        if hooks_enabled is not None:
            self.config.hooks_enabled = hooks_enabled
        if permission_mode is not None:
            self.config.permission_mode = permission_mode
        if max_turns is not None:
            self.config.max_turns = max_turns

        # Load system prompt
        if system_prompt:
            self.system_prompt = system_prompt
        elif self.config.system_prompt_path:
            prompt_file = Path(self.config.system_prompt_path)
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    self.system_prompt = f.read()
            else:
                logger.warning(f"System prompt file not found: {self.config.system_prompt_path}")
                self.system_prompt = self._get_default_system_prompt()
        else:
            self.system_prompt = self._get_default_system_prompt()

        # Initialize components (will be implemented in Phase 5)
        self.client = None  # ClaudeSDKClient instance
        self.hooks = []     # List of registered hooks
        self.tools = []     # List of registered tools

        logger.info(f"SpringMVCAnalyzerAgent initialized with mode: {self.config.mode}")

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt."""
        return """You are a Spring MVC code analysis expert.

Analyze Spring MVC, JSP, MyBatis, and Oracle projects with expertise.
Use available tools to analyze code and provide insights."""

    async def start_interactive(self) -> None:
        """
        Start interactive dialogue mode.

        Raises:
            AgentNotInitializedError: If client not initialized
        """
        if not self.client:
            raise AgentNotInitializedError(
                "Agent not initialized. SDK Client not available."
            )

        logger.info("Starting interactive mode...")
        # Implementation in Phase 5
        print("🤖 SpringMVC Agent Analyzer - Interactive Mode")
        print("=" * 60)
        print("Note: Full implementation coming in Phase 5")
        print("=" * 60)

    async def analyze_project(
        self,
        project_path: str,
        output_format: str = "markdown"
    ) -> Dict[str, Any]:
        """
        Analyze entire project (batch mode).

        Args:
            project_path: Path to project directory
            output_format: Output format (markdown, json, html)

        Returns:
            Analysis results

        Raises:
            AgentNotInitializedError: If client not initialized
        """
        if not self.client:
            raise AgentNotInitializedError(
                "Agent not initialized. SDK Client not available."
            )

        logger.info(f"Analyzing project: {project_path}")
        # Implementation in Phase 5
        return {
            "status": "pending",
            "message": "Full implementation coming in Phase 5",
            "project_path": project_path,
            "output_format": output_format
        }

    async def set_model(self, model: str) -> None:
        """
        Dynamically set model at runtime.

        Args:
            model: Model name
        """
        if not self.client:
            raise AgentNotInitializedError("Agent not initialized")

        logger.info(f"Switching model to: {model}")
        # Implementation in Phase 5

    async def set_permission_mode(self, mode: str) -> None:
        """
        Dynamically set permission mode.

        Args:
            mode: Permission mode (acceptAll, acceptEdits, rejectAll)
        """
        if mode not in ["acceptAll", "acceptEdits", "rejectAll"]:
            raise ValueError(f"Invalid permission mode: {mode}")

        self.config.permission_mode = mode
        logger.info(f"Permission mode set to: {mode}")

    async def interrupt(self) -> None:
        """Interrupt current operation."""
        if not self.client:
            raise AgentNotInitializedError("Agent not initialized")

        logger.info("Interrupting current operation...")
        # Implementation in Phase 5

    def get_config(self) -> SDKAgentConfig:
        """Get current configuration."""
        return self.config

    def get_tools(self) -> list:
        """Get list of registered tools."""
        return self.tools

    def get_hooks(self) -> list:
        """Get list of registered hooks."""
        return self.hooks
