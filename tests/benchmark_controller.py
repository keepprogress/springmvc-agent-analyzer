"""
Benchmark script for Controller Agent POC validation.

This script:
1. Loads test fixtures and gold standard
2. Runs ControllerAgent analysis on each fixture
3. Compares results against gold standard
4. Calculates accuracy metrics (precision, recall, F1)
5. Tracks costs and model usage
6. Generates benchmark report
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.controller_agent import ControllerAgent
from core.model_router import ModelRouter
from core.prompt_manager import PromptManager
from core.cost_tracker import CostTracker
from core.cache_manager import CacheManager
from core.config_loader import load_config


class BenchmarkMetrics:
    """Tracks benchmark metrics for controller analysis."""

    def __init__(self):
        self.total_files = 0
        self.total_cost = 0.0
        self.total_tokens_input = 0
        self.total_tokens_output = 0

        # Model usage tracking
        self.model_usage = {
            "haiku": 0,
            "sonnet": 0,
            "opus": 0
        }

        # Accuracy metrics
        self.class_name_matches = 0
        self.package_matches = 0
        self.controller_type_matches = 0
        self.mapping_precision = []  # Per-file precision for mappings
        self.mapping_recall = []     # Per-file recall for mappings
        self.dependency_precision = []
        self.dependency_recall = []

        # Detailed results
        self.results = []

    def add_result(
        self,
        file_name: str,
        gold: Dict[str, Any],
        predicted: Dict[str, Any],
        cost: float,
        model: str,
        confidence: float
    ):
        """Add a single file's benchmark result."""
        self.total_files += 1
        self.total_cost += cost

        # Track model usage
        if "haiku" in model.lower():
            self.model_usage["haiku"] += 1
        elif "sonnet" in model.lower():
            self.model_usage["sonnet"] += 1
        elif "opus" in model.lower():
            self.model_usage["opus"] += 1

        # Compare class name
        class_match = gold.get("class_name") == predicted.get("class_name")
        if class_match:
            self.class_name_matches += 1

        # Compare package
        package_match = gold.get("package") == predicted.get("package")
        if package_match:
            self.package_matches += 1

        # Compare controller type
        type_match = gold.get("controller_type") == predicted.get("controller_type")
        if type_match:
            self.controller_type_matches += 1

        # Compare mappings
        mapping_prec, mapping_rec = self._compare_mappings(
            gold.get("mappings", []),
            predicted.get("mappings", [])
        )
        self.mapping_precision.append(mapping_prec)
        self.mapping_recall.append(mapping_rec)

        # Compare dependencies
        dep_prec, dep_rec = self._compare_dependencies(
            gold.get("dependencies", []),
            predicted.get("dependencies", [])
        )
        self.dependency_precision.append(dep_prec)
        self.dependency_recall.append(dep_rec)

        # Store detailed result
        self.results.append({
            "file": file_name,
            "class_name_match": class_match,
            "package_match": package_match,
            "controller_type_match": type_match,
            "mapping_precision": mapping_prec,
            "mapping_recall": mapping_rec,
            "dependency_precision": dep_prec,
            "dependency_recall": dep_rec,
            "cost": cost,
            "model": model,
            "confidence": confidence
        })

    def _compare_mappings(
        self,
        gold_mappings: List[Dict],
        pred_mappings: List[Dict]
    ) -> Tuple[float, float]:
        """Calculate precision and recall for mappings."""
        if not gold_mappings and not pred_mappings:
            return 1.0, 1.0

        if not pred_mappings:
            return 0.0, 0.0

        if not gold_mappings:
            return 0.0, 1.0

        # Count matches by method_name + path
        # Note: We compare method_name and path only, because http_method
        # might be represented differently (e.g., "GET|POST" vs separate entries)
        gold_keys = {
            (m.get("method_name"), m.get("path"))
            for m in gold_mappings
        }
        pred_keys = {
            (m.get("method_name"), m.get("path"))
            for m in pred_mappings
        }

        matches = len(gold_keys & pred_keys)

        # Also check http_method matches for matched mappings
        http_method_matches = 0
        for gold_m in gold_mappings:
            for pred_m in pred_mappings:
                if (gold_m.get("method_name") == pred_m.get("method_name") and
                    gold_m.get("path") == pred_m.get("path")):
                    # Exact match or subset match (for multi-method cases)
                    if gold_m.get("http_method") == pred_m.get("http_method"):
                        http_method_matches += 1
                    break

        # Precision: how many predicted were correct
        precision = matches / len(pred_keys) if pred_keys else 0.0

        # Recall: how many gold standards were found
        recall = matches / len(gold_keys) if gold_keys else 0.0

        return precision, recall

    def _compare_dependencies(
        self,
        gold_deps: List[Dict],
        pred_deps: List[Dict]
    ) -> Tuple[float, float]:
        """Calculate precision and recall for dependencies."""
        if not gold_deps and not pred_deps:
            return 1.0, 1.0

        if not pred_deps:
            return 0.0, 0.0

        if not gold_deps:
            return 0.0, 1.0

        # Count matches by field_name + type
        gold_keys = {
            (d.get("field_name"), d.get("type"))
            for d in gold_deps
        }
        pred_keys = {
            (d.get("field_name"), d.get("type"))
            for d in pred_deps
        }

        matches = len(gold_keys & pred_keys)

        precision = matches / len(pred_keys) if pred_keys else 0.0
        recall = matches / len(gold_keys) if gold_keys else 0.0

        return precision, recall

    def generate_report(self) -> str:
        """Generate benchmark report."""
        if self.total_files == 0:
            return "No benchmark results available"

        # Calculate averages
        avg_mapping_prec = sum(self.mapping_precision) / len(self.mapping_precision)
        avg_mapping_rec = sum(self.mapping_recall) / len(self.mapping_recall)
        avg_dep_prec = sum(self.dependency_precision) / len(self.dependency_precision)
        avg_dep_rec = sum(self.dependency_recall) / len(self.dependency_recall)

        # F1 scores
        mapping_f1 = (
            2 * avg_mapping_prec * avg_mapping_rec / (avg_mapping_prec + avg_mapping_rec)
            if (avg_mapping_prec + avg_mapping_rec) > 0 else 0.0
        )
        dep_f1 = (
            2 * avg_dep_prec * avg_dep_rec / (avg_dep_prec + avg_dep_rec)
            if (avg_dep_prec + avg_dep_rec) > 0 else 0.0
        )

        # Overall accuracy
        class_accuracy = self.class_name_matches / self.total_files
        package_accuracy = self.package_matches / self.total_files
        type_accuracy = self.controller_type_matches / self.total_files

        # Model distribution percentages
        total = self.total_files
        haiku_pct = (self.model_usage["haiku"] / total * 100) if total else 0
        sonnet_pct = (self.model_usage["sonnet"] / total * 100) if total else 0
        opus_pct = (self.model_usage["opus"] / total * 100) if total else 0

        report = f"""
╔══════════════════════════════════════════════════════════════╗
║         Controller Agent POC Benchmark Report               ║
╚══════════════════════════════════════════════════════════════╝

📊 OVERALL METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Total Files Analyzed:  {self.total_files}
  Total Cost:            ${self.total_cost:.4f}
  Average Cost/File:     ${self.total_cost/self.total_files:.4f}

🎯 ACCURACY METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Class Name Accuracy:   {class_accuracy*100:.1f}% ({self.class_name_matches}/{self.total_files})
  Package Accuracy:      {package_accuracy*100:.1f}% ({self.package_matches}/{self.total_files})
  Controller Type Acc:   {type_accuracy*100:.1f}% ({self.controller_type_matches}/{self.total_files})

  Mapping Precision:     {avg_mapping_prec*100:.1f}%
  Mapping Recall:        {avg_mapping_rec*100:.1f}%
  Mapping F1 Score:      {mapping_f1*100:.1f}%

  Dependency Precision:  {avg_dep_prec*100:.1f}%
  Dependency Recall:     {avg_dep_rec*100:.1f}%
  Dependency F1 Score:   {dep_f1*100:.1f}%

🤖 MODEL USAGE DISTRIBUTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Haiku (cheap):   {self.model_usage['haiku']:2d} files ({haiku_pct:.1f}%)
  Sonnet (medium): {self.model_usage['sonnet']:2d} files ({sonnet_pct:.1f}%)
  Opus (premium):  {self.model_usage['opus']:2d} files ({opus_pct:.1f}%)

✅ POC SUCCESS CRITERIA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ Accuracy >= 90%:     {'✅ PASS' if mapping_f1 >= 0.90 else '❌ FAIL'} ({mapping_f1*100:.1f}%)
  ✓ Cost <= $1 for 20:   {'✅ PASS' if self.total_cost <= 1.0 else '❌ FAIL'} (${self.total_cost:.4f})
  ✓ Cache hit rate:      (See cache_manager.json)

📋 DETAILED RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        for r in self.results:
            status = "✅" if r["mapping_precision"] >= 0.9 and r["mapping_recall"] >= 0.9 else "⚠️"
            report += f"""
  {status} {r['file']:25s} | F1: {self._f1(r['mapping_precision'], r['mapping_recall'])*100:5.1f}% | Cost: ${r['cost']:.4f} | {r['model']}"""

        report += "\n\n"

        return report

    def _f1(self, precision: float, recall: float) -> float:
        """Calculate F1 score."""
        if precision + recall == 0:
            return 0.0
        return 2 * precision * recall / (precision + recall)


async def run_benchmark():
    """Run the benchmark suite."""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("benchmark")

    # Early validation: Check API key is set
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("=" * 60)
        logger.error("ANTHROPIC_API_KEY environment variable not set!")
        logger.error("=" * 60)
        logger.error("")
        logger.error("Please set your API key before running benchmark:")
        logger.error("  export ANTHROPIC_API_KEY=your_key_here")
        logger.error("")
        logger.error("Or create a .env file in project root:")
        logger.error("  ANTHROPIC_API_KEY=your_key_here")
        logger.error("")
        sys.exit(1)

    # Load config
    config = load_config()

    # Initialize components with appropriate parameters
    cost_tracker = CostTracker(
        output_file="output/benchmark_cost_tracker.jsonl",
        budget_per_project=config.get("cost", {}).get("budget_per_project", 5.0),
        alert_threshold=config.get("cost", {}).get("alert_threshold", 0.8)
    )

    cache_manager = CacheManager(
        cache_dir=config.get("cache", {}).get("cache_dir", ".cache"),
        ttl_days=config.get("cache", {}).get("ttl_days", 30),
        max_cache_size=config.get("cache", {}).get("max_size", 10000)
    )

    model_router = ModelRouter(
        config_path="config/config.yaml"
    )

    prompt_manager = PromptManager(
        prompts_dir="prompts"
    )

    # Initialize ControllerAgent
    agent = ControllerAgent(
        model_router=model_router,
        prompt_manager=prompt_manager,
        cost_tracker=cost_tracker,
        cache_manager=cache_manager,
        config=config
    )

    # Setup paths
    fixtures_dir = project_root / "tests" / "fixtures" / "controllers"
    gold_dir = project_root / "tests" / "fixtures" / "gold_standard"

    # Initialize metrics
    metrics = BenchmarkMetrics()

    logger.info("Starting Controller Agent Benchmark...")
    logger.info(f"Fixtures dir: {fixtures_dir}")
    logger.info(f"Gold standard dir: {gold_dir}")

    # Get all test fixtures
    test_files = sorted(fixtures_dir.glob("*.java"))

    if not test_files:
        logger.error(f"No test fixtures found in {fixtures_dir}")
        return

    logger.info(f"Found {len(test_files)} test fixtures")

    # Checkpoint/resume capability - save progress after each file
    checkpoint_file = project_root / "output" / "benchmark_checkpoint.json"
    completed_files = set()

    if checkpoint_file.exists():
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
                completed_files = set(checkpoint_data.get("completed", []))
                logger.info(f"Resuming from checkpoint: {len(completed_files)} files already completed")
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}, starting fresh")
            completed_files = set()

    # Run analysis on each fixture
    for test_file in test_files:
        file_name = test_file.stem
        gold_file = gold_dir / f"{file_name}.json"

        # Skip if already completed (resume capability)
        if file_name in completed_files:
            logger.info(f"Skipping {file_name} (already completed)")
            continue

        if not gold_file.exists():
            logger.warning(f"No gold standard for {file_name}, skipping")
            continue

        logger.info(f"\n{'='*60}")
        logger.info(f"Analyzing: {file_name}")
        logger.info(f"{'='*60}")

        # Load gold standard
        with open(gold_file, 'r', encoding='utf-8') as f:
            gold_standard = json.load(f)

        # Run analysis
        try:
            result = await agent.analyze(str(test_file))

            # Extract analysis from result
            analysis = result.get("analysis", {})
            cost = result.get("cost", 0.0)
            model = result.get("model_used", "unknown")
            confidence = result.get("confidence", 0.0)

            # Validate analysis structure
            if not isinstance(analysis, dict):
                logger.warning(f"Analysis is not a dict for {file_name}, skipping metrics")
                continue

            # Ensure required fields have default values if missing
            analysis.setdefault("class_name", "unknown")
            analysis.setdefault("package", "unknown")
            analysis.setdefault("controller_type", "unknown")
            analysis.setdefault("mappings", [])
            analysis.setdefault("dependencies", [])

            # Add to metrics
            metrics.add_result(
                file_name=file_name,
                gold=gold_standard,
                predicted=analysis,
                cost=cost,
                model=model,
                confidence=confidence
            )

            logger.info(f"✓ Analysis complete: cost=${cost:.4f}, model={model}, confidence={confidence:.2f}")

            # Save checkpoint after successful analysis
            completed_files.add(file_name)
            checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump({"completed": list(completed_files)}, f)

        except Exception as e:
            logger.error(f"✗ Analysis failed for {file_name}: {e}")
            import traceback
            traceback.print_exc()

    # Generate and display report
    report = metrics.generate_report()
    print(report)

    # Save report to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = project_root / "output" / f"benchmark_report_{timestamp}.txt"
    report_file.parent.mkdir(parents=True, exist_ok=True)

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    logger.info(f"\n📄 Report saved to: {report_file}")

    # Save detailed results as JSON
    results_file = project_root / "output" / f"benchmark_results_{timestamp}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(metrics.results, f, indent=2)

    logger.info(f"📊 Detailed results saved to: {results_file}")

    # Save cost tracker data
    cost_tracker.save()
    cache_manager.save()

    # Clean up checkpoint file on successful completion
    if checkpoint_file.exists():
        try:
            checkpoint_file.unlink()
            logger.info("Checkpoint file cleaned up")
        except Exception as e:
            logger.warning(f"Failed to clean up checkpoint: {e}")

    logger.info("\n✅ Benchmark complete!")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
