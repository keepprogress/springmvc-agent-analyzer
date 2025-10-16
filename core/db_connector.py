"""
Conceptual Database Connector.

This module simulates a database connection for extracting schema information.
In a real implementation, this would use a library like 'oracledb',
'psycopg2', or 'sqlalchemy'.
"""

import asyncio
from typing import Dict, Any, List


class DatabaseConnector:
    """
    A simulated database connector for Oracle.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the connector.

        Args:
            config: A dictionary with connection details like 'host', 'port',
                    'user', 'password', 'service_name'.
        """
        self.config = config
        self.is_connected = False
        print(f"DatabaseConnector initialized for user '{self.config.get('user')}' on host '{self.config.get('host')}'.")

    async def connect(self):
        """Simulates establishing a database connection."""
        if self.is_connected:
            return
        print("Simulating: Connecting to the database...")
        await asyncio.sleep(0.1)  # Simulate network latency
        self.is_connected = True
        print("Simulating: Connection successful.")

    async def disconnect(self):
        """Simulates closing the database connection."""
        if not self.is_connected:
            return
        print("Simulating: Disconnecting from the database...")
        await asyncio.sleep(0.05)
        self.is_connected = False
        print("Simulating: Disconnection successful.")

    async def get_all_tables(self) -> List[str]:
        """Simulates fetching a list of all user tables."""
        if not self.is_connected:
            raise ConnectionError("Not connected to the database.")
        print("Simulating: Fetching all table names...")
        await asyncio.sleep(0.2)
        # Mock response
        return ["USERS", "ORDERS", "PRODUCTS", "ORDER_ITEMS", "DEPARTMENTS"]

    async def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Simulates fetching column metadata for a specific table."""
        if not self.is_connected:
            raise ConnectionError("Not connected to the database.")
        print(f"Simulating: Fetching column info for table '{table_name}'...")
        await asyncio.sleep(0.1)

        # Mock responses for different tables
        mock_schemas = {
            "USERS": [
                {"name": "USER_ID", "type": "NUMBER(10)", "nullable": False, "comment": "Primary Key"},
                {"name": "USERNAME", "type": "VARCHAR2(50)", "nullable": False, "comment": "Unique username"},
                {"name": "EMAIL", "type": "VARCHAR2(100)", "nullable": False, "comment": "User's email address"},
                {"name": "CREATED_AT", "type": "DATE", "nullable": True, "comment": "Timestamp of user creation"},
            ],
            "ORDERS": [
                {"name": "ORDER_ID", "type": "NUMBER(10)", "nullable": False, "comment": "Primary Key"},
                {"name": "USER_ID", "type": "NUMBER(10)", "nullable": False, "comment": "Foreign key to USERS table"},
                {"name": "ORDER_DATE", "type": "TIMESTAMP", "nullable": False, "comment": "Date the order was placed"},
                {"name": "STATUS", "type": "VARCHAR2(20)", "nullable": True, "comment": "Order status (e.g., PENDING, SHIPPED)"},
            ],
            "PRODUCTS": [
                {"name": "PRODUCT_ID", "type": "NUMBER(10)", "nullable": False, "comment": "Primary Key"},
                {"name": "NAME", "type": "VARCHAR2(200)", "nullable": False, "comment": "Product name"},
                {"name": "PRICE", "type": "NUMBER(10, 2)", "nullable": True, "comment": "Price of the product"},
            ],
        }
        return mock_schemas.get(table_name, [])