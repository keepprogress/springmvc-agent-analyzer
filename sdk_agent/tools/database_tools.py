"""
Database Tools for SDK Agent Mode.

This module provides tools for interacting with the database,
such as generating a data dictionary.
"""

import logging
from typing import Dict, Any, List, Optional

from agents.database_agent import DatabaseAgent
from sdk_agent.utils import format_tool_result

logger = logging.getLogger("sdk_agent.tools.database")

GENERATE_DATA_DICTIONARY_META = {
    "name": "generate_data_dictionary",
    "description": (
        "Connects to the database and generates a data dictionary for specified tables, or all tables if none are provided. "
        "The dictionary includes table names, column names, data types, and comments."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "tables": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional list of table names to document. If empty, all tables will be included.",
                "default": None,
            },
            "output_format": {
                "type": "string",
                "description": "The output format for the dictionary ('markdown' or 'json').",
                "default": "markdown",
            },
            "config_path": {
                "type": "string",
                "description": "Path to the database configuration file.",
                "default": "config/oracle_config.yaml",
            },
        },
    },
}


async def generate_data_dictionary(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool to generate a data dictionary from the database schema.

    Args:
        args: Dictionary with keys:
            - tables (List[str], optional): Specific tables to document.
            - output_format (str): 'markdown' or 'json'.
            - config_path (str): Path to the database config.

    Returns:
        A dictionary with the data dictionary content.
    """
    tables: Optional[List[str]] = args.get("tables")
    output_format: str = args.get("output_format", "markdown")
    config_path: str = args.get("config_path", "config/oracle_config.yaml")

    logger.info(f"Generating data dictionary. Tables: {tables or 'all'}. Format: {output_format}.")

    try:
        # Instantiate the database agent
        agent = DatabaseAgent(config_path=config_path)

        # Generate the dictionary
        dictionary_content = await agent.generate_data_dictionary(
            tables=tables, output_format=output_format
        )

        return {
            "content": [{"type": "text", "text": dictionary_content}],
            "data": {
                "message": "Data dictionary generated successfully.",
                "format": output_format,
                "tables_documented": tables or "all",
            },
            "is_error": False,
        }

    except Exception as e:
        logger.error(f"Error generating data dictionary: {e}", exc_info=True)
        return format_tool_result(
            {"error": str(e)},
            format_type="json",
            is_error=True
        )