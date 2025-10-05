"""
Base Agent Class for LLM-driven analysis.

This module provides the abstract base class that all specialized analysis agents
inherit from. It handles common functionality like file loading, LLM querying,
response parsing, and cost tracking.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from pathlib import Path
import logging
from datetime import datetime
import json
import re
import hashlib
from tenacity import retry, stop_after_attempt, wait_exponential

if TYPE_CHECKING:
    from core.model_router import ModelRouter
    from core.prompt_manager import PromptManager
    from core.cost_tracker import CostTracker
    from core.cache_manager import CacheManager


class BaseAgent(ABC):
    """
    Abstract base class for all LLM-driven analysis agents.

    Key responsibilities:
    1. File loading with context management
    2. Prompt construction via PromptManager
    3. LLM querying via ModelRouter
    4. Response parsing (JSON extraction)
    5. Result validation
    6. Cost tracking
    7. Cache management
    8. Error handling and retry logic

    Attributes:
        agent_name: Name of the agent (e.g., "controller", "jsp")
        model_router: ModelRouter instance for LLM queries
        prompt_manager: PromptManager instance for prompt templates
        cost_tracker: CostTracker instance for cost monitoring
        cache_manager: CacheManager instance for result caching
        config: Configuration dictionary
        logger: Logger instance
    """

    def __init__(
        self,
        agent_name: str,
        model_router: ModelRouter,
        prompt_manager: PromptManager,
        cost_tracker: CostTracker,
        cache_manager: CacheManager,
        config: Dict[str, Any]
    ):
        """
        Initialize the base agent.

        Args:
            agent_name: Unique name for this agent
            model_router: Router for LLM model selection
            prompt_manager: Manager for prompt templates
            cost_tracker: Tracker for API costs
            cache_manager: Manager for caching results
            config: Agent configuration dictionary
        """
        self.agent_name = agent_name
        self.model_router = model_router
        self.prompt_manager = prompt_manager
        self.cost_tracker = cost_tracker
        self.cache_manager = cache_manager
        self.config = config
        self.logger = logging.getLogger(f"agents.{agent_name}")

    async def analyze(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        Main analysis method with cache integration.

        This method:
        1. Loads the file content
        2. Checks cache for existing results
        3. If cache miss, calls _analyze_impl() (subclass implementation)
        4. Validates the result
        5. Saves to cache
        6. Returns structured results

        Args:
            file_path: Path to file to analyze
            **kwargs: Agent-specific parameters

        Returns:
            Dictionary containing:
            {
                "file_path": str,
                "analysis": Dict,  # Agent-specific structure
                "confidence": float,
                "model_used": str,
                "cost": float,
                "timestamp": str,
                "cached": bool
            }
        """
        # Load file content
        content = self._load_file_with_context(file_path)

        # Check cache
        cached_result = self.cache_manager.get(
            agent_name=self.agent_name,
            file_path=file_path,
            file_content=content
        )

        if cached_result:
            self.logger.info(f"Cache HIT for {file_path}")
            # Track cache hit in cost tracker
            self.cost_tracker.record(
                agent=self.agent_name,
                model="cache",
                tokens={"input": 0, "output": 0},
                cost=0.0,
                cached=True
            )
            cached_result["cached"] = True
            return cached_result

        # Cache miss - perform actual analysis
        self.logger.info(f"Cache MISS for {file_path}")
        result = await self._analyze_impl(file_path, content, **kwargs)

        # Add metadata
        result["file_path"] = file_path
        result["timestamp"] = self._get_timestamp()
        result["cached"] = False

        # Validate
        is_valid = self.validate_result(result)
        if not is_valid:
            self.logger.warning(
                f"Low confidence result ({result.get('confidence', 0)}) for {file_path}"
            )

        # Save to cache
        self.cache_manager.save(
            agent_name=self.agent_name,
            file_path=file_path,
            file_content=content,
            result=result
        )

        return result

    @abstractmethod
    async def _analyze_impl(self, file_path: str, content: str, **kwargs) -> Dict[str, Any]:
        """
        Actual analysis implementation - MUST be implemented by subclasses.

        Args:
            file_path: Path to file being analyzed
            content: File content (already loaded)
            **kwargs: Agent-specific parameters

        Returns:
            Dictionary with analysis results (structure varies by agent):
            {
                "analysis": Dict,  # Agent-specific structure
                "confidence": float,
                "model_used": str,
                "cost": float
            }
        """
        pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def _query_llm(
        self,
        prompt: str,
        complexity: str = "medium",
        max_tokens: int = 4096,
        force_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query LLM via ModelRouter with automatic cost tracking and retries.

        This method handles:
        - Model routing based on complexity
        - Automatic escalation if confidence is low
        - Cost tracking
        - Error handling and retries (up to 3 attempts with exponential backoff)

        Args:
            prompt: The prompt to send to the LLM
            complexity: Task complexity - "simple" | "medium" | "complex"
            max_tokens: Maximum response tokens
            force_model: Force specific model (bypasses routing)

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
            Exception: If LLM API call fails after all retries
        """
        try:
            result = await self.model_router.query(
                prompt=prompt,
                complexity=complexity,
                max_tokens=max_tokens,
                force_model=force_model
            )

            # Track cost
            self.cost_tracker.record(
                agent=self.agent_name,
                model=result["model"],
                tokens=result["tokens"],
                cost=result["cost"],
                cached=False
            )

            self.logger.info(
                f"LLM query successful: model={result['model']}, "
                f"cost=${result['cost']:.4f}, confidence={result.get('confidence', 'N/A')}"
            )

            return result

        except Exception as e:
            self.logger.error(f"LLM API error: {e}")
            raise

    def _load_file_with_context(
        self,
        file_path: str,
        target_line: Optional[int] = None,
        context_lines: int = 20,
        max_lines: int = 2000
    ) -> str:
        """
        Load file with optional context window.

        If target_line is specified, return ±context_lines around it.
        Otherwise return full file (with size check and warning).

        Args:
            file_path: Path to the file
            target_line: Optional specific line number to focus on
            context_lines: Number of lines before/after target_line
            max_lines: Maximum number of lines to load (safety limit)

        Returns:
            File content as string

        Raises:
            FileNotFoundError: If file doesn't exist
            UnicodeDecodeError: If file encoding is not UTF-8 or latin-1
            ValueError: If file is too large
        """
        path = Path(file_path).resolve()

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            # Try with different encoding
            self.logger.warning(f"UTF-8 decode failed, trying latin-1 for {file_path}")
            with open(path, 'r', encoding='latin-1') as f:
                lines = f.readlines()

        # Full file
        if target_line is None:
            if len(lines) > max_lines:
                raise ValueError(
                    f"File too large ({len(lines)} lines, max {max_lines}). "
                    f"Use target_line parameter for context window."
                )
            if len(lines) > 1000:
                self.logger.warning(
                    f"Large file ({len(lines)} lines) in {file_path}. "
                    "Consider using chunking or context windows."
                )
            return ''.join(lines)

        # Context window around target line
        start = max(0, target_line - context_lines)
        end = min(len(lines), target_line + context_lines)

        self.logger.debug(
            f"Loading context window: lines {start}-{end} from {file_path}"
        )

        return ''.join(lines[start:end])

    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response, handling various formats.

        This method handles:
        - Raw JSON: {"key": "value"}
        - Markdown code blocks: ```json\n{...}\n```
        - Mixed text with JSON: "Here's the result:\n```json..."
        - JSON with trailing text

        Args:
            response: Raw LLM response string

        Returns:
            Parsed JSON as dictionary

        Raises:
            ValueError: If no valid JSON found in response
        """
        # Try raw JSON first (fastest path)
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass

        # Try to extract from markdown code block
        match = re.search(r'```(?:json)?\s*\n(.*?)\n```', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find any JSON object in the response
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        # Try to find JSON array
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        # Log the response for debugging (don't log full content in production)
        self.logger.error(f"Could not extract JSON from response (length: {len(response)})")
        self.logger.debug(f"Response preview: {response[:500]}")
        raise ValueError(
            f"Could not extract valid JSON from LLM response. "
            f"Response preview: {response[:200]}"
        )

    def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate analysis result.

        Default implementation checks confidence threshold.
        Override in subclasses for domain-specific validation.

        Args:
            result: Analysis result dictionary

        Returns:
            True if result is valid, False otherwise
        """
        min_confidence = self.config.get("agents", {}).get("min_confidence", 0.7)
        confidence = result.get("confidence", 0)

        is_valid = confidence >= min_confidence

        if not is_valid:
            self.logger.warning(
                f"Result validation failed: confidence {confidence:.2f} < {min_confidence}"
            )

        return is_valid

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO 8601 format."""
        return datetime.now().isoformat()

    def _calculate_file_hash(self, content: str) -> str:
        """
        Calculate hash of file content for cache key.

        Args:
            content: File content string

        Returns:
            SHA256 hash as hex string
        """
        return hashlib.sha256(content.encode()).hexdigest()

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return f"<{self.__class__.__name__}(agent_name='{self.agent_name}')>"
