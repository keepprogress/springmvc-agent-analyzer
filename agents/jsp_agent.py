"""
JSP Agent for JavaServer Pages analysis.

This module implements JSP file analysis to extract page directives,
tag libraries, model attributes, forms, and backend dependencies.
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


class JSPAgent(BaseAgent):
    """
    Analyzes JSP (JavaServer Pages) files.

    Extracts:
    - Page directives (imports, content type, session, error page)
    - Tag library declarations (JSTL, Spring Form, custom)
    - Model attributes and data bindings
    - Form submissions and field mappings
    - Backend dependencies (controller endpoints, AJAX calls)
    - Dynamic content (JSTL loops, conditionals, AJAX)

    JSP analysis is more complex than Controllers due to mixed HTML/Java/EL syntax,
    so we use complexity="medium" for model routing.
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
        Initialize the JSP Agent.

        Args:
            model_router: Router for LLM model selection
            prompt_manager: Manager for prompt templates
            cost_tracker: Tracker for API costs
            cache_manager: Manager for caching results
            config: Agent configuration dictionary
        """
        super().__init__(
            agent_name="jsp",
            model_router=model_router,
            prompt_manager=prompt_manager,
            cost_tracker=cost_tracker,
            cache_manager=cache_manager,
            config=config
        )

        self.logger.info("JSPAgent initialized")

    async def _analyze_impl(
        self,
        file_path: str,
        content: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Actual JSP analysis implementation.

        Args:
            file_path: Path to the JSP file
            content: File content (already loaded by base class)
            **kwargs: Additional parameters (unused for JSP agent)

        Returns:
            Analysis result dictionary with structure:
            {
                "analysis": {
                    "file_name": str,
                    "page_directives": Dict,
                    "tag_libraries": List[Dict],
                    "model_attributes": List[Dict],
                    "forms": List[Dict],
                    "backend_dependencies": List[Dict],
                    "dynamic_content": Dict
                },
                "confidence": float,
                "model_used": str,
                "cost": float
            }
        """
        # Build prompt using PromptManager
        try:
            prompt = self.prompt_manager.build_prompt(
                template_name="jsp_analysis",
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
                    "file_name": file_path.split("/")[-1] if "/" in file_path else file_path.split("\\")[-1],
                    "page_directives": {},
                    "tag_libraries": [],
                    "model_attributes": [],
                    "forms": [],
                    "backend_dependencies": [],
                    "dynamic_content": {}
                },
                "confidence": 0.0,
                "model_used": "none",
                "cost": 0.0
            }

        self.logger.debug(f"Built prompt for {file_path} ({len(prompt)} chars)")

        # Query LLM via ModelRouter
        # JSP files are more complex than controllers → use "medium" complexity
        # Max tokens configurable via config, with higher default due to JSP complexity
        max_tokens = self.config.get("agents", {}).get("max_tokens_jsp", 3072)

        llm_result = await self._query_llm(
            prompt=prompt,
            complexity="medium",  # JSPs are more complex than controllers
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

        # Log summary
        num_models = len(analysis.get("model_attributes", []))
        num_forms = len(analysis.get("forms", []))
        num_deps = len(analysis.get("backend_dependencies", []))

        self.logger.info(
            f"Analyzed {file_path}: "
            f"{analysis.get('file_name', 'unknown')} "
            f"({num_models} model attrs, {num_forms} forms, {num_deps} deps, "
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
            "file_name",
            "page_directives",
            "tag_libraries",
            "model_attributes",
            "forms",
            "backend_dependencies",
            "dynamic_content",
            "confidence",
            "notes"
        ]

        for field in required_fields:
            if field not in analysis:
                self.logger.warning(f"Missing required field: {field}")
                return False

        # Validate page_directives structure
        if not isinstance(analysis["page_directives"], dict):
            self.logger.warning("page_directives should be a dict")
            return False

        # Validate tag_libraries structure
        if not isinstance(analysis["tag_libraries"], list):
            self.logger.warning("tag_libraries should be a list")
            return False

        for taglib in analysis["tag_libraries"]:
            required_taglib_fields = ["prefix", "uri", "type"]
            for field in required_taglib_fields:
                if field not in taglib:
                    self.logger.warning(f"Tag library missing required field: {field}")
                    return False

        # Validate model_attributes structure
        if not isinstance(analysis["model_attributes"], list):
            self.logger.warning("model_attributes should be a list")
            return False

        for attr in analysis["model_attributes"]:
            required_attr_fields = ["name", "type", "usage"]
            for field in required_attr_fields:
                if field not in attr:
                    self.logger.warning(f"Model attribute missing required field: {field}")
                    return False

        # Validate forms structure (optional, but if present should be valid)
        if not isinstance(analysis["forms"], list):
            self.logger.warning("forms should be a list")
            return False

        # Validate backend_dependencies structure
        if not isinstance(analysis["backend_dependencies"], list):
            self.logger.warning("backend_dependencies should be a list")
            return False

        # Validate dynamic_content structure
        if not isinstance(analysis["dynamic_content"], dict):
            self.logger.warning("dynamic_content should be a dict")
            return False

        return True

    def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate JSP analysis result.

        Overrides base class to add domain-specific validation.

        Args:
            result: Analysis result dictionary

        Returns:
            True if result is valid, False otherwise
        """
        # First run base validation (confidence check)
        if not super().validate_result(result):
            return False

        # JSP-specific validation
        analysis = result.get("analysis", {})

        # Should have at least a file name
        if not analysis.get("file_name"):
            self.logger.warning("JSP analysis missing file_name")
            return False

        # If confidence is high and no model attributes, might be suspicious
        # (most JSPs display some data)
        if result.get("confidence", 0) >= 0.9 and not analysis.get("model_attributes"):
            self.logger.warning("High confidence but no model attributes - might be a static page")
            # This is not necessarily invalid, just noteworthy

        return True

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return (
            f"<JSPAgent("
            f"max_tokens={self.config.get('agents', {}).get('max_tokens_jsp', 3072)}, "
            f"complexity=medium"
            f")>"
        )
