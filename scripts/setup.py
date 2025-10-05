#!/usr/bin/env python3
"""
Setup script for SpringMVC Agent Analyzer.

Initializes project structure, validates configuration, and tests API connectivity.
"""

import os
import sys
from pathlib import Path
import yaml
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run setup checks and initialization."""
    print("🚀 SpringMVC Agent Analyzer Setup\n")
    print("=" * 60)

    # Check 1: Python version
    print("\n[1/6] Checking Python version...")
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required")
        print(f"   Current version: {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} OK")

    # Check 2: ANTHROPIC_API_KEY
    print("\n[2/6] Checking ANTHROPIC_API_KEY...")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable not set")
        print("   Set it in .env or export ANTHROPIC_API_KEY=your_key")
        sys.exit(1)
    print(f"✅ ANTHROPIC_API_KEY found ({len(api_key)} chars)")

    # Check 3: Test API connectivity
    print("\n[3/6] Testing Anthropic API connection...")
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        print("✅ Anthropic API connection OK")
    except ImportError:
        print("❌ anthropic package not installed")
        print("   Run: pip install anthropic")
        sys.exit(1)
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        sys.exit(1)

    # Check 4: Create output directories
    print("\n[4/6] Creating output directories...")
    directories = ["output", ".cache", "prompts/base", "prompts/examples", "prompts/learned"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    print(f"✅ Created {len(directories)} directories")

    # Check 5: Validate config
    print("\n[5/6] Validating configuration...")
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        print("❌ config/config.yaml not found")
        sys.exit(1)

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Check required keys
        required_keys = [
            ("llm", "routing", "screening_model"),
            ("llm", "routing", "screening_cost_per_mtok_input"),
            ("llm", "routing", "screening_cost_per_mtok_output"),
            ("llm", "routing", "analysis_model"),
            ("llm", "routing", "analysis_cost_per_mtok_input"),
            ("llm", "routing", "analysis_cost_per_mtok_output"),
            ("llm", "thresholds", "screening_confidence"),
            ("llm", "thresholds", "analysis_confidence"),
            ("agents", "min_confidence"),
            ("cache", "enabled"),
            ("cost", "budget_per_project"),
        ]

        missing_keys = []
        for key_path in required_keys:
            obj = config
            for key in key_path:
                if key not in obj:
                    missing_keys.append(".".join(key_path))
                    break
                obj = obj[key]

        if missing_keys:
            print(f"❌ Missing config keys: {missing_keys}")
            sys.exit(1)

        print("✅ Configuration valid")

    except yaml.YAMLError as e:
        print(f"❌ Invalid YAML in config file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Config validation error: {e}")
        sys.exit(1)

    # Check 6: Test core imports
    print("\n[6/6] Testing core module imports...")
    try:
        from core import ModelRouter, PromptManager, CacheManager, CostTracker
        from agents import BaseAgent
        print("✅ All core modules import successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        sys.exit(1)

    # Success summary
    print("\n" + "=" * 60)
    print("✨ Setup complete! System is ready.")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("  1. Review configuration: config/config.yaml")
    print("  2. Run integration test: python scripts/test_integration.py")
    print("  3. Start implementing agents (Phase 2)")
    print("\n💡 Useful commands:")
    print("  - Clear cache: rm -rf .cache/*")
    print("  - View costs: cat output/cost_tracker.jsonl")
    print("")


if __name__ == "__main__":
    main()
