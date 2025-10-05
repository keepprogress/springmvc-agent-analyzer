"""
Cost Tracker for LLM API usage monitoring.

This module tracks real-time costs, provides budget alerts, and generates
detailed cost breakdowns by agent and model tier.
"""

from __future__ import annotations
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
    - Budget alerts (configurable threshold)
    - Cost projection based on current usage
    - JSONL logging for detailed analysis

    Attributes:
        output_file: Path to JSONL log file
        budget_per_project: Budget limit in USD
        alert_threshold: Percentage of budget to trigger alert (0.0-1.0)
        session_costs: List of cost records for current session
        total_cost: Running total of costs
        logger: Logger instance
    """

    def __init__(
        self,
        output_file: str = "output/cost_tracker.jsonl",
        budget_per_project: float = 5.0,
        alert_threshold: float = 0.8
    ):
        """
        Initialize the Cost Tracker.

        Args:
            output_file: Path to JSONL output file
            budget_per_project: Maximum budget in USD
            alert_threshold: Alert when cost reaches this % of budget (0.0-1.0)
        """
        self.output_file = Path(output_file)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        self.budget_per_project = budget_per_project
        self.alert_threshold = alert_threshold
        self.logger = logging.getLogger("core.cost_tracker")

        # Runtime tracking
        self.session_costs: List[Dict[str, Any]] = []
        self.total_cost = 0.0

        self.logger.info(
            f"CostTracker initialized: budget=${budget_per_project:.2f}, "
            f"alert_threshold={alert_threshold*100:.0f}%"
        )

    def record(
        self,
        agent: str,
        model: str,
        tokens: Dict[str, int],
        cost: float,
        cached: bool = False
    ):
        """
        Record a single LLM query cost.

        Args:
            agent: Agent name (e.g., "controller", "jsp")
            model: Model identifier (e.g., "claude-3-5-haiku-20241022" or "cache")
            tokens: Token usage dictionary {"input": int, "output": int}
            cost: Cost in USD
            cached: Whether this was a cache hit (cost should be 0.0)
        """
        # Create record
        record = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "model": model,
            "tokens": tokens,
            "cost": cost,
            "cached": cached
        }

        # Append to JSONL file
        try:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write cost record: {e}")

        # Update runtime totals
        self.session_costs.append(record)
        self.total_cost += cost

        # Check budget and alert if needed
        if self.total_cost >= self.budget_per_project * self.alert_threshold:
            usage_pct = (self.total_cost / self.budget_per_project) * 100
            self.logger.warning(
                f"⚠️  COST ALERT: ${self.total_cost:.4f} / ${self.budget_per_project:.2f} "
                f"({usage_pct:.1f}% of budget)"
            )

        # Log cache hits differently
        if cached:
            self.logger.debug(f"Cost recorded: {agent} (CACHED, $0.00)")
        else:
            self.logger.debug(
                f"Cost recorded: {agent} via {model.split('-')[-1]} - ${cost:.4f}"
            )

    def get_summary(self) -> Dict[str, Any]:
        """
        Get cost summary for current session.

        Returns:
            Dictionary with comprehensive cost breakdown:
            {
                "total_cost": float,
                "total_queries": int,
                "cached_queries": int,
                "cache_savings": float,
                "budget_remaining": float,
                "budget_usage_pct": float,
                "by_agent": {
                    "agent_name": {"cost": float, "queries": int}
                },
                "by_model": {
                    "model_name": {"cost": float, "queries": int, "tokens": int}
                }
            }
        """
        if not self.session_costs:
            return {
                "total_cost": 0.0,
                "total_queries": 0,
                "cached_queries": 0,
                "cache_savings": 0.0,
                "budget_remaining": self.budget_per_project,
                "budget_usage_pct": 0.0,
                "by_agent": {},
                "by_model": {}
            }

        # Calculate cache statistics
        cached_queries = sum(1 for r in self.session_costs if r.get("cached", False))
        non_cached_queries = len(self.session_costs) - cached_queries

        # Estimate cache savings (average cost per non-cached query * cached queries)
        if non_cached_queries > 0:
            avg_query_cost = sum(
                r["cost"] for r in self.session_costs if not r.get("cached", False)
            ) / non_cached_queries
            cache_savings = avg_query_cost * cached_queries
        else:
            cache_savings = 0.0

        # Group by agent
        agent_costs: Dict[str, Dict[str, Any]] = {}
        for record in self.session_costs:
            agent = record["agent"]
            if agent not in agent_costs:
                agent_costs[agent] = {"cost": 0.0, "queries": 0}

            agent_costs[agent]["cost"] += record["cost"]
            agent_costs[agent]["queries"] += 1

        # Group by model
        model_costs: Dict[str, Dict[str, Any]] = {}
        for record in self.session_costs:
            model = record["model"]
            if model not in model_costs:
                model_costs[model] = {"cost": 0.0, "queries": 0, "tokens": 0}

            model_costs[model]["cost"] += record["cost"]
            model_costs[model]["queries"] += 1
            model_costs[model]["tokens"] += (
                record["tokens"]["input"] + record["tokens"]["output"]
            )

        return {
            "total_cost": round(self.total_cost, 6),
            "total_queries": len(self.session_costs),
            "cached_queries": cached_queries,
            "cache_savings": round(cache_savings, 6),
            "budget_remaining": round(self.budget_per_project - self.total_cost, 6),
            "budget_usage_pct": round((self.total_cost / self.budget_per_project) * 100, 2),
            "by_agent": {
                agent: {
                    "cost": round(stats["cost"], 6),
                    "queries": stats["queries"]
                }
                for agent, stats in agent_costs.items()
            },
            "by_model": {
                model: {
                    "cost": round(stats["cost"], 6),
                    "queries": stats["queries"],
                    "tokens": stats["tokens"]
                }
                for model, stats in model_costs.items()
            }
        }

    def print_summary(self):
        """Print formatted cost summary to console."""
        summary = self.get_summary()

        print("\n" + "=" * 60)
        print("💰 COST SUMMARY")
        print("=" * 60)
        print(f"Total Cost:        ${summary['total_cost']:.4f}")
        print(f"Total Queries:     {summary['total_queries']}")
        print(f"Cached Queries:    {summary['cached_queries']} "
              f"({summary['cached_queries']/max(1, summary['total_queries'])*100:.1f}%)")
        print(f"Cache Savings:     ${summary['cache_savings']:.4f}")
        print(f"\nBudget:            ${self.budget_per_project:.2f}")
        print(f"Remaining:         ${summary['budget_remaining']:.4f} "
              f"({100 - summary['budget_usage_pct']:.1f}%)")

        # Budget status indicator
        if summary['budget_usage_pct'] >= 100:
            status = "❌ OVER BUDGET"
        elif summary['budget_usage_pct'] >= self.alert_threshold * 100:
            status = "⚠️  WARNING"
        else:
            status = "✅ OK"
        print(f"Status:            {status}")

        # By agent
        if summary['by_agent']:
            print("\n--- By Agent ---")
            for agent, stats in sorted(
                summary['by_agent'].items(),
                key=lambda x: x[1]['cost'],
                reverse=True
            ):
                print(f"  {agent:15s}: ${stats['cost']:.4f} ({stats['queries']} queries)")

        # By model
        if summary['by_model']:
            print("\n--- By Model ---")
            for model, stats in sorted(
                summary['by_model'].items(),
                key=lambda x: x[1]['cost'],
                reverse=True
            ):
                # Shorten model name for display
                model_short = model.split("-")[-1] if "-" in model else model
                print(
                    f"  {model_short:12s}: ${stats['cost']:.4f} "
                    f"({stats['queries']} queries, {stats['tokens']:,} tokens)"
                )

        print("=" * 60 + "\n")

    def project_cost(self, remaining_files: int, avg_cost_per_file: float) -> float:
        """
        Project total cost based on current average.

        Args:
            remaining_files: Number of files left to analyze
            avg_cost_per_file: Average cost per file so far

        Returns:
            Projected total cost
        """
        projected_additional = remaining_files * avg_cost_per_file
        projected_total = self.total_cost + projected_additional

        self.logger.info(
            f"Cost projection: Current ${self.total_cost:.4f} + "
            f"Projected ${projected_additional:.4f} = "
            f"Total ${projected_total:.4f}"
        )

        return projected_total

    def check_budget(self) -> Dict[str, Any]:
        """
        Check budget status.

        Returns:
            {
                "within_budget": bool,
                "usage_pct": float,
                "remaining": float,
                "alert": bool
            }
        """
        usage_pct = (self.total_cost / self.budget_per_project) * 100
        within_budget = self.total_cost <= self.budget_per_project
        alert = usage_pct >= (self.alert_threshold * 100)

        return {
            "within_budget": within_budget,
            "usage_pct": round(usage_pct, 2),
            "remaining": round(self.budget_per_project - self.total_cost, 6),
            "alert": alert
        }

    def reset(self):
        """
        Reset session costs.

        Note: Does not delete the JSONL log file, only clears in-memory data.
        """
        self.session_costs = []
        self.total_cost = 0.0
        self.logger.info("Cost tracker reset (session costs cleared)")

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return (
            f"<CostTracker(total_cost=${self.total_cost:.4f}, "
            f"queries={len(self.session_costs)}, "
            f"budget=${self.budget_per_project:.2f})>"
        )
