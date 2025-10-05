#!/usr/bin/env python3
"""
Integration test for Phase 1 core infrastructure.

Tests all core components working together without requiring a full agent implementation.
"""

import os
import sys
import asyncio
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import core components
from core import ModelRouter, PromptManager, CacheManager, CostTracker


async def test_model_router():
    """Test Model Router functionality."""
    print("\n" + "=" * 60)
    print("TEST 1: Model Router")
    print("=" * 60)

    router = ModelRouter("config/config.yaml")
    print(f"✓ ModelRouter initialized: {router}")

    # Test simple query with forced model
    print("\n• Testing Haiku query (forced)...")
    prompt = """
    Analyze this simple code and return JSON:

    ```java
    public class Test {
        public String hello() {
            return "Hello";
        }
    }
    ```

    Return: {"class_name": "Test", "confidence": 0.95}
    """

    try:
        result = await router.query(prompt, force_model="haiku", max_tokens=100)
        print(f"  Model: {result['model']}")
        print(f"  Cost: ${result['cost']:.6f}")
        print(f"  Tokens: {result['tokens']}")
        print(f"  Confidence: {result.get('confidence', 'N/A')}")
        print("✓ Haiku query successful")
    except Exception as e:
        print(f"✗ Haiku query failed: {e}")
        return False

    return True


def test_prompt_manager():
    """Test Prompt Manager functionality."""
    print("\n" + "=" * 60)
    print("TEST 2: Prompt Manager")
    print("=" * 60)

    manager = PromptManager("prompts")
    print(f"✓ PromptManager initialized: {manager}")

    # Create a simple test template
    test_template_path = Path("prompts/base/test_template.txt")
    test_template_path.write_text(
        "Analyze this {file_type} file:\n\n{code}\n\nReturn JSON with confidence score."
    )

    print(f"\n• Created test template: {test_template_path}")

    # Reload to pick up new template
    manager.reload()
    print(f"✓ Reloaded templates: {manager.list_templates()}")

    # Build prompt
    try:
        prompt = manager.build_prompt(
            template_name="test_template",
            context={
                "file_type": "Java",
                "code": "public class Test {}"
            },
            include_examples=False
        )
        print(f"✓ Built prompt ({len(prompt)} chars)")
        print(f"  Preview: {prompt[:100]}...")
    except Exception as e:
        print(f"✗ Prompt building failed: {e}")
        return False

    # Test learning mechanism
    print("\n• Testing learning mechanism...")
    manager.learn_from_result(
        template_name="test_template",
        input_data={"file_type": "Java", "code": "test"},
        output={"result": "success"},
        feedback={"correct": True}
    )
    print(f"✓ Learned {len(manager.learned_patterns)} pattern(s)")

    # Cleanup
    test_template_path.unlink()

    return True


def test_cache_manager():
    """Test Cache Manager functionality."""
    print("\n" + "=" * 60)
    print("TEST 3: Cache Manager")
    print("=" * 60)

    cache = CacheManager(cache_dir=".cache", ttl_days=30)
    print(f"✓ CacheManager initialized: {cache}")

    # Test save and retrieve
    print("\n• Testing cache save/retrieve...")
    test_result = {
        "analysis": {"test": "data"},
        "confidence": 0.95,
        "model_used": "test-model",
        "cost": 0.001
    }

    cache.save(
        agent_name="test_agent",
        file_path="test_file.java",
        file_content="public class Test {}",
        result=test_result
    )
    print("✓ Saved to cache")

    # Retrieve
    cached_result = cache.get(
        agent_name="test_agent",
        file_path="test_file.java",
        file_content="public class Test {}"
    )

    if cached_result == test_result:
        print("✓ Cache retrieval successful (exact match)")
    else:
        print("✗ Cache retrieval failed (mismatch)")
        return False

    # Test cache miss (different content)
    print("\n• Testing cache miss...")
    missed = cache.get(
        agent_name="test_agent",
        file_path="test_file.java",
        file_content="public class Different {}"
    )

    if missed is None:
        print("✓ Cache miss works correctly")
    else:
        print("✗ Cache miss failed (should be None)")
        return False

    # Print stats
    print("\n• Cache statistics:")
    cache.print_stats()

    return True


def test_cost_tracker():
    """Test Cost Tracker functionality."""
    print("\n" + "=" * 60)
    print("TEST 4: Cost Tracker")
    print("=" * 60)

    tracker = CostTracker(
        output_file="output/test_cost_tracker.jsonl",
        budget_per_project=5.0
    )
    print(f"✓ CostTracker initialized: {tracker}")

    # Record some costs
    print("\n• Recording test costs...")
    tracker.record(
        agent="test_agent",
        model="claude-3-5-haiku-20241022",
        tokens={"input": 1000, "output": 500},
        cost=0.001
    )
    tracker.record(
        agent="test_agent",
        model="cache",
        tokens={"input": 0, "output": 0},
        cost=0.0,
        cached=True
    )
    tracker.record(
        agent="another_agent",
        model="claude-3-5-sonnet-20250929",
        tokens={"input": 2000, "output": 1000},
        cost=0.021
    )
    print(f"✓ Recorded {len(tracker.session_costs)} queries")

    # Get summary
    print("\n• Cost summary:")
    tracker.print_summary()

    # Check budget
    budget_status = tracker.check_budget()
    print(f"\n• Budget check: {budget_status}")

    if budget_status["within_budget"]:
        print("✓ Within budget")
    else:
        print("✗ Over budget")

    return True


async def test_integration():
    """Test all components integrated together."""
    print("\n" + "=" * 60)
    print("TEST 5: Full Integration")
    print("=" * 60)

    # Initialize all components
    print("\n• Initializing all components...")
    router = ModelRouter("config/config.yaml")
    manager = PromptManager("prompts")
    cache = CacheManager(".cache")
    tracker = CostTracker("output/integration_test_cost.jsonl")

    print("✓ All components initialized")

    # Create a mini workflow
    print("\n• Simulating analysis workflow...")

    # 1. Build prompt
    test_template = Path("prompts/base/integration_test.txt")
    test_template.write_text(
        "Analyze: {code}\nReturn JSON: {{\"result\": \"test\", \"confidence\": 0.9}}"
    )
    manager.reload()

    prompt = manager.build_prompt(
        "integration_test",
        {"code": "test code"},
        include_examples=False
    )
    print("  1. ✓ Prompt built")

    # 2. Check cache (should be miss)
    file_content = "test code content"
    cached = cache.get("integration_test", "test.java", file_content)
    if cached is None:
        print("  2. ✓ Cache miss (expected)")
    else:
        print("  2. ✗ Unexpected cache hit")
        return False

    # 3. Query LLM
    llm_result = await router.query(prompt, force_model="haiku", max_tokens=50)
    print(f"  3. ✓ LLM queried (cost: ${llm_result['cost']:.6f})")

    # 4. Track cost
    tracker.record(
        agent="integration_test",
        model=llm_result["model"],
        tokens=llm_result["tokens"],
        cost=llm_result["cost"],
        cached=False
    )
    print("  4. ✓ Cost tracked")

    # 5. Save to cache
    result = {
        "analysis": {"test": "result"},
        "confidence": 0.9,
        "model_used": llm_result["model"],
        "cost": llm_result["cost"]
    }
    cache.save("integration_test", "test.java", file_content, result)
    print("  5. ✓ Result cached")

    # 6. Verify cache hit on second attempt
    cached_second = cache.get("integration_test", "test.java", file_content)
    if cached_second == result:
        print("  6. ✓ Cache hit verified")
        tracker.record(
            agent="integration_test",
            model="cache",
            tokens={"input": 0, "output": 0},
            cost=0.0,
            cached=True
        )
    else:
        print("  6. ✗ Cache verification failed")
        return False

    # Cleanup
    test_template.unlink()

    print("\n✓ Full integration test passed!")
    print("\n• Final statistics:")
    cache.print_stats()
    tracker.print_summary()

    return True


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("SPRINGMVC AGENT ANALYZER - PHASE 1 INTEGRATION TESTS")
    print("=" * 70)

    # Check environment
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ ANTHROPIC_API_KEY not set. Please run setup.py first.")
        sys.exit(1)

    # Run tests
    tests = [
        ("Model Router", test_model_router()),
        ("Prompt Manager", test_prompt_manager()),
        ("Cache Manager", test_cache_manager()),
        ("Cost Tracker", test_cost_tracker()),
        ("Full Integration", test_integration())
    ]

    results = []
    for name, test in tests:
        if asyncio.iscoroutine(test):
            result = await test
        else:
            result = test
        results.append((name, result))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8s} - {name}")
        if not result:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n✅ All tests passed! Phase 1 infrastructure is ready.")
        print("\n📋 Next steps:")
        print("  - Implement ControllerAgent (Phase 2)")
        print("  - Create prompt templates for controller analysis")
        print("  - Add few-shot examples")
        return 0
    else:
        print("\n❌ Some tests failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
