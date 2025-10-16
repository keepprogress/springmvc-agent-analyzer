"""
Configuration Analysis Agent.

This agent specializes in parsing and interpreting Spring configuration files,
including XML-based bean definitions and .properties files.
"""

import xml.etree.ElementTree as ET
from configparser import ConfigParser
from pathlib import Path
from typing import Dict, Any, List

from sdk_agent.exceptions import SDKAgentError


class ConfigAgent:
    """
    Agent for analyzing Spring Framework configuration files.
    """

    def __init__(self):
        """Initializes the ConfigAgent."""
        print("Configuration Analysis Agent initialized.")

    async def analyze_spring_xml(self, file_path: str) -> Dict[str, Any]:
        """
        Parses a Spring XML configuration file to extract bean definitions,
        aliases, and imported resources.

        Args:
            file_path: The path to the Spring XML file.

        Returns:
            A dictionary containing the extracted configuration details.
        """
        print(f"Analyzing Spring XML file: {file_path}")
        path = Path(file_path)
        if not path.exists():
            raise SDKAgentError(f"XML configuration file not found: {file_path}")

        tree = ET.parse(path)
        root = tree.getroot()

        # Namespace handling is critical for Spring XML
        ns = {'beans': 'http://www.springframework.org/schema/beans'}

        beans = []
        for bean_elem in root.findall('beans:bean', ns):
            bean_info = {
                "id": bean_elem.get("id"),
                "class": bean_elem.get("class"),
                "scope": bean_elem.get("scope", "singleton"),
                "properties": []
            }
            for prop_elem in bean_elem.findall('beans:property', ns):
                bean_info["properties"].append({
                    "name": prop_elem.get("name"),
                    "value": prop_elem.get("value"),
                    "ref": prop_elem.get("ref")
                })
            beans.append(bean_info)

        imports = [imp.get("resource") for imp in root.findall('beans:import', ns)]

        return {
            "file_path": file_path,
            "bean_definitions": beans,
            "imported_resources": imports,
            "total_beans": len(beans),
        }

    async def analyze_properties_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parses a .properties file to extract key-value pairs.

        Args:
            file_path: The path to the .properties file.

        Returns:
            A dictionary containing the extracted properties.
        """
        print(f"Analyzing properties file: {file_path}")
        path = Path(file_path)
        if not path.exists():
            raise SDKAgentError(f"Properties file not found: {file_path}")

        # ConfigParser needs a section, so we add a dummy one.
        config_string = '[dummy_section]\n' + path.read_text()
        config = ConfigParser()
        config.read_string(config_string)

        properties = dict(config.items('dummy_section'))

        return {
            "file_path": file_path,
            "properties": properties,
            "total_properties": len(properties),
        }