#!/usr/bin/env python
"""
SpringMVC Agent Analyzer - SDK Agent Mode Entry Point.

This script starts the SDK Agent mode for interactive dialogue-driven analysis.

Usage:
    # Interactive mode
    python run_sdk_agent.py --interactive

    # Batch analysis
    python run_sdk_agent.py --analyze-project src/main/java --output-format markdown

    # Validate configuration
    python run_sdk_agent.py --validate-config

    # Custom config
    python run_sdk_agent.py --interactive --config config/custom_config.yaml
"""

import asyncio
import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

from sdk_agent.client import SpringMVCAnalyzerAgent
from sdk_agent.config import load_config, validate_config_file
from sdk_agent.exceptions import ConfigurationError, AgentNotInitializedError
from sdk_agent.constants import (
    DEFAULT_LOG_LEVEL,
    DEFAULT_LOG_FILE,
    LOG_FORMAT,
    VALID_OUTPUT_FORMATS,
)


def setup_logging(level: str = DEFAULT_LOG_LEVEL, log_file: Optional[str] = None):
    """
    Setup logging configuration for SDK Agent.

    Uses module-specific loggers to avoid conflicts with other components.
    """
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    # File handler (if specified)
    handlers = [console_handler]
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        handlers.append(file_handler)

    # Configure SDK agent logger (not root logger to avoid conflicts)
    sdk_logger = logging.getLogger("sdk_agent")
    sdk_logger.setLevel(level)
    sdk_logger.handlers = handlers
    sdk_logger.propagate = False


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="SpringMVC Agent Analyzer - SDK Agent Mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python run_sdk_agent.py --interactive

  # Batch analysis
  python run_sdk_agent.py --analyze-project src/main/java

  # Validate configuration
  python run_sdk_agent.py --validate-config

  # Custom config
  python run_sdk_agent.py --interactive --config config/custom.yaml
        """
    )

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Start interactive dialogue mode"
    )
    mode_group.add_argument(
        "--analyze-project",
        metavar="PATH",
        help="Analyze entire project (batch mode)"
    )
    mode_group.add_argument(
        "--validate-config",
        action="store_true",
        help="Validate configuration file"
    )

    # Configuration
    parser.add_argument(
        "-c", "--config",
        default="config/sdk_agent_config.yaml",
        help="Path to configuration file (default: config/sdk_agent_config.yaml)"
    )

    # Output options
    parser.add_argument(
        "--output-format",
        choices=VALID_OUTPUT_FORMATS,
        default="markdown",
        help="Output format for batch analysis (default: markdown)"
    )

    parser.add_argument(
        "--output-path",
        help="Output file path for batch analysis"
    )

    # Agent options
    parser.add_argument(
        "--no-hooks",
        action="store_true",
        help="Disable hooks system"
    )

    parser.add_argument(
        "--permission-mode",
        choices=["acceptAll", "acceptEdits", "rejectAll"],
        help="Permission mode (overrides config)"
    )

    parser.add_argument(
        "--max-turns",
        type=int,
        help="Maximum conversation turns (overrides config)"
    )

    # Logging options
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )

    parser.add_argument(
        "--log-file",
        help="Log to file"
    )

    # Dry run
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run (validate only, don't execute)"
    )

    return parser.parse_args()


async def validate_config_command(config_path: str) -> int:
    """
    Validate configuration file.

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        print(f"Validating configuration: {config_path}")
        validate_config_file(config_path)

        print("✅ Configuration is valid!")
        print(f"   Config file: {config_path}")

        # Load and display config
        config = load_config(config_path)
        print(f"   Mode: {config.mode}")
        print(f"   Model: {config.default_model}")
        print(f"   Hooks enabled: {config.hooks_enabled}")
        print(f"   Permission mode: {config.permission_mode}")
        print(f"   Max turns: {config.max_turns}")

        return 0

    except ConfigurationError as e:
        print(f"❌ Configuration error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


async def interactive_mode(agent: SpringMVCAnalyzerAgent, dry_run: bool = False) -> int:
    """
    Start interactive mode.

    Returns:
        Exit code
    """
    try:
        if dry_run:
            print("✅ Dry run: Interactive mode validated successfully")
            print(f"   System prompt loaded: {len(agent.system_prompt)} chars")
            print(f"   Hooks enabled: {agent.config.hooks_enabled}")
            print(f"   Permission mode: {agent.config.permission_mode}")
            return 0

        # Start interactive mode
        await agent.start_interactive()
        return 0

    except AgentNotInitializedError as e:
        print(f"❌ Agent initialization error: {e}")
        print("\nNote: Full SDK Agent implementation coming in Phase 5.")
        print("      Currently showing placeholder functionality.")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


async def batch_analysis_mode(
    agent: SpringMVCAnalyzerAgent,
    project_path: str,
    output_format: str,
    output_path: Optional[str],
    dry_run: bool = False
) -> int:
    """
    Run batch analysis.

    Returns:
        Exit code
    """
    try:
        if dry_run:
            print(f"✅ Dry run: Batch analysis validated successfully")
            print(f"   Project path: {project_path}")
            print(f"   Output format: {output_format}")
            if output_path:
                print(f"   Output path: {output_path}")
            return 0

        # Analyze project
        result = await agent.analyze_project(
            project_path=project_path,
            output_format=output_format
        )

        # Save results
        if output_path:
            import json
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            if output_format == "json":
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
            else:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(str(result))

            print(f"✅ Results saved to: {output_path}")
        else:
            print(result)

        return 0

    except AgentNotInitializedError as e:
        print(f"❌ Agent initialization error: {e}")
        print("\nNote: Full SDK Agent implementation coming in Phase 5.")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


async def main():
    """Main entry point."""
    args = parse_args()

    # Setup logging
    log_file = args.log_file
    if not log_file and not args.validate_config:
        # Use default log file
        log_file = DEFAULT_LOG_FILE

    setup_logging(level=args.log_level, log_file=log_file)
    logger = logging.getLogger("sdk_agent")

    logger.info("Starting SDK Agent mode...")
    logger.info(f"Arguments: {vars(args)}")

    # Validate config command
    if args.validate_config:
        return await validate_config_command(args.config)

    # Initialize agent
    try:
        agent = SpringMVCAnalyzerAgent(
            config_path=args.config,
            hooks_enabled=not args.no_hooks,
            permission_mode=args.permission_mode,
            max_turns=args.max_turns
        )

        print("🤖 SpringMVC Agent Analyzer - SDK Agent Mode")
        print("=" * 60)
        print(f"Config: {args.config}")
        print(f"Mode: {agent.config.mode}")
        print(f"Model: {agent.config.default_model}")
        print(f"Hooks: {'Enabled' if agent.config.hooks_enabled else 'Disabled'}")
        print(f"Permission: {agent.config.permission_mode}")
        print("=" * 60)
        print()

    except ConfigurationError as e:
        print(f"❌ Configuration error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        logger.exception("Agent initialization failed")
        return 1

    # Run mode
    if args.interactive:
        return await interactive_mode(agent, dry_run=args.dry_run)
    elif args.analyze_project:
        return await batch_analysis_mode(
            agent,
            args.analyze_project,
            args.output_format,
            args.output_path,
            dry_run=args.dry_run
        )


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
