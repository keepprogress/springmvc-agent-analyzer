"""
SDK Agent Utility Functions.

Common utility functions for SDK Agent mode.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def expand_file_path(
    file_path: str,
    project_root: Optional[str] = None
) -> str:
    """
    Expand and normalize file path.

    Args:
        file_path: File path (relative or absolute)
        project_root: Project root directory (optional)

    Returns:
        Absolute normalized path
    """
    path = Path(file_path)

    if not path.is_absolute() and project_root:
        path = Path(project_root) / path

    return str(path.resolve())


def detect_file_type(file_path: str) -> str:
    """
    Detect file type based on extension and content.

    Args:
        file_path: Path to file

    Returns:
        File type: 'controller', 'service', 'mapper', 'jsp', 'procedure', 'unknown'
    """
    path = Path(file_path)

    # Check extension
    if path.suffix == '.jsp':
        return 'jsp'
    elif path.suffix == '.xml':
        # Could be MyBatis mapper
        if 'mapper' in path.name.lower():
            return 'mapper'
        return 'unknown'
    elif path.suffix == '.sql':
        return 'procedure'
    elif path.suffix == '.java':
        # Check file name patterns
        name_lower = path.stem.lower()
        if 'controller' in name_lower:
            return 'controller'
        elif 'service' in name_lower:
            return 'service'
        elif 'mapper' in name_lower or 'dao' in name_lower:
            return 'mapper'

        # Check file content (first few lines)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(1000)  # First 1000 chars
                if '@Controller' in content or '@RestController' in content:
                    return 'controller'
                elif '@Service' in content:
                    return 'service'
                elif '@Mapper' in content or '@Repository' in content:
                    return 'mapper'
        except Exception as e:
            logger.warning(f"Failed to read file {file_path}: {e}")

    return 'unknown'


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
    if format_type == "json":
        import json
        text = json.dumps(data, indent=2, ensure_ascii=False)
    elif format_type == "markdown":
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
    min_threshold: float = 0.7
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
    Load system prompt from file.

    Args:
        prompt_path: Path to prompt file

    Returns:
        System prompt content
    """
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()
