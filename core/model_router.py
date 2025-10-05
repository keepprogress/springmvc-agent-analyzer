"""
Model Router for hierarchical LLM selection.

This module implements cost-optimized model routing by trying cheaper models first
and escalating to more capable (expensive) models only when needed based on confidence scores.
"""

from typing import Dict, Any, Optional
import logging
import os
import yaml
import json
import re
from pathlib import Path
from anthropic import AsyncAnthropic
import anthropic
import httpx


class ModelRouter:
    """
    Routes queries to appropriate Claude model based on complexity and confidence.

    Strategy:
    1. Simple tasks → Try Haiku ($0.25/1M tokens input, $1.25/1M output)
    2. If Haiku confidence < 0.9 → Escalate to Sonnet ($3/1M input, $15/1M output)
    3. If Sonnet confidence < 0.85 → Escalate to Opus ($15/1M input, $75/1M output)

    Expected Savings: 50-70% cost reduction vs Sonnet-only approach

    Attributes:
        llm_config: LLM configuration from config.yaml
        client: Anthropic API client
        models: Model tier definitions with costs
        thresholds: Confidence thresholds for escalation
        logger: Logger instance
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the Model Router.

        Args:
            config_path: Path to configuration file

        Raises:
            FileNotFoundError: If config file not found
            KeyError: If required config keys missing
            ValueError: If ANTHROPIC_API_KEY not set
        """
        # Load configuration
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_file) as f:
            config = yaml.safe_load(f)

        self.llm_config = config["llm"]

        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Please set it in .env or export ANTHROPIC_API_KEY=your_key"
            )

        # Configure timeout: 60s for read operations, 10s for connect
        timeout = httpx.Timeout(60.0, connect=10.0)
        self.client = AsyncAnthropic(api_key=api_key, timeout=timeout)
        self.logger = logging.getLogger("core.model_router")

        # Model definitions with costs
        self.models = {
            "haiku": {
                "name": self.llm_config["routing"]["screening_model"],
                "cost_per_mtok_input": self.llm_config["routing"]["screening_cost_per_mtok_input"],
                "cost_per_mtok_output": self.llm_config["routing"]["screening_cost_per_mtok_output"],
                "max_tokens": 8192,
                "best_for": ["simple controllers", "basic services", "standard CRUD"]
            },
            "sonnet": {
                "name": self.llm_config["routing"]["analysis_model"],
                "cost_per_mtok_input": self.llm_config["routing"]["analysis_cost_per_mtok_input"],
                "cost_per_mtok_output": self.llm_config["routing"]["analysis_cost_per_mtok_output"],
                "max_tokens": 8192,
                "best_for": ["complex JSP", "nested mappers", "SQL analysis"]
            },
            "opus": {
                "name": self.llm_config["routing"]["critical_model"],
                "cost_per_mtok_input": self.llm_config["routing"]["critical_cost_per_mtok_input"],
                "cost_per_mtok_output": self.llm_config["routing"]["critical_cost_per_mtok_output"],
                "max_tokens": 4096,
                "best_for": ["ambiguous deps", "complex procedures", "edge cases"]
            }
        }

        # Confidence thresholds for escalation
        self.thresholds = self.llm_config["thresholds"]

        self.logger.info(
            f"Model Router initialized: Haiku → Sonnet → Opus "
            f"(thresholds: {self.thresholds['screening_confidence']}, "
            f"{self.thresholds['analysis_confidence']})"
        )

    async def query(
        self,
        prompt: str,
        complexity: str = "medium",
        max_tokens: int = 4096,
        force_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute hierarchical query with automatic escalation.

        Args:
            prompt: The prompt to send to the LLM
            complexity: Task complexity - "simple" | "medium" | "complex"
            max_tokens: Maximum response tokens
            force_model: Force specific model tier (bypasses routing)

        Returns:
            {
                "response": str,
                "model": str,
                "cost": float,
                "tokens": {"input": int, "output": int},
                "confidence": float,
                "escalations": int
            }

        Raises:
            anthropic.APIError: If API call fails
            ValueError: If force_model is invalid
        """
        # Validate force_model if provided
        if force_model and force_model not in self.models:
            raise ValueError(
                f"Invalid force_model: {force_model}. "
                f"Must be one of: {list(self.models.keys())}"
            )

        # If forced model specified, use it directly
        if force_model:
            self.logger.info(f"Using forced model: {force_model}")
            result = await self._query_model(force_model, prompt, max_tokens)
            confidence = self._extract_confidence(result["response"])
            return {**result, "confidence": confidence, "escalations": 0}

        # Hierarchical routing based on complexity
        escalations = 0

        # Step 1: Try Haiku for simple/medium tasks
        if complexity in ["simple", "medium"]:
            self.logger.info(f"Trying Haiku (complexity={complexity})")
            result = await self._query_model("haiku", prompt, max_tokens)
            confidence = self._extract_confidence(result["response"])

            if confidence >= self.thresholds["screening_confidence"]:
                self.logger.info(
                    f"✅ Haiku sufficient (confidence={confidence:.2f}), "
                    f"cost=${result['cost']:.4f}"
                )
                return {**result, "confidence": confidence, "escalations": 0}

            self.logger.info(
                f"⬆️  Haiku low confidence ({confidence:.2f}), escalating to Sonnet"
            )
            escalations += 1

        # Step 2: Try Sonnet (or if complexity is "complex")
        self.logger.info("Trying Sonnet")
        result = await self._query_model("sonnet", prompt, max_tokens)
        confidence = self._extract_confidence(result["response"])

        if confidence >= self.thresholds["analysis_confidence"]:
            self.logger.info(
                f"✅ Sonnet sufficient (confidence={confidence:.2f}), "
                f"cost=${result['cost']:.4f}, escalations={escalations}"
            )
            return {**result, "confidence": confidence, "escalations": escalations}

        # Step 3: Escalate to Opus (last resort)
        self.logger.warning(
            f"⬆️  Sonnet low confidence ({confidence:.2f}), escalating to Opus"
        )
        escalations += 1

        self.logger.info("Trying Opus (highest tier)")
        result = await self._query_model("opus", prompt, max_tokens)
        confidence = self._extract_confidence(result["response"])

        self.logger.info(
            f"✅ Opus result (confidence={confidence:.2f}), "
            f"cost=${result['cost']:.4f}, escalations={escalations}"
        )

        return {**result, "confidence": confidence, "escalations": escalations}

    async def _query_model(
        self,
        model_tier: str,
        prompt: str,
        max_tokens: int
    ) -> Dict[str, Any]:
        """
        Execute actual API call to specified model tier.

        Args:
            model_tier: Model tier ("haiku", "sonnet", "opus")
            prompt: The prompt to send
            max_tokens: Maximum response tokens

        Returns:
            {
                "response": str,
                "model": str,
                "cost": float,
                "tokens": {"input": int, "output": int}
            }

        Raises:
            anthropic.APIError: If API call fails
        """
        model_info = self.models[model_tier]

        try:
            # Call Anthropic API (async)
            response = await self.client.messages.create(
                model=model_info["name"],
                max_tokens=min(max_tokens, model_info["max_tokens"]),
                temperature=self.llm_config["api"]["temperature"],
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract tokens
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            # Calculate cost
            cost = self._calculate_cost(
                model_tier=model_tier,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )

            # Extract text response
            response_text = response.content[0].text

            self.logger.debug(
                f"{model_tier.upper()}: {input_tokens} in, {output_tokens} out, ${cost:.4f}"
            )

            return {
                "response": response_text,
                "model": model_info["name"],
                "cost": cost,
                "tokens": {
                    "input": input_tokens,
                    "output": output_tokens
                }
            }

        except anthropic.APIError as e:
            self.logger.error(f"API error with {model_tier}: {e}")
            raise

    def _extract_confidence(self, response: str) -> float:
        """
        Extract confidence score from LLM response.

        Expects JSON response with "confidence" field.
        Falls back to 0.5 if not found or parsing fails.

        Args:
            response: LLM response text

        Returns:
            Confidence score (0.0 - 1.0)
        """
        try:
            # Try 1: Look for confidence with flexible quotes and scientific notation
            # Matches: "confidence": 0.95, 'confidence': 0.95, confidence:0.95
            pattern = r'["\']?confidence["\']?\s*:\s*([0-9.]+(?:[eE][+-]?[0-9]+)?)'
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                confidence = float(match.group(1))
                # Clamp to valid range
                if confidence < 0.0 or confidence > 1.0:
                    self.logger.warning(
                        f"Confidence out of range: {confidence}, clamping to [0,1]"
                    )
                return max(0.0, min(1.0, confidence))

            # Try 2: Parse as complete JSON object (simple case)
            json_match = re.search(r'\{[^{}]*"confidence"[^{}]*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                if "confidence" in data:
                    confidence = float(data["confidence"])
                    return max(0.0, min(1.0, confidence))

            # Try 3: Multi-line nested JSON (more expensive but comprehensive)
            brace_count = 0
            start_idx = response.find('{')
            if start_idx != -1:
                for i, char in enumerate(response[start_idx:], start=start_idx):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_str = response[start_idx:i+1]
                            data = json.loads(json_str)
                            if "confidence" in data:
                                confidence = float(data["confidence"])
                                return max(0.0, min(1.0, confidence))
                            break

        except (json.JSONDecodeError, ValueError, AttributeError) as e:
            self.logger.debug(f"Could not extract confidence: {e}")

        # Fallback: medium confidence
        self.logger.debug("No confidence found, using default 0.5")
        return 0.5

    def _calculate_cost(
        self,
        model_tier: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Calculate cost based on token usage.

        Args:
            model_tier: Model tier ("haiku", "sonnet", "opus")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        model_info = self.models[model_tier]

        input_cost = (input_tokens / 1_000_000) * model_info["cost_per_mtok_input"]
        output_cost = (output_tokens / 1_000_000) * model_info["cost_per_mtok_output"]

        total_cost = input_cost + output_cost

        return round(total_cost, 6)  # Round to 6 decimal places

    def get_model_info(self, model_tier: str) -> Dict[str, Any]:
        """
        Get information about a specific model tier.

        Args:
            model_tier: Model tier ("haiku", "sonnet", "opus")

        Returns:
            Model information dictionary

        Raises:
            KeyError: If model_tier not found
        """
        if model_tier not in self.models:
            raise KeyError(
                f"Unknown model tier: {model_tier}. "
                f"Available: {list(self.models.keys())}"
            )

        return self.models[model_tier].copy()

    def get_all_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all available model tiers.

        Returns:
            Dictionary of model tier -> model info
        """
        return {tier: info.copy() for tier, info in self.models.items()}

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return (
            f"<ModelRouter(models={list(self.models.keys())}, "
            f"thresholds={self.thresholds})>"
        )
