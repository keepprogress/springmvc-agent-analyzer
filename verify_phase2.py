#!/usr/bin/env python
"""
Verification script for Phase 2: Infrastructure.

Verifies that all Phase 2 components are correctly set up.
"""

import sys
from pathlib import Path
from typing import List, Tuple

def check_file_exists(file_path: str) -> Tuple[bool, str]:
    """Check if file exists."""
    path = Path(file_path)
    if path.exists():
        return True, f"✅ {file_path}"
    else:
        return False, f"❌ {file_path} - NOT FOUND"

def check_directory_exists(dir_path: str) -> Tuple[bool, str]:
    """Check if directory exists."""
    path = Path(dir_path)
    if path.exists() and path.is_dir():
        return True, f"✅ {dir_path}/"
    else:
        return False, f"❌ {dir_path}/ - NOT FOUND"

def verify_phase2() -> int:
    """
    Verify Phase 2 infrastructure.

    Returns:
        Exit code (0 = success, 1 = error)
    """
    print("=" * 70)
    print("Phase 2: Infrastructure Verification")
    print("=" * 70)
    print()

    all_passed = True

    # Check directories
    print("📁 Checking directories...")
    directories = [
        "sdk_agent",
        "sdk_agent/tools",
        "sdk_agent/hooks",
        "config",
        "prompts/sdk_agent",
    ]

    for directory in directories:
        passed, message = check_directory_exists(directory)
        print(f"   {message}")
        if not passed:
            all_passed = False

    print()

    # Check Python files
    print("🐍 Checking Python files...")
    python_files = [
        "sdk_agent/__init__.py",
        "sdk_agent/client.py",
        "sdk_agent/config.py",
        "sdk_agent/exceptions.py",
        "sdk_agent/utils.py",
        "sdk_agent/permissions.py",
        "sdk_agent/tools/__init__.py",
        "sdk_agent/hooks/__init__.py",
        "run_sdk_agent.py",
    ]

    for file_path in python_files:
        passed, message = check_file_exists(file_path)
        print(f"   {message}")
        if not passed:
            all_passed = False

    print()

    # Check configuration files
    print("⚙️  Checking configuration files...")
    config_files = [
        "config/sdk_agent_config.yaml",
        "config/sdk_agent_config.example.yaml",
    ]

    for file_path in config_files:
        passed, message = check_file_exists(file_path)
        print(f"   {message}")
        if not passed:
            all_passed = False

    print()

    # Check prompts
    print("💬 Checking prompts...")
    prompt_files = [
        "prompts/sdk_agent/system_prompt.md",
    ]

    for file_path in prompt_files:
        passed, message = check_file_exists(file_path)
        print(f"   {message}")
        if not passed:
            all_passed = False

    print()

    # Try importing SDK agent modules
    print("📦 Checking imports...")
    try:
        from sdk_agent import SpringMVCAnalyzerAgent
        print("   ✅ sdk_agent.SpringMVCAnalyzerAgent")
    except ImportError as e:
        print(f"   ❌ Failed to import SpringMVCAnalyzerAgent: {e}")
        all_passed = False

    try:
        from sdk_agent.config import load_config, SDKAgentConfig
        print("   ✅ sdk_agent.config")
    except ImportError as e:
        print(f"   ❌ Failed to import config: {e}")
        all_passed = False

    try:
        from sdk_agent.exceptions import SDKAgentError, ConfigurationError
        print("   ✅ sdk_agent.exceptions")
    except ImportError as e:
        print(f"   ❌ Failed to import exceptions: {e}")
        all_passed = False

    try:
        from sdk_agent.utils import detect_file_type, format_tool_result
        print("   ✅ sdk_agent.utils")
    except ImportError as e:
        print(f"   ❌ Failed to import utils: {e}")
        all_passed = False

    try:
        from sdk_agent.permissions import PermissionManager
        print("   ✅ sdk_agent.permissions")
    except ImportError as e:
        print(f"   ❌ Failed to import permissions: {e}")
        all_passed = False

    print()

    # Try loading configuration
    print("🔧 Checking configuration loading...")
    try:
        from sdk_agent.config import load_config
        config = load_config("config/sdk_agent_config.yaml")
        print(f"   ✅ Config loaded successfully")
        print(f"      Mode: {config.mode}")
        print(f"      Model: {config.default_model}")
        print(f"      Hooks: {config.hooks_enabled}")
        print(f"      Permission: {config.permission_mode}")
    except Exception as e:
        print(f"   ❌ Failed to load config: {e}")
        all_passed = False

    print()

    # Try creating agent
    print("🤖 Checking agent creation...")
    try:
        from sdk_agent import SpringMVCAnalyzerAgent
        agent = SpringMVCAnalyzerAgent(
            config_path="config/sdk_agent_config.yaml"
        )
        print(f"   ✅ Agent created successfully")
        print(f"      System prompt: {len(agent.system_prompt)} chars")
        print(f"      Config mode: {agent.config.mode}")
    except Exception as e:
        print(f"   ❌ Failed to create agent: {e}")
        all_passed = False

    print()
    print("=" * 70)

    if all_passed:
        print("✅ Phase 2 verification PASSED!")
        print()
        print("📋 Summary:")
        print("   - All directories created")
        print("   - All Python files present")
        print("   - All configuration files present")
        print("   - All imports working")
        print("   - Configuration loads successfully")
        print("   - Agent initializes successfully")
        print()
        print("🎉 Phase 2: Infrastructure is complete!")
        return 0
    else:
        print("❌ Phase 2 verification FAILED!")
        print()
        print("Please check the errors above and fix them.")
        return 1

if __name__ == "__main__":
    exit_code = verify_phase2()
    sys.exit(exit_code)
