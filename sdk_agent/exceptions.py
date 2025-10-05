"""
SDK Agent Exceptions.

Custom exception hierarchy for SDK Agent mode.
"""


class SDKAgentError(Exception):
    """Base exception for SDK Agent errors."""
    pass


class ConfigurationError(SDKAgentError):
    """Configuration-related errors."""
    pass


class ToolExecutionError(SDKAgentError):
    """Tool execution errors."""
    pass


class HookError(SDKAgentError):
    """Hook execution errors."""
    pass


class PermissionDeniedError(SDKAgentError):
    """Permission denied for tool usage."""
    pass


class ValidationError(SDKAgentError):
    """Validation errors (confidence too low, invalid input, etc.)."""
    pass


class GraphError(SDKAgentError):
    """Knowledge graph operation errors."""
    pass


class AgentNotInitializedError(SDKAgentError):
    """Agent not properly initialized."""
    pass
