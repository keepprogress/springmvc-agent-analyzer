# Implementation Plan - SpringMVC Agent Analyzer

**Version**: 0.1.0-alpha
**Start Date**: 2025-10-05
**Target Completion**: 14 weeks (2025-12-30)
**Philosophy**: LLM-First, Cost-Conscious, Iterative Validation

---

## Overview

This plan implements a **complete paradigm shift** from parser-heavy to **Agent-based analysis** for legacy SpringMVC codebases. Each phase includes **validation checkpoints** to ensure we're on the right track.

**Critical Success Factor**: Phase 2 POC must demonstrate:
- ✅ Accuracy >= 90%
- ✅ Cost <= $1 per project (medium size)
- ✅ Maintenance effort << parser approach

If POC fails, we pivot or refine strategy.

---

## Phase 1: Foundation Infrastructure (Week 1-2, 10 days)

**Goal**: Build core infrastructure that all agents depend on.

**Deliverables**:
- Base Agent framework
- Model Router with cost optimization
- Prompt Manager with learning capability
- Semantic Cache
- Cost Tracker
- Configuration management

---

### Phase 1.1: Base Agent Class (Days 1-2)

**File**: `agents/base_agent.py`

**Requirements**:
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from anthropic import Anthropic
import anthropic
from core.model_router import ModelRouter
from core.prompt_manager import PromptManager
from core.cost_tracker import CostTracker
import logging

class BaseAgent(ABC):
    """
    Base class for all LLM-driven analysis agents.

    Key responsibilities:
    1. File loading and preprocessing
    2. Prompt construction with context
    3. LLM querying via ModelRouter
    4. Response parsing and validation
    5. Cost tracking
    6. Error handling and retry logic
    """

    def __init__(
        self,
        agent_name: str,
        model_router: ModelRouter,
        prompt_manager: PromptManager,
        cost_tracker: CostTracker,
        config: Dict[str, Any]
    ):
        self.agent_name = agent_name
        self.model_router = model_router
        self.prompt_manager = prompt_manager
        self.cost_tracker = cost_tracker
        self.config = config
        self.logger = logging.getLogger(f"agents.{agent_name}")

    @abstractmethod
    async def analyze(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        Main analysis method - must be implemented by subclasses.

        Args:
            file_path: Path to file to analyze
            **kwargs: Agent-specific parameters

        Returns:
            {
                "file_path": str,
                "analysis": Dict,  # Agent-specific structure
                "confidence": float,
                "model_used": str,
                "cost": float,
                "timestamp": str
            }
        """
        pass

    async def _query_llm(
        self,
        prompt: str,
        complexity: str = "medium",
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Query LLM via ModelRouter with cost tracking.

        Args:
            prompt: The prompt to send
            complexity: "simple" | "medium" | "complex"
            max_tokens: Maximum response tokens

        Returns:
            {
                "response": str,
                "model": str,
                "cost": float,
                "tokens": {"input": int, "output": int}
            }
        """
        try:
            result = await self.model_router.query(
                prompt=prompt,
                complexity=complexity,
                max_tokens=max_tokens
            )

            # Track cost
            self.cost_tracker.record(
                agent=self.agent_name,
                model=result["model"],
                tokens=result["tokens"],
                cost=result["cost"]
            )

            return result

        except anthropic.APIError as e:
            self.logger.error(f"LLM API error: {e}")
            raise

    def _load_file_with_context(
        self,
        file_path: str,
        target_line: Optional[int] = None,
        context_lines: int = 20
    ) -> str:
        """
        Load file with optional context window.

        If target_line specified, return ±context_lines around it.
        Otherwise return full file (with size check).
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if target_line is None:
            # Full file - check size
            if len(lines) > 1000:
                self.logger.warning(
                    f"Large file ({len(lines)} lines), consider chunking"
                )
            return ''.join(lines)

        # Context window
        start = max(0, target_line - context_lines)
        end = min(len(lines), target_line + context_lines)
        return ''.join(lines[start:end])

    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response, handling markdown code blocks.

        Supports:
        - Raw JSON: {"key": "value"}
        - Markdown: ```json\n{...}\n```
        - With explanation: "Here's the analysis:\n```json..."
        """
        import json
        import re

        # Try raw JSON first
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass

        # Extract from markdown code block
        match = re.search(r'```(?:json)?\s*\n(.*?)\n```', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Last resort: find any {...} block
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not extract JSON from response: {response[:200]}")

    async def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        Optional validation hook - override in subclasses.

        Default: Check confidence threshold.
        """
        min_confidence = self.config.get("min_confidence", 0.7)
        return result.get("confidence", 0) >= min_confidence
```

**Validation**:
- Unit test: Mock LLM responses, verify cost tracking
- Test error handling (API timeout, invalid JSON)
- Test file loading with various encodings

---

### Phase 1.2: Model Router (Days 3-4)

**File**: `core/model_router.py`

**Requirements**:
```python
from typing import Dict, Any, Optional
from anthropic import Anthropic
import anthropic
import yaml
import logging

class ModelRouter:
    """
    Routes queries to appropriate model based on complexity and confidence.

    Strategy:
    1. Try Haiku (cheapest) for simple tasks
    2. Escalate to Sonnet if Haiku confidence < threshold
    3. Escalate to Opus for critical decisions

    Saves 50%+ cost while maintaining accuracy.
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path) as f:
            config = yaml.safe_load(f)

        self.llm_config = config["llm"]
        self.client = Anthropic()  # Uses ANTHROPIC_API_KEY env var
        self.logger = logging.getLogger("core.model_router")

        # Model definitions
        self.models = {
            "haiku": {
                "name": self.llm_config["routing"]["screening_model"],
                "cost_per_mtok": self.llm_config["routing"]["screening_cost_per_mtok"]
            },
            "sonnet": {
                "name": self.llm_config["routing"]["analysis_model"],
                "cost_per_mtok": self.llm_config["routing"]["analysis_cost_per_mtok"]
            },
            "opus": {
                "name": self.llm_config["routing"]["critical_model"],
                "cost_per_mtok": self.llm_config["routing"]["critical_cost_per_mtok"]
            }
        }

        # Confidence thresholds
        self.thresholds = self.llm_config["thresholds"]

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
            prompt: The prompt to send
            complexity: "simple" | "medium" | "complex"
            max_tokens: Maximum response tokens
            force_model: Skip routing, use specific model

        Returns:
            {
                "response": str,
                "model": str,
                "cost": float,
                "tokens": {"input": int, "output": int},
                "confidence": float,
                "escalations": int
            }
        """
        if force_model:
            return await self._query_model(force_model, prompt, max_tokens)

        # Hierarchical routing
        escalations = 0

        # Step 1: Try Haiku if simple/medium
        if complexity in ["simple", "medium"]:
            result = await self._query_model("haiku", prompt, max_tokens)
            confidence = self._extract_confidence(result["response"])

            if confidence >= self.thresholds["screening_confidence"]:
                self.logger.info(
                    f"Haiku sufficient (conf={confidence:.2f}), cost=${result['cost']:.4f}"
                )
                return {**result, "confidence": confidence, "escalations": 0}

            self.logger.info(
                f"Haiku low confidence ({confidence:.2f}), escalating to Sonnet"
            )
            escalations += 1

        # Step 2: Try Sonnet
        result = await self._query_model("sonnet", prompt, max_tokens)
        confidence = self._extract_confidence(result["response"])

        if confidence >= self.thresholds["analysis_confidence"]:
            self.logger.info(
                f"Sonnet sufficient (conf={confidence:.2f}), cost=${result['cost']:.4f}"
            )
            return {**result, "confidence": confidence, "escalations": escalations}

        self.logger.warning(
            f"Sonnet low confidence ({confidence:.2f}), escalating to Opus"
        )
        escalations += 1

        # Step 3: Opus (last resort)
        result = await self._query_model("opus", prompt, max_tokens)
        confidence = self._extract_confidence(result["response"])

        self.logger.info(
            f"Opus result (conf={confidence:.2f}), cost=${result['cost']:.4f}"
        )
        return {**result, "confidence": confidence, "escalations": escalations}

    async def _query_model(
        self,
        model_tier: str,
        prompt: str,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Execute actual API call to specified model."""
        model_info = self.models[model_tier]

        try:
            response = await self.client.messages.create(
                model=model_info["name"],
                max_tokens=max_tokens,
                temperature=self.llm_config["api"]["temperature"],
                messages=[{"role": "user", "content": prompt}]
            )

            # Calculate cost
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = (
                (input_tokens / 1_000_000) * model_info["cost_per_mtok"] +
                (output_tokens / 1_000_000) * model_info["cost_per_mtok"] * 3
                # Output typically 3x cost of input
            )

            return {
                "response": response.content[0].text,
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

        Expects JSON with "confidence" field, or fallback to 0.5.
        """
        import json
        import re

        try:
            # Try to parse JSON
            match = re.search(r'\{.*"confidence":\s*([0-9.]+).*\}', response, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return float(data.get("confidence", 0.5))
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: medium confidence
        return 0.5
```

**Validation**:
- Test hierarchical routing: Haiku → Sonnet → Opus
- Verify cost calculation accuracy
- Test confidence extraction from various JSON formats
- Mock API calls to avoid actual costs during testing

---

### Phase 1.3: Prompt Manager (Days 5-6)

**File**: `core/prompt_manager.py`

**Requirements**:
```python
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import yaml
import logging

class PromptManager:
    """
    Manages prompt templates and few-shot examples.

    Features:
    1. Load prompt templates from files
    2. Inject few-shot examples
    3. Learn from feedback (save successful patterns)
    4. Version prompts for A/B testing
    """

    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.logger = logging.getLogger("core.prompt_manager")

        # Load base prompts
        self.base_prompts = self._load_base_prompts()

        # Load few-shot examples
        self.examples = self._load_examples()

        # Learned patterns (runtime updates)
        self.learned_patterns = []

    def _load_base_prompts(self) -> Dict[str, str]:
        """Load all .txt files from prompts/base/"""
        prompts = {}
        base_dir = self.prompts_dir / "base"

        if not base_dir.exists():
            self.logger.warning(f"Base prompts directory not found: {base_dir}")
            return prompts

        for file_path in base_dir.glob("*.txt"):
            prompt_name = file_path.stem
            with open(file_path, 'r', encoding='utf-8') as f:
                prompts[prompt_name] = f.read()

        self.logger.info(f"Loaded {len(prompts)} base prompts")
        return prompts

    def _load_examples(self) -> Dict[str, List[Dict]]:
        """Load few-shot examples from prompts/examples/"""
        examples = {}
        examples_dir = self.prompts_dir / "examples"

        if not examples_dir.exists():
            return examples

        for file_path in examples_dir.glob("*.json"):
            example_name = file_path.stem
            with open(file_path, 'r', encoding='utf-8') as f:
                examples[example_name] = json.load(f)

        self.logger.info(f"Loaded {len(examples)} example sets")
        return examples

    def build_prompt(
        self,
        template_name: str,
        context: Dict[str, Any],
        include_examples: bool = True,
        max_examples: int = 3
    ) -> str:
        """
        Build final prompt from template + context + examples.

        Args:
            template_name: Name of prompt template (e.g., "controller_analysis")
            context: Variables to inject (e.g., {"file_path": "...", "code": "..."})
            include_examples: Whether to add few-shot examples
            max_examples: Maximum number of examples to include

        Returns:
            Complete prompt ready for LLM
        """
        # Get base template
        if template_name not in self.base_prompts:
            raise ValueError(f"Prompt template not found: {template_name}")

        template = self.base_prompts[template_name]

        # Inject few-shot examples
        if include_examples and template_name in self.examples:
            examples_text = self._format_examples(
                self.examples[template_name][:max_examples]
            )
            template = f"{examples_text}\n\n---\n\n{template}"

        # Inject context variables
        try:
            prompt = template.format(**context)
        except KeyError as e:
            raise ValueError(f"Missing context variable: {e}")

        return prompt

    def _format_examples(self, examples: List[Dict]) -> str:
        """Format few-shot examples as text."""
        formatted = ["# Few-Shot Examples\n"]

        for i, example in enumerate(examples, 1):
            formatted.append(f"## Example {i}\n")
            formatted.append(f"**Input**:\n```\n{example['input']}\n```\n")
            formatted.append(f"**Expected Output**:\n```json\n{json.dumps(example['output'], indent=2)}\n```\n")

        return "\n".join(formatted)

    def learn_from_result(
        self,
        template_name: str,
        input_data: Dict[str, Any],
        output: Dict[str, Any],
        feedback: Dict[str, Any]
    ):
        """
        Learn from analysis result.

        Args:
            template_name: Which prompt was used
            input_data: Input context
            output: LLM's output
            feedback: {
                "correct": bool,
                "issues": List[str],
                "suggestions": List[str]
            }
        """
        if feedback.get("correct"):
            # Save as positive example
            self.learned_patterns.append({
                "template": template_name,
                "input": input_data,
                "output": output,
                "rating": 5,
                "timestamp": self._get_timestamp()
            })

            # Persist to disk
            self._save_learned_pattern(template_name, self.learned_patterns[-1])

        else:
            # Log failure for analysis
            self.logger.warning(
                f"Prompt {template_name} produced incorrect result. "
                f"Issues: {feedback.get('issues')}"
            )

    def _save_learned_pattern(self, template_name: str, pattern: Dict):
        """Save learned pattern to prompts/learned/"""
        learned_dir = self.prompts_dir / "learned"
        learned_dir.mkdir(exist_ok=True)

        file_path = learned_dir / f"{template_name}_learned.jsonl"

        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(pattern) + "\n")

    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()
```

**Deliverables**:
- Prompt templates for Controller analysis (as POC)
- Few-shot examples for common patterns
- Learning mechanism (save successful/failed cases)

**Validation**:
- Test prompt loading and variable injection
- Test few-shot example formatting
- Test learning mechanism (save/load patterns)

---

### Phase 1.4: Semantic Cache (Day 7)

**File**: `core/cache_manager.py`

**Requirements**:
```python
from typing import Dict, Any, Optional
import hashlib
import json
import pickle
from pathlib import Path
import logging

class CacheManager:
    """
    Semantic cache for LLM analysis results.

    Instead of exact file match, uses file hash + semantic similarity
    to determine cache hits. This handles minor code changes (comments,
    formatting) that don't affect semantics.

    For MVP: Use simple hash-based cache.
    Future: Add vector embeddings for true semantic similarity.
    """

    def __init__(self, cache_dir: str = ".cache", ttl_days: int = 30):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl_days = ttl_days
        self.logger = logging.getLogger("core.cache_manager")

        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "saves": 0
        }

    def get(
        self,
        agent_name: str,
        file_path: str,
        file_content: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached analysis result.

        Args:
            agent_name: Which agent analyzed this
            file_path: Path to file
            file_content: Current file content

        Returns:
            Cached result or None
        """
        cache_key = self._compute_cache_key(agent_name, file_path, file_content)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        if not cache_file.exists():
            self.stats["misses"] += 1
            return None

        # Check if cache is expired
        if self._is_expired(cache_file):
            self.logger.debug(f"Cache expired: {cache_file}")
            cache_file.unlink()
            self.stats["misses"] += 1
            return None

        # Load cached result
        try:
            with open(cache_file, 'rb') as f:
                result = pickle.load(f)

            self.stats["hits"] += 1
            self.logger.info(f"Cache HIT: {file_path}")
            return result

        except Exception as e:
            self.logger.error(f"Cache read error: {e}")
            self.stats["misses"] += 1
            return None

    def save(
        self,
        agent_name: str,
        file_path: str,
        file_content: str,
        result: Dict[str, Any]
    ):
        """Save analysis result to cache."""
        cache_key = self._compute_cache_key(agent_name, file_path, file_content)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)

            self.stats["saves"] += 1
            self.logger.debug(f"Cache SAVE: {file_path}")

        except Exception as e:
            self.logger.error(f"Cache write error: {e}")

    def _compute_cache_key(
        self,
        agent_name: str,
        file_path: str,
        file_content: str
    ) -> str:
        """
        Compute cache key from agent + file + content hash.

        Future: Use semantic embeddings instead of raw content hash.
        """
        content_hash = hashlib.sha256(file_content.encode()).hexdigest()
        combined = f"{agent_name}:{file_path}:{content_hash}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def _is_expired(self, cache_file: Path) -> bool:
        """Check if cache file is older than TTL."""
        import time
        from datetime import timedelta

        file_age_seconds = time.time() - cache_file.stat().st_mtime
        ttl_seconds = timedelta(days=self.ttl_days).total_seconds()

        return file_age_seconds > ttl_seconds

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0

        return {
            **self.stats,
            "hit_rate": hit_rate,
            "cache_files": len(list(self.cache_dir.glob("*.pkl")))
        }

    def clear(self):
        """Clear all cache files."""
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()

        self.logger.info("Cache cleared")
        self.stats = {"hits": 0, "misses": 0, "saves": 0}
```

**Validation**:
- Test cache hit/miss logic
- Test expiration (mock file timestamps)
- Test statistics tracking

---

### Phase 1.5: Cost Tracker (Day 8)

**File**: `core/cost_tracker.py`

**Requirements**:
```python
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
import json
import logging

class CostTracker:
    """
    Tracks LLM API costs in real-time.

    Features:
    - Per-agent cost breakdown
    - Per-model cost breakdown
    - Budget alerts
    - Cost projection
    """

    def __init__(
        self,
        output_file: str = "output/cost_tracker.jsonl",
        budget_per_project: float = 5.0,
        alert_threshold: float = 0.8
    ):
        self.output_file = Path(output_file)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        self.budget_per_project = budget_per_project
        self.alert_threshold = alert_threshold
        self.logger = logging.getLogger("core.cost_tracker")

        # Runtime tracking
        self.session_costs = []
        self.total_cost = 0.0

    def record(
        self,
        agent: str,
        model: str,
        tokens: Dict[str, int],
        cost: float
    ):
        """Record a single LLM query cost."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "model": model,
            "tokens": tokens,
            "cost": cost
        }

        # Append to JSONL file
        with open(self.output_file, 'a') as f:
            f.write(json.dumps(record) + "\n")

        # Update runtime totals
        self.session_costs.append(record)
        self.total_cost += cost

        # Check budget
        if self.total_cost >= self.budget_per_project * self.alert_threshold:
            self.logger.warning(
                f"⚠️  Cost alert: ${self.total_cost:.2f} / ${self.budget_per_project:.2f} "
                f"({self.total_cost/self.budget_per_project*100:.0f}%)"
            )

    def get_summary(self) -> Dict[str, Any]:
        """Get cost summary for current session."""
        if not self.session_costs:
            return {"total_cost": 0, "queries": 0}

        # Group by agent
        agent_costs = {}
        for record in self.session_costs:
            agent = record["agent"]
            if agent not in agent_costs:
                agent_costs[agent] = {"cost": 0, "queries": 0}

            agent_costs[agent]["cost"] += record["cost"]
            agent_costs[agent]["queries"] += 1

        # Group by model
        model_costs = {}
        for record in self.session_costs:
            model = record["model"]
            if model not in model_costs:
                model_costs[model] = {"cost": 0, "queries": 0, "tokens": 0}

            model_costs[model]["cost"] += record["cost"]
            model_costs[model]["queries"] += 1
            model_costs[model]["tokens"] += (
                record["tokens"]["input"] + record["tokens"]["output"]
            )

        return {
            "total_cost": self.total_cost,
            "total_queries": len(self.session_costs),
            "budget_remaining": self.budget_per_project - self.total_cost,
            "budget_usage_pct": (self.total_cost / self.budget_per_project) * 100,
            "by_agent": agent_costs,
            "by_model": model_costs
        }

    def print_summary(self):
        """Print formatted cost summary."""
        summary = self.get_summary()

        print("\n" + "=" * 60)
        print("💰 COST SUMMARY")
        print("=" * 60)
        print(f"Total Cost: ${summary['total_cost']:.4f}")
        print(f"Total Queries: {summary['total_queries']}")
        print(f"Budget: ${self.budget_per_project:.2f}")
        print(f"Remaining: ${summary['budget_remaining']:.2f} ({100-summary['budget_usage_pct']:.1f}%)")

        print("\nBy Agent:")
        for agent, stats in summary["by_agent"].items():
            print(f"  {agent}: ${stats['cost']:.4f} ({stats['queries']} queries)")

        print("\nBy Model:")
        for model, stats in summary["by_model"].items():
            model_short = model.split("-")[-1]  # e.g., "haiku-20241022" -> "20241022"
            print(
                f"  {model_short}: ${stats['cost']:.4f} "
                f"({stats['queries']} queries, {stats['tokens']:,} tokens)"
            )

        print("=" * 60 + "\n")
```

**Validation**:
- Test cost recording and aggregation
- Test budget alerts
- Test summary generation

---

### Phase 1.6: Integration & Testing (Days 9-10)

**Tasks**:
1. Wire all components together
2. Create integration test that:
   - Loads config
   - Initializes all core components
   - Simulates a simple query
   - Verifies cost tracking, caching work
3. Create setup script for easy initialization

**File**: `scripts/setup.py`

```python
#!/usr/bin/env python3
"""
Setup script for SpringMVC Agent Analyzer.

Initializes project structure, validates configuration, tests API connectivity.
"""

import os
import sys
from pathlib import Path
import yaml
from anthropic import Anthropic

def main():
    print("🚀 SpringMVC Agent Analyzer Setup\n")

    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required")
        sys.exit(1)
    print("✅ Python version OK")

    # Check ANTHROPIC_API_KEY
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY environment variable not set")
        print("   Set it in .env or export ANTHROPIC_API_KEY=your_key")
        sys.exit(1)
    print("✅ ANTHROPIC_API_KEY found")

    # Test API connectivity
    try:
        client = Anthropic()
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        print("✅ Anthropic API connection OK")
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        sys.exit(1)

    # Create output directories
    Path("output").mkdir(exist_ok=True)
    Path(".cache").mkdir(exist_ok=True)
    print("✅ Output directories created")

    # Validate config
    if not Path("config/config.yaml").exists():
        print("❌ config/config.yaml not found")
        sys.exit(1)

    with open("config/config.yaml") as f:
        config = yaml.safe_load(f)

    print("✅ Configuration valid")

    print("\n✨ Setup complete! Ready to analyze.")
    print("\nNext steps:")
    print("  1. Run POC: python -m tests.integration.test_controller_poc")
    print("  2. Start MCP server: python -m mcp.server")

if __name__ == "__main__":
    main()
```

**Phase 1 Success Criteria**:
- ✅ All core components implemented and tested
- ✅ Integration test passes
- ✅ Setup script works
- ✅ Documentation complete

---

## Phase 2: Controller Agent POC (Week 3-4, 10 days)

**Goal**: Build ONE complete agent as proof-of-concept. Validate the entire approach.

**Critical**: This phase determines if we continue or pivot.

---

### Phase 2.1: Controller Agent Implementation (Days 11-14)

**File**: `agents/controller_agent.py`

**Requirements**:
Analyze Java Spring Controller files to extract:
- Class name
- Class-level @RequestMapping path
- Method-level @RequestMapping paths
- HTTP methods (GET/POST/PUT/DELETE)
- Service dependencies (@Autowired)
- Method parameters
- Return types

**Prompt Template** (`prompts/base/controller_analysis.txt`):

```
You are a Java Spring Framework expert analyzer.

Analyze the following Spring Controller file and extract its structure.

# Task

Extract:
1. **Class Information**
   - Class name
   - Class-level @RequestMapping path (if any)
   - Package name

2. **Request Mappings**
   For each method with @RequestMapping, @GetMapping, @PostMapping, etc.:
   - Method name
   - Path (combine class-level + method-level)
   - HTTP method (GET/POST/PUT/DELETE/PATCH)
   - Parameters (name, type, annotation like @RequestParam, @PathVariable)
   - Return type

3. **Dependencies**
   - @Autowired services (field name and type)
   - Other @Autowired components

4. **Confidence Assessment**
   - Rate your confidence (0.0-1.0) in the analysis
   - Note any ambiguities or unclear patterns

# Input

File: {file_path}

```java
{code}
```

# Output Format

Return ONLY valid JSON (no markdown, no explanation):

{{
  "class_name": "UserController",
  "package": "com.example.controller",
  "class_level_mapping": "/users",
  "mappings": [
    {{
      "method_name": "listUsers",
      "path": "/users/list",
      "http_method": "GET",
      "parameters": [
        {{"name": "page", "type": "int", "annotation": "@RequestParam(defaultValue=\\"1\\")"}}
      ],
      "return_type": "ModelAndView"
    }}
  ],
  "dependencies": [
    {{"field_name": "userService", "type": "UserService", "annotation": "@Autowired"}}
  ],
  "confidence": 0.95,
  "notes": "Clear structure, no ambiguities"
}}
```

**Few-Shot Examples** (`prompts/examples/controller_analysis.json`):

```json
[
  {
    "input": "@Controller\n@RequestMapping(\"/users\")\npublic class UserController {\n    @Autowired\n    private UserService userService;\n\n    @GetMapping(\"/list\")\n    public ModelAndView listUsers() {\n        return new ModelAndView(\"users/list\");\n    }\n}",
    "output": {
      "class_name": "UserController",
      "package": "unknown",
      "class_level_mapping": "/users",
      "mappings": [
        {
          "method_name": "listUsers",
          "path": "/users/list",
          "http_method": "GET",
          "parameters": [],
          "return_type": "ModelAndView"
        }
      ],
      "dependencies": [
        {"field_name": "userService", "type": "UserService", "annotation": "@Autowired"}
      ],
      "confidence": 0.95,
      "notes": "Standard Spring MVC pattern"
    }
  },
  {
    "input": "@RestController\npublic class ApiController {\n    @PostMapping(\"/api/save\")\n    public ResponseEntity<User> saveUser(@RequestBody User user) {\n        return ResponseEntity.ok(user);\n    }\n}",
    "output": {
      "class_name": "ApiController",
      "package": "unknown",
      "class_level_mapping": null,
      "mappings": [
        {
          "method_name": "saveUser",
          "path": "/api/save",
          "http_method": "POST",
          "parameters": [
            {"name": "user", "type": "User", "annotation": "@RequestBody"}
          ],
          "return_type": "ResponseEntity<User>"
        }
      ],
      "dependencies": [],
      "confidence": 0.9,
      "notes": "REST controller, no class-level mapping"
    }
  }
]
```

**Agent Implementation**:

```python
from agents.base_agent import BaseAgent
from typing import Dict, Any

class ControllerAgent(BaseAgent):
    """Analyzes Spring Controller files."""

    def __init__(self, model_router, prompt_manager, cost_tracker, config):
        super().__init__(
            agent_name="controller",
            model_router=model_router,
            prompt_manager=prompt_manager,
            cost_tracker=cost_tracker,
            config=config
        )

    async def analyze(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Analyze a Spring Controller file."""
        # Load file
        code = self._load_file_with_context(file_path)

        # Build prompt
        prompt = self.prompt_manager.build_prompt(
            template_name="controller_analysis",
            context={
                "file_path": file_path,
                "code": code
            },
            include_examples=True,
            max_examples=2
        )

        # Query LLM
        llm_result = await self._query_llm(
            prompt=prompt,
            complexity="simple",  # Controllers are usually straightforward
            max_tokens=2048
        )

        # Parse response
        try:
            analysis = self._extract_json_from_response(llm_result["response"])
        except ValueError as e:
            self.logger.error(f"Failed to parse response: {e}")
            return {
                "file_path": file_path,
                "error": str(e),
                "raw_response": llm_result["response"][:500]
            }

        # Add metadata
        result = {
            "file_path": file_path,
            "analysis": analysis,
            "confidence": analysis.get("confidence", 0.5),
            "model_used": llm_result["model"],
            "cost": llm_result["cost"],
            "timestamp": self._get_timestamp()
        }

        # Validate
        if not await self.validate_result(result):
            self.logger.warning(
                f"Low confidence result ({result['confidence']}) for {file_path}"
            )

        return result

    def _get_timestamp(self):
        from datetime import datetime
        return datetime.now().isoformat()
```

**Validation**:
- Create 10 test Controller files with varying complexity
- Run analysis on each
- Compare against manual analysis (gold standard)
- Measure accuracy, cost, time

---

### Phase 2.2: Java Validator (Days 15-16)

**File**: `validators/java_validator.py`

**Purpose**: Lightweight syntax check (NOT full parsing)

```python
import javalang

class JavaValidator:
    """
    Lightweight Java syntax validator.

    Does NOT do semantic analysis - just checks if code is parseable.
    """

    @staticmethod
    def validate_syntax(code: str) -> Dict[str, Any]:
        """
        Check if Java code is syntactically valid.

        Returns:
            {
                "valid": bool,
                "error": str or None,
                "line": int or None
            }
        """
        try:
            javalang.parse.parse(code)
            return {"valid": True, "error": None, "line": None}
        except javalang.parser.JavaSyntaxError as e:
            return {
                "valid": False,
                "error": str(e),
                "line": getattr(e, 'lineno', None)
            }

    @staticmethod
    def extract_class_name(code: str) -> str or None:
        """Quick extraction of class name (validation helper)."""
        try:
            tree = javalang.parse.parse(code)
            for path, node in tree:
                if isinstance(node, javalang.tree.ClassDeclaration):
                    return node.name
        except:
            pass
        return None
```

---

### Phase 2.3: Benchmarking & Validation (Days 17-20)

**Goal**: Prove POC meets success criteria.

**Test Suite** (`tests/integration/test_controller_poc.py`):

```python
import pytest
import asyncio
from agents.controller_agent import ControllerAgent
from core.model_router import ModelRouter
from core.prompt_manager import PromptManager
from core.cost_tracker import CostTracker
import yaml

@pytest.fixture
async def controller_agent():
    """Initialize Controller Agent with all dependencies."""
    with open("config/config.yaml") as f:
        config = yaml.safe_load(f)

    model_router = ModelRouter()
    prompt_manager = PromptManager()
    cost_tracker = CostTracker()

    return ControllerAgent(
        model_router=model_router,
        prompt_manager=prompt_manager,
        cost_tracker=cost_tracker,
        config=config
    )

@pytest.mark.asyncio
async def test_simple_controller(controller_agent):
    """Test analysis of simple controller."""
    result = await controller_agent.analyze("tests/fixtures/SimpleController.java")

    assert result["confidence"] >= 0.8
    assert result["analysis"]["class_name"] == "SimpleController"
    assert len(result["analysis"]["mappings"]) == 2
    assert result["cost"] < 0.01  # Should be cheap

@pytest.mark.asyncio
async def test_complex_controller(controller_agent):
    """Test analysis of complex controller with edge cases."""
    result = await controller_agent.analyze("tests/fixtures/ComplexController.java")

    assert result["confidence"] >= 0.7
    assert len(result["analysis"]["mappings"]) >= 5

@pytest.mark.asyncio
async def test_batch_analysis(controller_agent):
    """Test analyzing multiple controllers and measure total cost."""
    import glob

    controller_files = glob.glob("tests/fixtures/*Controller.java")
    results = []

    for file_path in controller_files:
        result = await controller_agent.analyze(file_path)
        results.append(result)

    # Aggregate metrics
    total_cost = sum(r["cost"] for r in results)
    avg_confidence = sum(r["confidence"] for r in results) / len(results)

    print(f"\n📊 Batch Analysis Results:")
    print(f"   Files analyzed: {len(results)}")
    print(f"   Total cost: ${total_cost:.4f}")
    print(f"   Avg confidence: {avg_confidence:.2f}")
    print(f"   Cost per file: ${total_cost/len(results):.4f}")

    # Success criteria
    assert total_cost < 1.0  # Should be under $1 for ~20 files
    assert avg_confidence >= 0.85
```

**Gold Standard Creation**:
1. Manually analyze 20 Controller files
2. Create JSON ground truth files
3. Compare LLM results against ground truth
4. Calculate precision, recall, F1 score

**Benchmark Script** (`scripts/benchmark.py`):

```python
#!/usr/bin/env python3
"""
Benchmark Controller Agent against gold standard.

Measures:
- Accuracy (precision, recall, F1)
- Cost per file
- Time per file
- Model distribution (Haiku vs Sonnet vs Opus usage)
"""

import asyncio
import json
from pathlib import Path
from agents.controller_agent import ControllerAgent
# ... (full implementation)

async def main():
    # Load gold standard
    gold_standard = load_gold_standard("tests/fixtures/gold_standard.json")

    # Analyze all files
    agent = initialize_agent()
    results = []

    for file_path, expected in gold_standard.items():
        actual = await agent.analyze(file_path)
        comparison = compare_results(expected, actual)
        results.append(comparison)

    # Calculate metrics
    metrics = calculate_metrics(results)

    print(f"\n{'='*60}")
    print(f"📊 CONTROLLER AGENT BENCHMARK RESULTS")
    print(f"{'='*60}")
    print(f"Accuracy:  {metrics['accuracy']*100:.1f}%")
    print(f"Precision: {metrics['precision']*100:.1f}%")
    print(f"Recall:    {metrics['recall']*100:.1f}%")
    print(f"F1 Score:  {metrics['f1']*100:.1f}%")
    print(f"\nCost:      ${metrics['total_cost']:.4f}")
    print(f"Avg Cost:  ${metrics['avg_cost']:.4f} per file")
    print(f"\nModel Usage:")
    print(f"  Haiku:  {metrics['haiku_pct']:.0f}%")
    print(f"  Sonnet: {metrics['sonnet_pct']:.0f}%")
    print(f"  Opus:   {metrics['opus_pct']:.0f}%")
    print(f"{'='*60}\n")

    # Decision point
    if metrics['accuracy'] >= 0.9 and metrics['avg_cost'] <= 0.05:
        print("✅ POC SUCCESS! Proceed to Phase 3.")
    else:
        print("⚠️  POC needs refinement. Review prompts and model routing.")

if __name__ == "__main__":
    asyncio.run(main())
```

**Phase 2 Success Criteria**:
- ✅ Accuracy >= 90% (precision + recall)
- ✅ Cost <= $1 for 20 files (≈$0.05 per file)
- ✅ Confidence >= 0.85 average
- ✅ Haiku usage >= 70% (cost optimization proof)

**Decision Point**:
- ✅ If POC succeeds → Proceed to Phase 3
- ⚠️ If partial success → Refine prompts, retry
- ❌ If POC fails → Reconsider hybrid approach (more code validation)

---

## Phase 3: Expand Agent Coverage (Week 5-8, 20 days)

**Goal**: Build remaining agents following the proven Controller Agent pattern.

**Agents to Build**:
1. JSP Agent (Days 21-25)
2. Service Agent (Days 26-30)
3. MyBatis Mapper Agent (Days 31-35)
4. Procedure Agent (Days 36-40)

---

### Phase 3.1: JSP Agent (Days 21-25)

**File**: `agents/jsp_agent.py`

**Extraction Targets**:
- JSP includes (`<jsp:include>`, `<%@ include %>`)
- AJAX calls (`$.ajax`, `$.post`, `fetch()`, `XMLHttpRequest`)
- Form submissions (`<form action="...">`)
- EL expressions (`${...}`)
- Imported tag libraries (`<%@ taglib %>`)

**Prompt Template**: `prompts/base/jsp_analysis.txt`

**Few-Shot Examples**: `prompts/examples/jsp_analysis.json`

**Complexity**: Medium (HTML + Java + JavaScript mixed)

**Estimated Cost**: $0.03 per file (mostly Sonnet)

---

### Phase 3.2: Service Agent (Days 26-30)

**File**: `agents/service_agent.py`

**Extraction Targets**:
- Class name and package
- @Service, @Component annotations
- @Autowired Mapper dependencies
- @Transactional methods
- Business logic method signatures

**Estimated Cost**: $0.02 per file (mostly Haiku)

---

### Phase 3.3: MyBatis Mapper Agent (Days 31-35)

**File**: `agents/mapper_agent.py`

**Extraction Targets**:
- Mapper interface name
- XML file mapping
- SQL statements (`<select>`, `<insert>`, `<update>`, `<delete>`)
- Stored procedure calls (`statementType="CALLABLE"`)
- Parameter types
- Result types
- Table/column references

**Complexity**: Medium-High (XML + SQL parsing)

**Estimated Cost**: $0.04 per file

---

### Phase 3.4: Procedure Agent (Days 36-40)

**File**: `agents/procedure_agent.py`

**Note**: This can reuse logic from the old project's `procedure_analyzer.py`.

**Extraction Targets**:
- Business purpose
- Operation type
- Table impacts
- Trigger detection
- Exception handling
- Integration recommendations

**Estimated Cost**: $0.10 per procedure (Sonnet/Opus mix)

---

**Phase 3 Success Criteria**:
- ✅ All 4 agents implemented
- ✅ Each agent has >= 85% accuracy
- ✅ Average cost per file <= $0.05
- ✅ Integration tests pass for all agents

---

## Phase 4: Knowledge Graph Builder (Week 9-10, 10 days)

**Goal**: Assemble analysis results into a queryable knowledge graph.

---

### Phase 4.1: Graph Builder (Days 41-45)

**File**: `graph/builder.py`

**Node Types**:
- JSP
- CONTROLLER
- SERVICE
- MAPPER
- TABLE
- PROCEDURE
- ORACLE_JOB

**Edge Types**:
- INCLUDES (JSP → JSP)
- AJAX_CALL (JSP → CONTROLLER)
- INVOKES (CONTROLLER → SERVICE)
- CALLS (SERVICE → MAPPER)
- QUERIES (MAPPER → TABLE)
- EXECUTES (MAPPER → PROCEDURE)
- SCHEDULED (ORACLE_JOB → PROCEDURE)

**Implementation**: Use NetworkX (same as old project)

---

### Phase 4.2: Graph Query Engine (Days 46-48)

**File**: `graph/query.py`

**Capabilities**:
- find_call_chains(start, end)
- find_impact(node) - What depends on this node?
- find_dependencies(node) - What does this node depend on?
- find_orphans() - Nodes with no incoming edges
- find_cycles() - Circular dependencies

**Reuse**: Can adapt logic from old project's `query_engine.py`

---

### Phase 4.3: Visualization (Days 49-50)

**File**: `graph/visualizer.py`

**Output Formats**:
1. Mermaid (markdown documentation)
2. PyVis (interactive HTML)
3. GraphML (for Gephi)

**Reuse**: Can adapt from old project's visualization code.

---

**Phase 4 Success Criteria**:
- ✅ Graph builds from all agent outputs
- ✅ Query functions work correctly
- ✅ Visualization renders for sample project
- ✅ Performance acceptable (< 5s for 1000 nodes)

---

## Phase 5: MCP Integration (Week 11-12, 10 days)

**Goal**: Expose all capabilities as MCP tools for Claude Code integration.

---

### Phase 5.1: MCP Server (Days 51-55)

**File**: `mcp/server.py`

**Tools to Expose**:
1. `analyze_controller` - Analyze a Spring Controller
2. `analyze_jsp` - Analyze a JSP file
3. `analyze_service` - Analyze a Service class
4. `analyze_mapper` - Analyze a MyBatis Mapper
5. `build_graph` - Build knowledge graph from directory
6. `query_chain` - Find call chain between nodes
7. `impact_analysis` - Analyze impact of changes
8. `cost_summary` - Get cost breakdown

**Reference**: MCP Server implementation from old project

---

### Phase 5.2: Integration Testing (Days 56-60)

**Tasks**:
1. Test MCP server with Claude Code CLI
2. Create sample slash commands
3. End-to-end validation on real project
4. Performance optimization
5. Error handling improvements

---

**Phase 5 Success Criteria**:
- ✅ All MCP tools functional
- ✅ Integration with Claude Code works
- ✅ Documentation complete
- ✅ Real-world project analysis succeeds

---

## Phase 6: Production Readiness (Week 13-14, 10 days)

**Goal**: Polish, document, and prepare for real-world usage.

---

### Phase 6.1: Comprehensive Testing (Days 61-65)

**Test Coverage**:
- Unit tests for all agents
- Integration tests for graph builder
- Performance tests
- Error handling tests
- Real-world project validation

**Target**: >= 80% code coverage

---

### Phase 6.2: Documentation (Days 66-68)

**Documents to Create**:
1. `docs/ARCHITECTURE.md` - System design
2. `docs/AGENT_GUIDE.md` - How to create new agents
3. `docs/API_REFERENCE.md` - Programmatic API docs
4. `docs/COST_OPTIMIZATION.md` - Tips for reducing costs
5. `docs/TROUBLESHOOTING.md` - Common issues

---

### Phase 6.3: Performance Optimization (Days 69-70)

**Optimization Targets**:
- Batch processing for multiple files
- Parallel agent execution
- Cache warming strategies
- Prompt optimization based on learned patterns

---

**Phase 6 Success Criteria**:
- ✅ All tests pass
- ✅ Documentation complete
- ✅ Performance benchmarks met
- ✅ Real project validated successfully

---

## Success Metrics (Overall Project)

**Must-Have**:
- ✅ Accuracy >= 90% across all agents
- ✅ Total cost <= $5 per medium project (100 files)
- ✅ Cache hit rate >= 60%
- ✅ Maintenance time <= 2 hours/month

**Nice-to-Have**:
- ✅ Cost <= $3 per project
- ✅ Cache hit rate >= 70%
- ✅ Accuracy >= 95%

---

## Risk Mitigation

**Risk 1: POC Fails (Accuracy < 90%)**
- Mitigation: Refine prompts, add more few-shot examples
- Fallback: Hybrid approach (LLM + targeted parsers)

**Risk 2: Cost Too High (> $5/project)**
- Mitigation: Optimize model routing, increase cache usage
- Fallback: Use Haiku-only mode for initial screening

**Risk 3: LLM Hallucination**
- Mitigation: Validators catch syntax errors
- Mitigation: Confidence thresholds reject uncertain results

**Risk 4: API Rate Limiting**
- Mitigation: Batch requests, respect rate limits
- Mitigation: Retry logic with exponential backoff

---

## Timeline Summary

| Phase | Duration | Key Deliverable |
|-------|----------|----------------|
| **Phase 1: Foundation** | 2 weeks | Core infrastructure |
| **Phase 2: Controller POC** | 2 weeks | Validation of approach |
| **Decision Point** | - | Go/No-Go decision |
| **Phase 3: Expand Agents** | 4 weeks | All analyzers complete |
| **Phase 4: Knowledge Graph** | 2 weeks | Graph builder & query |
| **Phase 5: MCP Integration** | 2 weeks | Claude Code integration |
| **Phase 6: Production** | 2 weeks | Polish & validation |
| **TOTAL** | **14 weeks** | Production-ready system |

---

## Next Steps for Implementing Agent

1. **Week 1 Focus**: Phase 1.1-1.3 (BaseAgent, ModelRouter, PromptManager)
2. **Week 2 Focus**: Phase 1.4-1.6 (Cache, CostTracker, Integration)
3. **Week 3-4 Focus**: Controller Agent POC
4. **Decision Point**: Evaluate POC results, decide to proceed or pivot

**Let's build this! 🚀**
