"""
Procedure Agent for Oracle PL/SQL stored procedure analysis.

This module implements stored procedure analysis to extract parameters,
SQL operations, cursors, control flow, and business logic patterns.
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


class ProcedureAgent(BaseAgent):
    """
    Analyzes Oracle PL/SQL stored procedures.

    Extracts:
    - Procedure name, package, and parameters (IN/OUT/IN OUT)
    - SQL operations (SELECT, INSERT, UPDATE, DELETE, MERGE)
    - Cursors and result sets
    - Control flow (loops, conditionals, exceptions, transactions)
    - Business logic patterns (validation, calculation, batch processing)
    - Tables accessed

    Procedure analysis is complex due to PL/SQL logic → use complexity="complex"
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
        Initialize the Procedure Agent.

        Args:
            model_router: Router for LLM model selection
            prompt_manager: Manager for prompt templates
            cost_tracker: Tracker for API costs
            cache_manager: Manager for caching results
            config: Agent configuration dictionary
        """
        super().__init__(
            agent_name="procedure",
            model_router=model_router,
            prompt_manager=prompt_manager,
            cost_tracker=cost_tracker,
            cache_manager=cache_manager,
            config=config
        )

        self.logger.info("ProcedureAgent initialized")

    async def _analyze_impl(
        self,
        file_path: str,
        content: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Actual procedure analysis implementation.

        Args:
            file_path: Path to the procedure file
            content: File content (already loaded by base class)
            **kwargs: Additional parameters (unused for procedure agent)

        Returns:
            Analysis result dictionary with structure:
            {
                "analysis": {
                    "procedure_name": str,
                    "package_name": str or null,
                    "parameters": List[Dict],
                    "sql_operations": List[Dict],
                    "cursors": List[Dict],
                    "control_flow": Dict,
                    "business_patterns": List[str],
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
                template_name="procedure_analysis",
                context={
                    "file_path": file_path,
                    "code": content
                },
                include_examples=True,
                max_examples=2  # Procedures are verbose, limit examples
            )
        except ValueError as e:
            self.logger.error(f"Failed to build prompt for {file_path}: {e}")
            # Return partial result instead of raising
            return {
                "analysis": {
                    "error": "Failed to build prompt",
                    "error_details": str(e),
                    "procedure_name": "unknown",
                    "package_name": None,
                    "parameters": [],
                    "sql_operations": [],
                    "cursors": [],
                    "tables_accessed": []
                },
                "confidence": 0.0,
                "model_used": "none",
                "cost": 0.0
            }

        self.logger.debug(f"Built prompt for {file_path} ({len(prompt)} chars)")

        # Query LLM via ModelRouter
        # Stored procedures are complex (PL/SQL + SQL + business logic) → use "complex"
        max_tokens = self.config.get("agents", {}).get("max_tokens_procedure", 4096)

        llm_result = await self._query_llm(
            prompt=prompt,
            complexity="complex",  # Procedures are most complex
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
            if "confidence" in analysis:
                analysis["confidence"] = min(analysis["confidence"], 0.6)

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
        num_params = len(analysis.get("parameters", []))
        num_ops = len(analysis.get("sql_operations", []))
        num_cursors = len(analysis.get("cursors", []))
        patterns = ", ".join(analysis.get("business_patterns", []))
        complexity = analysis.get("control_flow", {}).get("complexity", "unknown")

        self.logger.info(
            f"Analyzed {file_path}: "
            f"{analysis.get('procedure_name', 'unknown')} "
            f"({num_params} params, {num_ops} SQL ops, {num_cursors} cursors, "
            f"complexity={complexity}, patterns=[{patterns}], "
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
            "procedure_name",
            "package_name",
            "parameters",
            "sql_operations",
            "cursors",
            "control_flow",
            "business_patterns",
            "tables_accessed",
            "confidence",
            "notes"
        ]

        for field in required_fields:
            if field not in analysis:
                self.logger.warning(f"Missing required field: {field}")
                return False

        # Validate parameters structure
        if not isinstance(analysis["parameters"], list):
            self.logger.warning("parameters should be a list")
            return False

        for param in analysis["parameters"]:
            required_param_fields = ["name", "data_type", "direction"]
            for field in required_param_fields:
                if field not in param:
                    self.logger.warning(f"Parameter missing required field: {field}")
                    return False

        # Validate sql_operations structure
        if not isinstance(analysis["sql_operations"], list):
            self.logger.warning("sql_operations should be a list")
            return False

        # Validate control_flow structure
        if not isinstance(analysis["control_flow"], dict):
            self.logger.warning("control_flow should be a dict")
            return False

        if "complexity" not in analysis["control_flow"]:
            self.logger.warning("control_flow missing complexity field")
            return False

        return True

    def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate procedure analysis result.

        Overrides base class to add domain-specific validation.

        Args:
            result: Analysis result dictionary

        Returns:
            True if result is valid, False otherwise
        """
        # First run base validation (confidence check)
        if not super().validate_result(result):
            return False

        # Procedure-specific validation
        analysis = result.get("analysis", {})

        # Should have procedure name
        if not analysis.get("procedure_name"):
            self.logger.warning("Procedure analysis missing procedure_name")
            return False

        # If confidence is high, should have some SQL operations
        if result.get("confidence", 0) >= 0.9 and not analysis.get("sql_operations"):
            self.logger.warning("High confidence but no SQL operations - might be invalid")
            # This could be valid for some utility procedures, so just warn

        return True

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return (
            f"<ProcedureAgent("
            f"max_tokens={self.config.get('agents', {}).get('max_tokens_procedure', 4096)}, "
            f"complexity=complex"
            f")>"
        )
