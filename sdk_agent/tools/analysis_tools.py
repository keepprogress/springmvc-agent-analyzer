"""
Analysis Tools for SDK Agent Mode.

This module implements tools for analyzing Spring MVC application components.
Each tool wraps an existing agent and formats the output for SDK consumption.

Tools:
- analyze_controller: Analyze Spring Controller files
- analyze_jsp: Analyze JSP view files
- analyze_service: Analyze Service layer files
- analyze_mapper: Analyze MyBatis Mapper files
- analyze_procedure: Analyze Oracle stored procedures
- analyze_directory: Batch analyze files in a directory

Note: @tool decorators will be added in Phase 5 when SDK is integrated.
For now, these are regular async functions with proper structure.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
import glob

from sdk_agent.agent_factory import get_agent
from sdk_agent.utils import (
    expand_file_path,
    detect_file_type,
    format_tool_result,
    validate_confidence
)
from sdk_agent.constants import (
    FILE_TYPE_CONTROLLER,
    FILE_TYPE_SERVICE,
    FILE_TYPE_JSP,
    FILE_TYPE_MAPPER,
    FILE_TYPE_PROCEDURE,
    MIN_CONFIDENCE_THRESHOLD
)
from sdk_agent.exceptions import SDKAgentError

logger = logging.getLogger("sdk_agent.tools.analysis")


# Tool metadata (will be used by @tool decorator in Phase 5)
ANALYZE_CONTROLLER_META = {
    "name": "analyze_controller",
    "description": (
        "Analyze Spring MVC Controller file to extract:\n"
        "- Request mappings (@RequestMapping, @GetMapping, @PostMapping, etc.)\n"
        "- Service dependencies (@Autowired, @Resource, Constructor injection)\n"
        "- Method signatures, parameters, and return types\n"
        "- HTTP endpoints and URL patterns\n"
        "- Controller-level and method-level annotations"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the Controller .java file"
            },
            "include_details": {
                "type": "boolean",
                "description": "Include detailed method information (default: true)",
                "default": True
            },
            "project_root": {
                "type": "string",
                "description": "Project root directory for relative path resolution",
                "default": None
            }
        },
        "required": ["file_path"]
    }
}


async def analyze_controller(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze Spring MVC Controller file.

    Args:
        args: Dictionary with keys:
            - file_path (str): Path to Controller file
            - include_details (bool): Include method details (default: True)
            - project_root (str, optional): Project root directory

    Returns:
        Dict with structure:
        {
            "content": [{"type": "text", "text": "..."}],
            "data": {...},  # Full analysis data
            "is_error": False
        }

    Raises:
        SDKAgentError: If file not found or analysis fails
    """
    file_path = args["file_path"]
    include_details = args.get("include_details", True)
    project_root = args.get("project_root")

    logger.info(f"Analyzing controller: {file_path}")

    try:
        # Expand and validate path
        full_path = expand_file_path(file_path, project_root)

        # Verify file exists
        if not Path(full_path).exists():
            return format_tool_result(
                {"error": f"File not found: {full_path}"},
                format_type="json",
                is_error=True
            )

        # Get controller agent
        agent = get_agent("controller")

        # Analyze file
        result = await agent.analyze(full_path)

        # Validate confidence
        confidence = result.get("confidence", 0.0)
        if not validate_confidence(confidence):
            logger.warning(
                f"Low confidence for {file_path}: {confidence:.2%} "
                f"(threshold: {MIN_CONFIDENCE_THRESHOLD:.2%})"
            )

        # Format output
        analysis = result.get("analysis", {})
        summary_lines = [
            f"Controller Analysis: {analysis.get('class_name', 'Unknown')}",
            "=" * 60,
            f"Package: {analysis.get('package', 'N/A')}",
            f"Base URL: {analysis.get('base_url', 'N/A')}",
            f"Methods: {len(analysis.get('methods', []))}",
            f"Dependencies: {len(analysis.get('dependencies', []))}",
            "",
            f"Confidence: {confidence:.2%}",
            f"Model Used: {result.get('model_used', 'N/A')}",
            f"Cost: ${result.get('cost', 0.0):.4f}"
        ]

        if include_details and analysis.get('methods'):
            summary_lines.append("")
            summary_lines.append("Methods:")
            for method in analysis['methods']:
                method_name = method.get('name', 'unknown')
                http_method = method.get('http_method', 'GET')
                url = method.get('url', 'N/A')
                summary_lines.append(f"  - [{http_method}] {method_name}() → {url}")

        if analysis.get('dependencies'):
            summary_lines.append("")
            summary_lines.append("Dependencies:")
            for dep in analysis['dependencies']:
                dep_type = dep.get('type', 'Unknown')
                dep_name = dep.get('name', 'unknown')
                summary_lines.append(f"  - {dep_type}: {dep_name}")

        summary = "\n".join(summary_lines)

        return {
            "content": [{"type": "text", "text": summary}],
            "data": result,  # Full analysis data
            "is_error": False
        }

    except Exception as e:
        logger.error(f"Error analyzing controller {file_path}: {e}", exc_info=True)
        return format_tool_result(
            {"error": str(e), "file_path": file_path},
            format_type="json",
            is_error=True
        )


ANALYZE_JSP_META = {
    "name": "analyze_jsp",
    "description": (
        "Analyze JSP (JavaServer Pages) view file to extract:\n"
        "- Form fields and input elements\n"
        "- Model attributes referenced in the view\n"
        "- Included JSP fragments and taglibs\n"
        "- JavaScript dependencies and AJAX calls\n"
        "- Links to Controller actions"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the JSP file"
            },
            "project_root": {
                "type": "string",
                "description": "Project root directory",
                "default": None
            }
        },
        "required": ["file_path"]
    }
}


async def analyze_jsp(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze JSP view file.

    Args:
        args: Dictionary with keys:
            - file_path (str): Path to JSP file
            - project_root (str, optional): Project root directory

    Returns:
        Dict with analysis results
    """
    file_path = args["file_path"]
    project_root = args.get("project_root")

    logger.info(f"Analyzing JSP: {file_path}")

    try:
        full_path = expand_file_path(file_path, project_root)

        if not Path(full_path).exists():
            return format_tool_result(
                {"error": f"File not found: {full_path}"},
                format_type="json",
                is_error=True
            )

        agent = get_agent("jsp")
        result = await agent.analyze(full_path)

        analysis = result.get("analysis", {})
        summary_lines = [
            f"JSP Analysis: {Path(file_path).name}",
            "=" * 60,
            f"Form Fields: {len(analysis.get('form_fields', []))}",
            f"Model Attributes: {len(analysis.get('model_attributes', []))}",
            f"Includes: {len(analysis.get('includes', []))}",
            f"AJAX Calls: {len(analysis.get('ajax_calls', []))}",
            "",
            f"Confidence: {result.get('confidence', 0.0):.2%}",
            f"Cost: ${result.get('cost', 0.0):.4f}"
        ]

        if analysis.get('form_fields'):
            summary_lines.append("")
            summary_lines.append("Form Fields:")
            for field in analysis['form_fields'][:10]:  # Limit to 10
                field_name = field.get('name', 'unknown')
                field_type = field.get('type', 'unknown')
                summary_lines.append(f"  - {field_name} ({field_type})")

        summary = "\n".join(summary_lines)

        return {
            "content": [{"type": "text", "text": summary}],
            "data": result,
            "is_error": False
        }

    except Exception as e:
        logger.error(f"Error analyzing JSP {file_path}: {e}", exc_info=True)
        return format_tool_result(
            {"error": str(e), "file_path": file_path},
            format_type="json",
            is_error=True
        )


ANALYZE_SERVICE_META = {
    "name": "analyze_service",
    "description": (
        "Analyze Spring Service layer file to extract:\n"
        "- Service class name and package\n"
        "- Public methods and business logic\n"
        "- DAO/Repository dependencies\n"
        "- Transaction annotations (@Transactional)\n"
        "- Exception handling patterns"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the Service .java file"
            },
            "project_root": {
                "type": "string",
                "description": "Project root directory",
                "default": None
            }
        },
        "required": ["file_path"]
    }
}


async def analyze_service(args: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze Spring Service file."""
    file_path = args["file_path"]
    project_root = args.get("project_root")

    logger.info(f"Analyzing service: {file_path}")

    try:
        full_path = expand_file_path(file_path, project_root)

        if not Path(full_path).exists():
            return format_tool_result(
                {"error": f"File not found: {full_path}"},
                format_type="json",
                is_error=True
            )

        agent = get_agent("service")
        result = await agent.analyze(full_path)

        analysis = result.get("analysis", {})
        summary_lines = [
            f"Service Analysis: {analysis.get('class_name', 'Unknown')}",
            "=" * 60,
            f"Package: {analysis.get('package', 'N/A')}",
            f"Methods: {len(analysis.get('methods', []))}",
            f"Dependencies: {len(analysis.get('dependencies', []))}",
            "",
            f"Confidence: {result.get('confidence', 0.0):.2%}",
            f"Cost: ${result.get('cost', 0.0):.4f}"
        ]

        summary = "\n".join(summary_lines)

        return {
            "content": [{"type": "text", "text": summary}],
            "data": result,
            "is_error": False
        }

    except Exception as e:
        logger.error(f"Error analyzing service {file_path}: {e}", exc_info=True)
        return format_tool_result(
            {"error": str(e), "file_path": file_path},
            format_type="json",
            is_error=True
        )


ANALYZE_MAPPER_META = {
    "name": "analyze_mapper",
    "description": (
        "Analyze MyBatis Mapper file (XML or Java interface) to extract:\n"
        "- SQL statements (SELECT, INSERT, UPDATE, DELETE)\n"
        "- Result maps and parameter types\n"
        "- Database tables referenced\n"
        "- Dynamic SQL conditions"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to Mapper file (.xml or .java)"
            },
            "project_root": {
                "type": "string",
                "description": "Project root directory",
                "default": None
            }
        },
        "required": ["file_path"]
    }
}


async def analyze_mapper(args: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze MyBatis Mapper file."""
    file_path = args["file_path"]
    project_root = args.get("project_root")

    logger.info(f"Analyzing mapper: {file_path}")

    try:
        full_path = expand_file_path(file_path, project_root)

        if not Path(full_path).exists():
            return format_tool_result(
                {"error": f"File not found: {full_path}"},
                format_type="json",
                is_error=True
            )

        agent = get_agent("mapper")
        result = await agent.analyze(full_path)

        analysis = result.get("analysis", {})
        summary_lines = [
            f"Mapper Analysis: {analysis.get('namespace', 'Unknown')}",
            "=" * 60,
            f"SQL Statements: {len(analysis.get('statements', []))}",
            f"Tables: {len(analysis.get('tables', []))}",
            "",
            f"Confidence: {result.get('confidence', 0.0):.2%}",
            f"Cost: ${result.get('cost', 0.0):.4f}"
        ]

        summary = "\n".join(summary_lines)

        return {
            "content": [{"type": "text", "text": summary}],
            "data": result,
            "is_error": False
        }

    except Exception as e:
        logger.error(f"Error analyzing mapper {file_path}: {e}", exc_info=True)
        return format_tool_result(
            {"error": str(e), "file_path": file_path},
            format_type="json",
            is_error=True
        )


ANALYZE_PROCEDURE_META = {
    "name": "analyze_procedure",
    "description": (
        "Analyze Oracle stored procedure file to extract:\n"
        "- Procedure name and parameters (IN, OUT, IN OUT)\n"
        "- SQL operations performed\n"
        "- Tables and views accessed\n"
        "- Business logic description"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to procedure file (.sql or .pls)"
            },
            "project_root": {
                "type": "string",
                "description": "Project root directory",
                "default": None
            }
        },
        "required": ["file_path"]
    }
}


async def analyze_procedure(args: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze Oracle stored procedure."""
    file_path = args["file_path"]
    project_root = args.get("project_root")

    logger.info(f"Analyzing procedure: {file_path}")

    try:
        full_path = expand_file_path(file_path, project_root)

        if not Path(full_path).exists():
            return format_tool_result(
                {"error": f"File not found: {full_path}"},
                format_type="json",
                is_error=True
            )

        agent = get_agent("procedure")
        result = await agent.analyze(full_path)

        analysis = result.get("analysis", {})
        summary_lines = [
            f"Procedure Analysis: {analysis.get('name', 'Unknown')}",
            "=" * 60,
            f"Parameters: {len(analysis.get('parameters', []))}",
            f"Tables: {len(analysis.get('tables', []))}",
            "",
            f"Confidence: {result.get('confidence', 0.0):.2%}",
            f"Cost: ${result.get('cost', 0.0):.4f}"
        ]

        summary = "\n".join(summary_lines)

        return {
            "content": [{"type": "text", "text": summary}],
            "data": result,
            "is_error": False
        }

    except Exception as e:
        logger.error(f"Error analyzing procedure {file_path}: {e}", exc_info=True)
        return format_tool_result(
            {"error": str(e), "file_path": file_path},
            format_type="json",
            is_error=True
        )


ANALYZE_DIRECTORY_META = {
    "name": "analyze_directory",
    "description": (
        "Batch analyze all files in a directory matching a pattern.\n"
        "Automatically detects file types and uses appropriate agents.\n"
        "Useful for analyzing entire packages or project directories."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "directory_path": {
                "type": "string",
                "description": "Path to directory to analyze"
            },
            "pattern": {
                "type": "string",
                "description": "File pattern to match (e.g., '*.java', '**/*.jsp')",
                "default": "**/*.java"
            },
            "recursive": {
                "type": "boolean",
                "description": "Recursively search subdirectories",
                "default": True
            },
            "max_files": {
                "type": "integer",
                "description": "Maximum number of files to analyze",
                "default": 50
            },
            "project_root": {
                "type": "string",
                "description": "Project root directory",
                "default": None
            }
        },
        "required": ["directory_path"]
    }
}


async def analyze_directory(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Batch analyze directory.

    Args:
        args: Dictionary with keys:
            - directory_path (str): Directory to analyze
            - pattern (str): File pattern (default: "**/*.java")
            - recursive (bool): Recursive search (default: True)
            - max_files (int): Max files to analyze (default: 50)
            - project_root (str, optional): Project root

    Returns:
        Dict with batch analysis results
    """
    directory_path = args["directory_path"]
    pattern = args.get("pattern", "**/*.java")
    recursive = args.get("recursive", True)
    max_files = args.get("max_files", 50)
    project_root = args.get("project_root")

    logger.info(f"Analyzing directory: {directory_path} (pattern: {pattern})")

    try:
        full_path = expand_file_path(directory_path, project_root)
        dir_obj = Path(full_path)

        if not dir_obj.exists():
            return format_tool_result(
                {"error": f"Directory not found: {full_path}"},
                format_type="json",
                is_error=True
            )

        if not dir_obj.is_dir():
            return format_tool_result(
                {"error": f"Not a directory: {full_path}"},
                format_type="json",
                is_error=True
            )

        # Find files matching pattern
        if recursive:
            files = list(dir_obj.glob(pattern))
        else:
            files = list(dir_obj.glob(pattern.lstrip("**/")))

        # Limit number of files
        if len(files) > max_files:
            logger.warning(f"Found {len(files)} files, limiting to {max_files}")
            files = files[:max_files]

        # Analyze each file
        results = []
        errors = []

        for file_path in files:
            try:
                # Detect file type
                file_type = detect_file_type(str(file_path))

                # Skip unknown types
                if file_type == "unknown":
                    continue

                # Map file type to analysis function
                type_to_func = {
                    FILE_TYPE_CONTROLLER: analyze_controller,
                    FILE_TYPE_SERVICE: analyze_service,
                    FILE_TYPE_JSP: analyze_jsp,
                    FILE_TYPE_MAPPER: analyze_mapper,
                    FILE_TYPE_PROCEDURE: analyze_procedure
                }

                if file_type in type_to_func:
                    func = type_to_func[file_type]
                    result = await func({"file_path": str(file_path)})

                    if not result.get("is_error"):
                        results.append({
                            "file": str(file_path.relative_to(dir_obj)),
                            "type": file_type,
                            "data": result.get("data", {})
                        })
                    else:
                        errors.append({
                            "file": str(file_path.relative_to(dir_obj)),
                            "error": result.get("data", {}).get("error", "Unknown error")
                        })

            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")
                errors.append({
                    "file": str(file_path.relative_to(dir_obj)),
                    "error": str(e)
                })

        # Format summary
        summary_lines = [
            f"Directory Analysis: {directory_path}",
            "=" * 60,
            f"Files Analyzed: {len(results)}",
            f"Errors: {len(errors)}",
            f"Pattern: {pattern}",
            ""
        ]

        if results:
            summary_lines.append("Successfully Analyzed:")
            for r in results[:10]:  # Show first 10
                summary_lines.append(f"  - {r['file']} ({r['type']})")

        if errors:
            summary_lines.append("")
            summary_lines.append("Errors:")
            for e in errors[:10]:  # Show first 10
                summary_lines.append(f"  - {e['file']}: {e['error']}")

        summary = "\n".join(summary_lines)

        return {
            "content": [{"type": "text", "text": summary}],
            "data": {
                "results": results,
                "errors": errors,
                "total_files": len(files),
                "analyzed": len(results),
                "failed": len(errors)
            },
            "is_error": False
        }

    except Exception as e:
        logger.error(f"Error analyzing directory {directory_path}: {e}", exc_info=True)
        return format_tool_result(
            {"error": str(e), "directory_path": directory_path},
            format_type="json",
            is_error=True
        )


# Export all tools and metadata
ALL_TOOLS = [
    analyze_controller,
    analyze_jsp,
    analyze_service,
    analyze_mapper,
    analyze_procedure,
    analyze_directory
]

ALL_TOOL_META = [
    ANALYZE_CONTROLLER_META,
    ANALYZE_JSP_META,
    ANALYZE_SERVICE_META,
    ANALYZE_MAPPER_META,
    ANALYZE_PROCEDURE_META,
    ANALYZE_DIRECTORY_META
]
