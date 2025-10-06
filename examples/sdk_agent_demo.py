#!/usr/bin/env python3
"""
SDK Agent Mode Demo - SpringMVC Agent Analyzer

This demo showcases the three main usage patterns of SDK Agent Mode:
1. Interactive Mode - Conversational analysis
2. Batch Mode - Automated project analysis
3. Programmatic API - Custom workflows

Usage:
    # Interactive mode
    python sdk_agent_demo.py --interactive

    # Batch analysis
    python sdk_agent_demo.py --batch path/to/project

    # Custom workflow
    python sdk_agent_demo.py --custom
"""

import asyncio
import argparse
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sdk_agent.client import SpringMVCAnalyzerAgent


async def demo_interactive():
    """
    Demo 1: Interactive Mode

    Showcases conversational analysis where the agent autonomously
    selects tools and maintains context across multiple turns.
    """
    print("\n" + "="*70)
    print("Demo 1: Interactive Mode")
    print("="*70)
    print("\nStarting interactive session with SDK Agent...")
    print("Type 'exit' or 'quit' to end the session.\n")

    # Initialize agent with hooks enabled
    agent = SpringMVCAnalyzerAgent(
        config_path="config/sdk_agent_config.yaml",
        hooks_enabled=True,
        permission_mode="acceptEdits"
    )

    # Start interactive dialogue
    await agent.start_interactive()

    print("\n✓ Interactive session ended.")


async def demo_batch_analysis(project_path: str):
    """
    Demo 2: Batch Mode

    Automated analysis of entire project with single command.
    Agent analyzes all files, builds knowledge graph, and generates report.
    """
    print("\n" + "="*70)
    print("Demo 2: Batch Analysis Mode")
    print("="*70)
    print(f"\nAnalyzing project: {project_path}")
    print("This will:")
    print("  1. Scan all Java files")
    print("  2. Analyze Controllers, Services, Mappers")
    print("  3. Build dependency graph")
    print("  4. Generate analysis report\n")

    # Initialize agent
    agent = SpringMVCAnalyzerAgent(
        hooks_enabled=True,
        permission_mode="acceptAll"  # Auto-approve all tools for batch mode
    )

    # Run batch analysis
    result = await agent.analyze_project(
        project_path=project_path,
        output_format="markdown"
    )

    # Display results
    print("\n" + "-"*70)
    print("Analysis Complete!")
    print("-"*70)
    print(f"Project: {result['project_path']}")
    print(f"Format: {result['format']}")
    print(f"Success: {result['success']}")
    print("\nAnalysis Summary:")
    print(result['analysis'][:500] + "..." if len(result['analysis']) > 500 else result['analysis'])

    # Save full report
    output_file = Path("output") / "batch_analysis_report.md"
    output_file.parent.mkdir(exist_ok=True)
    output_file.write_text(result['analysis'], encoding='utf-8')
    print(f"\n✓ Full report saved to: {output_file}")


async def demo_custom_workflow():
    """
    Demo 3: Programmatic API

    Custom analysis workflow using direct tool calls.
    Demonstrates fine-grained control over the analysis process.
    """
    print("\n" + "="*70)
    print("Demo 3: Custom Workflow (Programmatic API)")
    print("="*70)
    print("\nExecuting custom analysis workflow...")

    # Initialize agent
    agent = SpringMVCAnalyzerAgent(hooks_enabled=True)

    # Custom workflow: Analyze specific files and build focused graph
    print("\nStep 1: Analyzing UserController...")

    # Use the SDK client for queries
    await agent.client.__aenter__()
    try:
        # Query 1: Analyze specific controller
        await agent.client.query(
            "Analyze the UserController and identify all its dependencies"
        )

        print("\nAgent Response:")
        async for message in agent.client.receive_response():
            print(message, end="")
        print("\n")

        # Query 2: Find impact
        await agent.client.query(
            "What would be the impact of modifying the UserService?"
        )

        print("\nImpact Analysis:")
        async for message in agent.client.receive_response():
            print(message, end="")
        print("\n")

        # Query 3: Export graph
        await agent.client.query(
            "Export the dependency graph to D3.js format"
        )

        print("\nGraph Export:")
        async for message in agent.client.receive_response():
            print(message, end="")
        print("\n")

    finally:
        await agent.client.__aexit__(None, None, None)

    print("✓ Custom workflow completed.")


async def demo_tools_showcase():
    """
    Demo 4: Tools Showcase

    Demonstrates all available tools and their capabilities.
    """
    print("\n" + "="*70)
    print("Demo 4: Available Tools Showcase")
    print("="*70)

    agent = SpringMVCAnalyzerAgent()
    tools = agent.get_tools()

    print(f"\nSDK Agent Mode provides {len(tools)} tools:\n")

    # Group tools by category
    analysis_tools = [t for t in tools if t['name'].startswith('analyze_')]
    graph_tools = [t for t in tools if 'graph' in t['name'].lower()]
    query_tools = [t for t in tools if any(x in t['name'] for x in ['query', 'find', 'impact'])]

    print("📊 Analysis Tools (6):")
    for tool in analysis_tools:
        print(f"  • {tool['name']}: {tool.get('description', 'N/A')[:60]}...")

    print("\n📈 Graph Tools (2):")
    for tool in graph_tools:
        print(f"  • {tool['name']}: {tool.get('description', 'N/A')[:60]}...")

    print("\n🔍 Query Tools (3):")
    for tool in query_tools:
        print(f"  • {tool['name']}: {tool.get('description', 'N/A')[:60]}...")

    print(f"\n✓ Total: {len(tools)} tools available")


async def demo_hooks_system():
    """
    Demo 5: Hooks System

    Demonstrates the 5 hook events and their effects.
    """
    print("\n" + "="*70)
    print("Demo 5: Hooks System")
    print("="*70)

    agent = SpringMVCAnalyzerAgent(hooks_enabled=True)
    hooks = agent.get_hooks()

    print(f"\nHooks System provides {len(hooks)} event hooks:\n")

    print("1. ValidationHook (PreToolUse)")
    print("   - Validates file paths for security")
    print("   - Prevents path traversal attacks")
    print("   - Checks file existence\n")

    print("2. CacheHook (PostToolUse)")
    print("   - Caches analysis results")
    print("   - Semantic similarity matching")
    print("   - Auto cache invalidation\n")

    print("3. CleanupHook (Stop)")
    print("   - Session cleanup on stop")
    print("   - Temporary file removal")
    print("   - Statistics logging\n")

    print("4. ContextManagerHook (PreCompact)")
    print("   - Smart context compression")
    print("   - Preserves important messages")
    print("   - Optimizes token usage\n")

    print("5. InputEnhancementHook (UserPromptSubmit)")
    print("   - Enhances user input")
    print("   - Adds project context")
    print("   - Improves query quality\n")

    print("✓ All hooks are active and monitoring tool execution")


def main():
    """Main entry point for demo."""
    parser = argparse.ArgumentParser(
        description="SpringMVC Agent Analyzer - SDK Agent Mode Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run interactive mode demo"
    )

    parser.add_argument(
        "--batch", "-b",
        metavar="PROJECT_PATH",
        help="Run batch analysis demo on specified project"
    )

    parser.add_argument(
        "--custom", "-c",
        action="store_true",
        help="Run custom workflow demo"
    )

    parser.add_argument(
        "--tools",
        action="store_true",
        help="Show available tools"
    )

    parser.add_argument(
        "--hooks",
        action="store_true",
        help="Show hooks system"
    )

    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run all non-interactive demos"
    )

    args = parser.parse_args()

    # Show help if no arguments
    if not any(vars(args).values()):
        parser.print_help()
        print("\n" + "="*70)
        print("Quick Start Examples:")
        print("="*70)
        print("\n# Show available tools")
        print("python sdk_agent_demo.py --tools")
        print("\n# Show hooks system")
        print("python sdk_agent_demo.py --hooks")
        print("\n# Run interactive mode")
        print("python sdk_agent_demo.py --interactive")
        print("\n# Analyze a project")
        print("python sdk_agent_demo.py --batch src/main/java")
        print("\n# Run all demos")
        print("python sdk_agent_demo.py --all")
        print("")
        return

    # Run selected demos
    if args.tools:
        asyncio.run(demo_tools_showcase())

    if args.hooks:
        asyncio.run(demo_hooks_system())

    if args.interactive:
        asyncio.run(demo_interactive())

    if args.batch:
        asyncio.run(demo_batch_analysis(args.batch))

    if args.custom:
        asyncio.run(demo_custom_workflow())

    if args.all:
        asyncio.run(demo_tools_showcase())
        asyncio.run(demo_hooks_system())
        # Skip interactive mode in --all
        print("\n(Skipping interactive mode in --all. Use --interactive to try it)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
