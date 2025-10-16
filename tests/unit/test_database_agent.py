"""
Unit tests for the DatabaseAgent.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from agents.database_agent import DatabaseAgent

@pytest.fixture
def mock_db_connector():
    """Provides a mock database connector."""
    connector = MagicMock()
    connector.connect = AsyncMock()
    connector.disconnect = AsyncMock()
    connector.get_all_tables = AsyncMock(return_value=["USERS", "ORDERS"])
    connector.get_table_columns = AsyncMock(return_value=[
        {"name": "ID", "type": "NUMBER", "nullable": False},
        {"name": "NAME", "type": "VARCHAR2", "nullable": True},
    ])
    return connector

@patch('agents.database_agent.DatabaseConnector')
@patch('pathlib.Path.exists', return_value=True)
def test_database_agent_initialization(mock_exists, mock_connector_class, mock_db_connector):
    """Tests that the DatabaseAgent can be initialized."""
    mock_connector_class.return_value = mock_db_connector
    with patch('builtins.open', new_callable=MagicMock) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = "key: value"
        with patch('yaml.safe_load', return_value={}) as mock_yaml:
            agent = DatabaseAgent()
            assert agent is not None
            assert agent.db_connector is not None

@pytest.mark.asyncio
@patch('agents.database_agent.DatabaseConnector')
@patch('pathlib.Path.exists', return_value=True)
async def test_generate_data_dictionary_markdown(mock_exists, mock_connector_class, mock_db_connector):
    """Tests that a Markdown data dictionary can be generated."""
    mock_connector_class.return_value = mock_db_connector
    with patch('builtins.open', new_callable=MagicMock) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = "key: value"
        with patch('yaml.safe_load', return_value={}) as mock_yaml:
            agent = DatabaseAgent()
            result = await agent.generate_data_dictionary()

            assert "## Table: `USERS`" in result
            assert "| Column Name | Data Type |" in result
            assert "| `ID` | NUMBER |" in result

@pytest.mark.asyncio
@patch('agents.database_agent.DatabaseConnector')
@patch('pathlib.Path.exists', return_value=True)
async def test_generate_data_dictionary_json(mock_exists, mock_connector_class, mock_db_connector):
    """Tests that a JSON data dictionary can be generated."""
    mock_connector_class.return_value = mock_db_connector
    with patch('builtins.open', new_callable=MagicMock) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = "key: value"
        with patch('yaml.safe_load', return_value={}) as mock_yaml:
            agent = DatabaseAgent()
            result = await agent.generate_data_dictionary(output_format="json")

            import json
            data = json.loads(result)
            assert isinstance(data, list)
            assert len(data) == 2
            assert data[0]["table"] == "USERS"
            assert "columns" in data[0]