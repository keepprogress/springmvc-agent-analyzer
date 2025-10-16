"""
Configuration Analysis Tools for SDK Agent Mode.

This module provides tools for parsing and analyzing configuration files,
such as Spring XML and .properties files.
"""

import logging
from typing import Dict, Any

from agents.config_agent import ConfigAgent
from sdk_agent.utils import format_tool_result, expand_file_path

logger = logging.getLogger("sdk_agent.tools.config")

ANALYZE_SPRING_XML_META = {
    "name": "analyze_spring_xml",
    "description": "Parses a Spring XML configuration file to extract bean definitions, dependencies, and imports.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The path to the Spring XML configuration file (e.g., applicationContext.xml)."
            },
            "project_root": {
                "type": "string",
                "description": "Project root directory for context.",
                "default": None
            }
        },
        "required": ["file_path"],
    },
}

async def analyze_spring_xml(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool to analyze a Spring XML configuration file.

    Args:
        args: Dictionary with keys:
            - file_path (str): The path to the XML file.
            - project_root (str, optional): The project root directory.

    Returns:
        A dictionary with the analysis results.
    """
    file_path = args["file_path"]
    project_root = args.get("project_root")
    logger.info(f"Analyzing Spring XML: {file_path}")

    try:
        full_path = expand_file_path(file_path, project_root)
        agent = ConfigAgent()
        result = await agent.analyze_spring_xml(full_path)

        summary_lines = [
            f"Spring XML Analysis: {file_path}",
            "=" * 60,
            f"Total Beans Defined: {result.get('total_beans', 0)}",
            f"Imported Resources: {len(result.get('imported_resources', []))}",
        ]
        summary = "\n".join(summary_lines)

        return {
            "content": [{"type": "text", "text": summary}],
            "data": result,
            "is_error": False,
        }

    except Exception as e:
        logger.error(f"Error analyzing Spring XML {file_path}: {e}", exc_info=True)
        return format_tool_result({"error": str(e)}, is_error=True)


ANALYZE_PROPERTIES_FILE_META = {
    "name": "analyze_properties_file",
    "description": "Parses a .properties file to extract all key-value pairs.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The path to the .properties file."
            },
            "project_root": {
                "type": "string",
                "description": "Project root directory for context.",
                "default": None
            }
        },
        "required": ["file_path"],
    },
}

async def analyze_properties_file(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool to analyze a .properties file.

    Args:
        args: Dictionary with keys:
            - file_path (str): The path to the properties file.
            - project_root (str, optional): The project root directory.

    Returns:
        A dictionary with the analysis results.
    """
    file_path = args["file_path"]
    project_root = args.get("project_root")
    logger.info(f"Analyzing properties file: {file_path}")

    try:
        full_path = expand_file_path(file_path, project_root)
        agent = ConfigAgent()
        result = await agent.analyze_properties_file(full_path)

        summary_lines = [
            f"Properties File Analysis: {file_path}",
            "=" * 60,
            f"Total Properties Found: {result.get('total_properties', 0)}",
        ]
        summary = "\n".join(summary_lines)

        return {
            "content": [{"type": "text", "text": summary}],
            "data": result,
            "is_error": False,
        }

    except Exception as e:
        logger.error(f"Error analyzing properties file {file_path}: {e}", exc_info=True)
        return format_tool_result({"error": str(e)}, is_error=True)