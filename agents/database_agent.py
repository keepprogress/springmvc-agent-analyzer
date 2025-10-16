"""
Database Analysis Agent.

This agent connects to the project's database to extract schema information,
table metadata, and other database-level details to generate a data dictionary.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List

# This is a conceptual import for a database connector.
# In a real project, this would be a library like 'oracledb' or 'sqlalchemy'.
from core.db_connector import DatabaseConnector
from sdk_agent.exceptions import ConfigurationError


class DatabaseAgent:
    """
    Agent responsible for database schema analysis.
    """

    def __init__(self, config_path: str = "config/oracle_config.yaml"):
        """
        Initializes the DatabaseAgent.

        Args:
            config_path: Path to the Oracle database configuration file.
        """
        self.config = self._load_db_config(config_path)
        # The connector would be initialized with self.config
        self.db_connector = DatabaseConnector(self.config)

    def _load_db_config(self, config_path: str) -> Dict[str, Any]:
        """Loads the database configuration file."""
        path = Path(config_path)
        if not path.exists():
            raise ConfigurationError(
                f"Database configuration file not found at: {config_path}. "
                "Please create it from the 'oracle_config.example.yaml'."
            )
        with open(path, "r") as f:
            return yaml.safe_load(f)

    async def generate_data_dictionary(
        self, tables: List[str] = None, output_format: str = "markdown"
    ) -> str:
        """
        Connects to the database and generates a data dictionary.

        Args:
            tables: An optional list of specific tables to document.
                    If None, all tables will be documented.
            output_format: The desired output format ('markdown' or 'json').

        Returns:
            A string containing the data dictionary in the specified format.
        """
        print(f"Connecting to database to generate data dictionary...")
        await self.db_connector.connect()

        if not tables:
            tables = await self.db_connector.get_all_tables()

        dictionary_entries = []
        for table_name in tables:
            columns = await self.db_connector.get_table_columns(table_name)
            dictionary_entries.append({"table": table_name, "columns": columns})

        await self.db_connector.disconnect()

        if output_format == "json":
            import json
            return json.dumps(dictionary_entries, indent=2)
        else:
            return self._format_as_markdown(dictionary_entries)

    def _format_as_markdown(self, entries: List[Dict[str, Any]]) -> str:
        """Formats the data dictionary as Markdown."""
        md_lines = ["# Data Dictionary\n"]
        for entry in entries:
            table_name = entry["table"]
            columns = entry["columns"]
            md_lines.append(f"## Table: `{table_name}`\n")
            md_lines.append("| Column Name | Data Type | Nullable | Comment |")
            md_lines.append("|-------------|-----------|----------|---------|")
            for col in columns:
                md_lines.append(
                    f"| `{col['name']}` "
                    f"| {col['type']} "
                    f"| {'Yes' if col['nullable'] else 'No'} "
                    f"| {col.get('comment', '')} |"
                )
            md_lines.append("\n")
        return "\n".join(md_lines)