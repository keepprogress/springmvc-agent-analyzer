"""
Controller Agent for Spring MVC Controller analysis.

This module implements the first POC agent that analyzes Spring Controller files
to extract request mappings, dependencies, and HTTP endpoints.
"""

from __future__ import annotations
from typing import Dict, Any, TYPE_CHECKING
import logging

from agents.base_agent import BaseAgent

if TYPE_CHECKING:
    from core.model_router import ModelRouter
    from core.prompt_manager import PromptManager
    from core.cost_tracker import CostTracker
    from core.cache_manager import CacheManager


class ControllerAgent(BaseAgent):
    """
    Analyzes Spring MVC Controller files.

    Extracts:
    - Class name and package
    - Request mappings with HTTP methods
    - Service dependencies (@Autowired, @Resource, Constructor)
    - Method parameters and return types

    This is the POC agent to validate the LLM-First approach.
    """

    def __init__(
        self,
        model_router: ModelRouter,
        prompt_manager: PromptManager,
        cost_tracker: CostTracker,
        cache_manager: CacheManager,
        config: Dict[str, Any]
    ):
        """
        Initialize the Controller Agent.

        Args:
            model_router: Router for LLM model selection
            prompt_manager: Manager for prompt templates
            cost_tracker: Tracker for API costs
            cache_manager: Manager for caching results
            config: Agent configuration dictionary
        """
        super().__init__(
            agent_name="controller",
            model_router=model_router,
            prompt_manager=prompt_manager,
            cost_tracker=cost_tracker,
            cache_manager=cache_manager,
            config=config
        )

        self.logger.info("ControllerAgent initialized")

    async def _analyze_impl(
        self,
        file_path: str,
        content: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Actual controller analysis implementation.

        Args:
            file_path: Path to the controller file
            content: File content (already loaded by base class)
            **kwargs: Additional parameters (unused for controller agent)

        Returns:
            Analysis result dictionary with structure:
            {
                "analysis": {
                    "class_name": str,
                    "package": str,
                    "class_level_mapping": str or None,
                    "controller_type": str,
                    "mappings": List[Dict],
                    "dependencies": List[Dict]
                },
                "confidence": float,
                "model_used": str,
                "cost": float
            }
        """
        # Build prompt using PromptManager
        try:
            prompt = self.prompt_manager.build_prompt(
                template_name="controller_analysis",
                context={
                    "file_path": file_path,
                    "code": content
                },
                include_examples=True,
                max_examples=3  # Include up to 3 few-shot examples
            )
        except ValueError as e:
            self.logger.error(f"Failed to build prompt for {file_path}: {e}")
            # Return partial result instead of raising
            return {
                "analysis": {
                    "error": "Failed to build prompt",
                    "error_details": str(e),
                    "class_name": "unknown",
                    "package": "unknown",
                    "mappings": [],
                    "dependencies": []
                },
                "confidence": 0.0,
                "model_used": "none",
                "cost": 0.0
            }

        self.logger.debug(f"Built prompt for {file_path} ({len(prompt)} chars)")

        # Query LLM via ModelRouter
        # Controllers are usually straightforward → use "simple" complexity
        # Max tokens configurable via config, with reasonable default
        max_tokens = self.config.get("agents", {}).get("max_tokens_controller", 2048)

        llm_result = await self._query_llm(
            prompt=prompt,
            complexity="simple",  # Controllers are usually simple
            max_tokens=max_tokens
        )

        # Parse LLM response to extract JSON
        try:
            analysis = self._extract_json_from_response(llm_result["response"])
        except ValueError as e:
            self.logger.error(f"Failed to parse LLM response for {file_path}: {e}")
            # Return partial result with error info
            return {
                "analysis": {
                    "error": "Failed to parse LLM response",
                    "error_details": str(e),
                    "raw_response_preview": llm_result["response"][:500]
                },
                "confidence": 0.0,
                "model_used": llm_result["model"],
                "cost": llm_result["cost"]
            }

        # Validate analysis structure
        if not self._validate_analysis_structure(analysis):
            self.logger.warning(f"Analysis structure validation failed for {file_path}")
            # Lower confidence if structure invalid
            penalty = self.config.get("agents", {}).get("structure_validation_penalty", 0.6)
            if "confidence" in analysis:
                analysis["confidence"] = min(analysis["confidence"], penalty)

        # Extract confidence from analysis (LLM provides this)
        confidence = analysis.get("confidence", 0.5)

        # Build result - confidence is at top level, analysis contains full LLM output
        result = {
            "analysis": analysis,
            "confidence": confidence,  # Promoted to top level for easy access
            "model_used": llm_result["model"],
            "cost": llm_result["cost"]
        }

        self.logger.info(
            f"Analyzed {file_path}: "
            f"{analysis.get('class_name', 'unknown')} "
            f"({len(analysis.get('mappings', []))} mappings, "
            f"confidence={confidence:.2f}, "
            f"cost=${llm_result['cost']:.4f})"
        )

        return result

    def _validate_analysis_structure(self, analysis: Dict[str, Any]) -> bool:
        """
        Validate that analysis has required fields.

        Args:
            analysis: Parsed analysis result

        Returns:
            True if structure is valid, False otherwise
        """
        required_fields = [
            "class_name",
            "package",
            "class_level_mapping",
            "controller_type",
            "mappings",
            "dependencies",
            "confidence",
            "notes"
        ]

        for field in required_fields:
            if field not in analysis:
                self.logger.warning(f"Missing required field: {field}")
                return False

        # Validate mappings structure
        if not isinstance(analysis["mappings"], list):
            self.logger.warning("mappings should be a list")
            return False

        for mapping in analysis["mappings"]:
            required_mapping_fields = ["method_name", "path", "http_method", "parameters", "return_type"]
            for field in required_mapping_fields:
                if field not in mapping:
                    self.logger.warning(f"Mapping missing required field: {field}")
                    return False

        # Validate dependencies structure
        if not isinstance(analysis["dependencies"], list):
            self.logger.warning("dependencies should be a list")
            return False

        for dep in analysis["dependencies"]:
            required_dep_fields = ["field_name", "type", "annotation"]
            for field in required_dep_fields:
                if field not in dep:
                    self.logger.warning(f"Dependency missing required field: {field}")
                    return False

        return True

    def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate controller analysis result.

        Overrides base class to add domain-specific validation.

        Args:
            result: Analysis result dictionary

        Returns:
            True if result is valid, False otherwise
        """
        # First run base validation (confidence check)
        if not super().validate_result(result):
            return False

        # Controller-specific validation
        analysis = result.get("analysis", {})

        # Should have at least a class name
        if not analysis.get("class_name"):
            self.logger.warning("Controller analysis missing class_name")
            return False

        # If confidence is high, should have mappings
        if result.get("confidence", 0) >= 0.9 and not analysis.get("mappings"):
            self.logger.warning("High confidence but no mappings found - suspicious")
            return False

        return True

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return (
            f"<ControllerAgent("
            f"max_tokens={self.config.get('agents', {}).get('max_tokens_controller', 2048)}"
            f")>"
        )
