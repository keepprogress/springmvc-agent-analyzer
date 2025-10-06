"""
SDK Agent Client Module.

Main client class for SDK Agent mode.
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

from sdk_agent.config import SDKAgentConfig, load_config
from sdk_agent.exceptions import AgentNotInitializedError, ConfigurationError
from sdk_agent.constants import PHASE_NOT_IMPLEMENTED_MESSAGE
from sdk_agent.utils import load_system_prompt

# Use module-specific logger to avoid conflicts
logger = logging.getLogger("sdk_agent.client")


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
        hooks_enabled: Optional[bool] = None,
        permission_mode: Optional[str] = None,
        max_turns: Optional[int] = None
    ):
        """
        Initialize SpringMVCAnalyzerAgent.

        Args:
            config_path: Path to configuration file
            system_prompt: Custom system prompt (overrides config)
            hooks_enabled: Enable hooks system (overrides config if specified)
            permission_mode: Permission mode (overrides config if specified)
            max_turns: Maximum conversation turns (overrides config if specified)
        """
        # Load configuration
        self.config = load_config(config_path)

        # Override config with explicitly provided parameters
        if hooks_enabled is not None:
            self.config.hooks_enabled = hooks_enabled
        if permission_mode is not None:
            self.config.permission_mode = permission_mode
        if max_turns is not None:
            self.config.max_turns = max_turns

        # Load system prompt (with caching)
        if system_prompt:
            self.system_prompt = system_prompt
        elif self.config.system_prompt_path:
            prompt_file = Path(self.config.system_prompt_path)
            if prompt_file.exists():
                self.system_prompt = load_system_prompt(str(prompt_file))
            else:
                logger.warning(
                    f"System prompt file not found: {self.config.system_prompt_path}"
                )
                self.system_prompt = self._get_default_system_prompt()
        else:
            self.system_prompt = self._get_default_system_prompt()

        # Initialize components (will be implemented in Phase 5)
        self.client = None  # ClaudeSDKClient instance
        self.hooks: List[Any] = []     # List of registered hooks
        self.tools: List[Dict[str, Any]] = []     # List of registered tools

        logger.info(
            f"SpringMVCAnalyzerAgent initialized: mode={self.config.mode}, "
            f"hooks_enabled={self.config.hooks_enabled}, "
            f"permission_mode={self.config.permission_mode}"
        )

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt."""
        return """You are a Spring MVC code analysis expert.

Analyze Spring MVC, JSP, MyBatis, and Oracle projects with expertise.
Use available tools to analyze code and provide insights."""

    async def start_interactive(self) -> None:
        """
        Start interactive dialogue mode.

        Raises:
            AgentNotInitializedError: If client not initialized (Phase 5)
        """
        if not self.client:
            raise AgentNotInitializedError(
                PHASE_NOT_IMPLEMENTED_MESSAGE.format(phase=5) +
                "\n\nCurrent status: Phase 2 (Infrastructure) complete. "
                "SDK Client integration requires Phase 3 (Tools) and "
                "Phase 4 (Hooks) to be implemented first."
            )

        logger.info("Starting interactive mode...")
        # Full implementation in Phase 5
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
            AgentNotInitializedError: If client not initialized (Phase 5)
        """
        if not self.client:
            raise AgentNotInitializedError(
                PHASE_NOT_IMPLEMENTED_MESSAGE.format(phase=5) +
                "\n\nCurrent status: Phase 2 (Infrastructure) complete."
            )

        logger.info(f"Analyzing project: {project_path}")
        # Full implementation in Phase 5
        return {
            "status": "pending",
            "message": PHASE_NOT_IMPLEMENTED_MESSAGE.format(phase=5),
            "project_path": project_path,
            "output_format": output_format
        }

    async def set_model(self, model: str) -> None:
        """
        Dynamically set model at runtime.

        Args:
            model: Model name

        Raises:
            AgentNotInitializedError: If client not initialized (Phase 5)
        """
        if not self.client:
            raise AgentNotInitializedError(
                PHASE_NOT_IMPLEMENTED_MESSAGE.format(phase=5)
            )

        logger.info(f"Switching model to: {model}")
        # Full implementation in Phase 5

    async def set_permission_mode(self, mode: str) -> None:
        """
        Dynamically set permission mode.

        Args:
            mode: Permission mode (acceptAll, acceptEdits, rejectAll)

        Raises:
            ValueError: If mode is invalid
        """
        from sdk_agent.constants import VALID_PERMISSION_MODES

        if mode not in VALID_PERMISSION_MODES:
            raise ValueError(
                f"Invalid permission mode: {mode}. "
                f"Must be one of {VALID_PERMISSION_MODES}"
            )

        self.config.permission_mode = mode
        logger.info(f"Permission mode set to: {mode}")

    async def interrupt(self) -> None:
        """
        Interrupt current operation.

        Raises:
            AgentNotInitializedError: If client not initialized (Phase 5)
        """
        if not self.client:
            raise AgentNotInitializedError(
                PHASE_NOT_IMPLEMENTED_MESSAGE.format(phase=5)
            )

        logger.info("Interrupting current operation...")
        # Full implementation in Phase 5

    def get_config(self) -> SDKAgentConfig:
        """Get current configuration."""
        return self.config

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of registered tools."""
        return self.tools

    def get_hooks(self) -> List[Any]:
        """Get list of registered hooks."""
        return self.hooks
