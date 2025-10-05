"""
SDK Agent Hooks Module.

This module contains hooks for pre/post processing in SDK Agent mode.
Hooks enable automatic validation, caching, context management, and cleanup.

Available Hooks:
- ValidationHook (PreToolUse): Validate inputs and auto-upgrade models
- CacheHook (PostToolUse): Cache analysis results
- ContextManagerHook (PreCompact): Smart context compression
- InputEnhancementHook (UserPromptSubmit): Expand paths and add context
- CleanupHook (Stop): Session cleanup and summary

Hook Types (from Claude Agent SDK):
- PreToolUse: Before tool execution
- PostToolUse: After tool execution
- UserPromptSubmit: When user submits a prompt
- Stop: When agent stops
- PreCompact: Before context compression
"""

from sdk_agent.hooks.validation import ValidationHook
from sdk_agent.hooks.cache import CacheHook
from sdk_agent.hooks.context_manager import ContextManagerHook
from sdk_agent.hooks.input_enhancement import InputEnhancementHook
from sdk_agent.hooks.cleanup import CleanupHook

__all__ = [
    "ValidationHook",
    "CacheHook",
    "ContextManagerHook",
    "InputEnhancementHook",
    "CleanupHook",
]
