"""
SDK Agent Utility Functions.

Common utility functions for SDK Agent mode.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

from sdk_agent.exceptions import SDKAgentError
from sdk_agent.constants import (
    FILE_DETECTION_BUFFER_SIZE,
    FILE_DETECTION_MAX_LINES,
    FILE_TYPE_CONTROLLER,
    FILE_TYPE_SERVICE,
    FILE_TYPE_MAPPER,
    FILE_TYPE_JSP,
    FILE_TYPE_PROCEDURE,
    FILE_TYPE_UNKNOWN,
    FILE_EXT_JSP,
    FILE_EXT_XML,
    FILE_EXT_SQL,
    FILE_EXT_JAVA,
    MIN_CONFIDENCE_THRESHOLD,
    OUTPUT_FORMAT_JSON,
    OUTPUT_FORMAT_MARKDOWN,
)

logger = logging.getLogger(__name__)

# System prompt cache
_PROMPT_CACHE: Dict[str, str] = {}


def expand_file_path(
    file_path: str,
    project_root: Optional[str] = None
) -> str:
    """
    Expand and normalize file path with security validation.

    Prevents path traversal attacks by ensuring the resolved path
    is within the project root.

    Args:
        file_path: File path (relative or absolute)
        project_root: Project root directory (optional)

    Returns:
        Absolute normalized path

    Raises:
        SDKAgentError: If path is outside project root
    """
    path = Path(file_path)

    if not path.is_absolute() and project_root:
        path = Path(project_root) / path

    resolved = path.resolve()

    # Security: ensure path is within project_root
    if project_root:
        root = Path(project_root).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            raise SDKAgentError(
                f"Security error: Path {resolved} is outside project root {root}"
            )

    return str(resolved)


def detect_file_type(file_path: str) -> str:
    """
    Detect file type based on extension and content.

    Uses a more robust approach that checks file extension first,
    then file name patterns, then content for Java files.

    Args:
        file_path: Path to file

    Returns:
        File type: 'controller', 'service', 'mapper', 'jsp', 'procedure', 'unknown'
    """
    path = Path(file_path)

    # Check extension
    if path.suffix == FILE_EXT_JSP:
        return FILE_TYPE_JSP
    elif path.suffix == FILE_EXT_XML:
        # Could be MyBatis mapper
        if "mapper" in path.name.lower():
            return FILE_TYPE_MAPPER
        return FILE_TYPE_UNKNOWN
    elif path.suffix == FILE_EXT_SQL:
        return FILE_TYPE_PROCEDURE
    elif path.suffix == FILE_EXT_JAVA:
        # Check file name patterns
        name_lower = path.stem.lower()
        if "controller" in name_lower:
            return FILE_TYPE_CONTROLLER
        elif "service" in name_lower:
            return FILE_TYPE_SERVICE
        elif "mapper" in name_lower or "dao" in name_lower:
            return FILE_TYPE_MAPPER

        # Check file content - read strategically
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                # Read first N lines instead of fixed buffer
                lines = []
                for i, line in enumerate(f):
                    if i >= FILE_DETECTION_MAX_LINES:
                        break
                    lines.append(line)

                content = "".join(lines)

                # Check for annotations
                if "@Controller" in content or "@RestController" in content:
                    return FILE_TYPE_CONTROLLER
                elif "@Service" in content:
                    return FILE_TYPE_SERVICE
                elif "@Mapper" in content or "@Repository" in content:
                    return FILE_TYPE_MAPPER

        except Exception as e:
            logger.warning(f"Failed to read file {file_path}: {e}")

    return FILE_TYPE_UNKNOWN


def format_tool_result(
    data: Dict[str, Any],
    format_type: str = "text"
) -> Dict[str, Any]:
    """
    Format tool result for SDK Agent response.

    Args:
        data: Analysis result data
        format_type: Format type ('text', 'json', 'markdown')

    Returns:
        Formatted result with 'content' field for SDK
    """
    if format_type == OUTPUT_FORMAT_JSON:
        text = json.dumps(data, indent=2, ensure_ascii=False)
    elif format_type == OUTPUT_FORMAT_MARKDOWN:
        text = dict_to_markdown(data)
    else:
        text = str(data)

    return {
        "content": [{"type": "text", "text": text}],
        "data": data  # Keep raw data for further processing
    }


def dict_to_markdown(data: Dict[str, Any], indent: int = 0) -> str:
    """
    Convert dictionary to markdown format.

    Args:
        data: Dictionary data
        indent: Indentation level

    Returns:
        Markdown formatted string
    """
    lines = []
    prefix = "  " * indent

    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}- **{key}**:")
            lines.append(dict_to_markdown(value, indent + 1))
        elif isinstance(value, list):
            lines.append(f"{prefix}- **{key}**:")
            for item in value:
                if isinstance(item, dict):
                    lines.append(dict_to_markdown(item, indent + 1))
                else:
                    lines.append(f"{prefix}  - {item}")
        else:
            lines.append(f"{prefix}- **{key}**: {value}")

    return "\n".join(lines)


def validate_confidence(
    confidence: float,
    min_threshold: float = MIN_CONFIDENCE_THRESHOLD
) -> bool:
    """
    Validate confidence score.

    Args:
        confidence: Confidence score (0.0-1.0)
        min_threshold: Minimum acceptable threshold

    Returns:
        True if confidence meets threshold
    """
    return confidence >= min_threshold


def get_file_list(
    directory: str,
    pattern: str = "**/*.java",
    exclude: Optional[List[str]] = None
) -> List[str]:
    """
    Get list of files matching pattern.

    Args:
        directory: Directory to search
        pattern: Glob pattern
        exclude: Patterns to exclude

    Returns:
        List of file paths
    """
    from pathlib import Path

    dir_path = Path(directory)
    files = []

    for file_path in dir_path.glob(pattern):
        if file_path.is_file():
            # Check exclusions
            if exclude:
                excluded = False
                for exc_pattern in exclude:
                    if file_path.match(exc_pattern):
                        excluded = True
                        break
                if excluded:
                    continue

            files.append(str(file_path))

    return sorted(files)


def ensure_directory(directory: str) -> None:
    """
    Ensure directory exists, create if not.

    Args:
        directory: Directory path
    """
    Path(directory).mkdir(parents=True, exist_ok=True)


def load_system_prompt(prompt_path: str) -> str:
    """
    Load system prompt from file with caching.

    Uses a module-level cache to avoid re-reading the same prompt file.
    This is safe as prompts typically don't change during runtime.

    Args:
        prompt_path: Path to prompt file

    Returns:
        System prompt content
    """
    # Check cache first
    if prompt_path in _PROMPT_CACHE:
        logger.debug(f"Using cached prompt: {prompt_path}")
        return _PROMPT_CACHE[prompt_path]

    # Load from file
    logger.debug(f"Loading prompt from file: {prompt_path}")
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt = f.read()

    # Cache for future use
    _PROMPT_CACHE[prompt_path] = prompt

    return prompt
