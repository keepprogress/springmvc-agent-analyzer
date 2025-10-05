"""
Mapper Agent for MyBatis XML Mapper analysis.

This module implements MyBatis mapper file analysis to extract SQL statements,
parameter mappings, result mappings, and dynamic SQL patterns.
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


class MapperAgent(BaseAgent):
    """
    Analyzes MyBatis XML Mapper files.

    Extracts:
    - Namespace (maps to Java DAO/Mapper interface)
    - SQL statements (select, insert, update, delete)
    - Parameter mappings (#{} and ${} syntax)
    - Result mappings (resultMap, resultType)
    - Dynamic SQL elements (<if>, <choose>, <foreach>)
    - Tables accessed and operation complexity

    Mapper analysis is medium complexity due to XML parsing and SQL extraction.
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
        Initialize the Mapper Agent.

        Args:
            model_router: Router for LLM model selection
            prompt_manager: Manager for prompt templates
            cost_tracker: Tracker for API costs
            cache_manager: Manager for caching results
            config: Agent configuration dictionary
        """
        super().__init__(
            agent_name="mapper",
            model_router=model_router,
            prompt_manager=prompt_manager,
            cost_tracker=cost_tracker,
            cache_manager=cache_manager,
            config=config
        )

        self.logger.info("MapperAgent initialized")

    async def _analyze_impl(
        self,
        file_path: str,
        content: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Actual mapper analysis implementation.

        Args:
            file_path: Path to the mapper XML file
            content: File content (already loaded by base class)
            **kwargs: Additional parameters (unused for mapper agent)

        Returns:
            Analysis result dictionary with structure:
            {
                "analysis": {
                    "file_name": str,
                    "namespace": str,
                    "statements": List[Dict],
                    "result_maps": List[Dict],
                    "tables_accessed": List[str]
                },
                "confidence": float,
                "model_used": str,
                "cost": float
            }
        """
        # Build prompt using PromptManager
        try:
            prompt = self.prompt_manager.build_prompt(
                template_name="mapper_analysis",
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
                    "namespace": "unknown",
                    "statements": [],
                    "result_maps": [],
                    "tables_accessed": []
                },
                "confidence": 0.0,
                "model_used": "none",
                "cost": 0.0
            }

        self.logger.debug(f"Built prompt for {file_path} ({len(prompt)} chars)")

        # Query LLM via ModelRouter
        # Mapper XML is medium complexity (XML + SQL parsing)
        max_tokens = self.config.get("agents", {}).get("max_tokens_mapper", 3072)

        llm_result = await self._query_llm(
            prompt=prompt,
            complexity="medium",  # Mappers are medium complexity
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
        num_statements = len(analysis.get("statements", []))
        num_result_maps = len(analysis.get("result_maps", []))
        tables = ", ".join(analysis.get("tables_accessed", []))

        self.logger.info(
            f"Analyzed {file_path}: "
            f"{analysis.get('namespace', 'unknown')} "
            f"({num_statements} statements, {num_result_maps} resultMaps, tables=[{tables}], "
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
            "namespace",
            "statements",
            "result_maps",
            "tables_accessed",
            "confidence",
            "notes"
        ]

        for field in required_fields:
            if field not in analysis:
                self.logger.warning(f"Missing required field: {field}")
                return False

        # Validate statements structure
        if not isinstance(analysis["statements"], list):
            self.logger.warning("statements should be a list")
            return False

        for stmt in analysis["statements"]:
            required_stmt_fields = ["id", "type", "sql", "parameters", "tables", "complexity"]
            for field in required_stmt_fields:
                if field not in stmt:
                    self.logger.warning(f"Statement missing required field: {field}")
                    return False

        # Validate result_maps structure (optional but if present should be valid)
        if not isinstance(analysis["result_maps"], list):
            self.logger.warning("result_maps should be a list")
            return False

        # Validate tables_accessed
        if not isinstance(analysis["tables_accessed"], list):
            self.logger.warning("tables_accessed should be a list")
            return False

        return True

    def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate mapper analysis result.

        Overrides base class to add domain-specific validation.

        Args:
            result: Analysis result dictionary

        Returns:
            True if result is valid, False otherwise
        """
        # First run base validation (confidence check)
        if not super().validate_result(result):
            return False

        # Mapper-specific validation
        analysis = result.get("analysis", {})

        # Should have namespace
        if not analysis.get("namespace"):
            self.logger.warning("Mapper analysis missing namespace")
            return False

        # If confidence is high, should have some statements
        if result.get("confidence", 0) >= 0.9 and not analysis.get("statements"):
            self.logger.warning("High confidence but no SQL statements found - suspicious")
            return False

        return True

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return (
            f"<MapperAgent("
            f"max_tokens={self.config.get('agents', {}).get('max_tokens_mapper', 3072)}, "
            f"complexity=medium"
            f")>"
        )
