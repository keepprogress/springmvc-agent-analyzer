"""
Unit tests for the ConfigAgent.
"""

import pytest
from unittest.mock import patch, MagicMock

from agents.config_agent import ConfigAgent

@pytest.fixture
def mock_config_agent():
    """Provides an instance of the ConfigAgent."""
    return ConfigAgent()

@pytest.fixture
def mock_spring_xml_content():
    """Provides mock Spring XML content."""
    return """
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd">

    <bean id="dataSource" class="org.apache.commons.dbcp.BasicDataSource">
        <property name="driverClassName" value="oracle.jdbc.driver.OracleDriver"/>
        <property name="url" value="jdbc:oracle:thin:@localhost:1521:xe"/>
    </bean>

    <bean id="userService" class="com.example.UserService">
        <property name="userDao" ref="userDao"/>
    </bean>

    <import resource="other-context.xml"/>
</beans>
"""

@pytest.fixture
def mock_properties_content():
    """Provides mock .properties file content."""
    return """
database.url=jdbc:mysql://localhost:3306/mydb
database.user=root
"""

@pytest.mark.asyncio
async def test_analyze_spring_xml(mock_config_agent, mock_spring_xml_content):
    """Tests parsing of a Spring XML file."""
    with patch('pathlib.Path.exists', return_value=True):
        with patch('xml.etree.ElementTree.parse') as mock_parse:
            # Mock the ElementTree object and its findall method
            mock_root = MagicMock()
            mock_bean1 = MagicMock()
            mock_bean1.get.side_effect = ['dataSource', 'org.apache.commons.dbcp.BasicDataSource', 'singleton']
            mock_bean1.findall.return_value = [] # No properties for simplicity in this mock
            mock_bean2 = MagicMock()
            mock_bean2.get.side_effect = ['userService', 'com.example.UserService', 'singleton']
            mock_bean2.findall.return_value = []
            mock_import = MagicMock()
            mock_import.get.return_value = 'other-context.xml'

            mock_root.findall.side_effect = [
                [mock_bean1, mock_bean2], # For beans:bean
                [mock_import] # For beans:import
            ]
            mock_parse.return_value.getroot.return_value = mock_root

            result = await mock_config_agent.analyze_spring_xml("dummy_path.xml")

            assert result['total_beans'] == 2
            assert result['imported_resources'] == ['other-context.xml']
            assert result['bean_definitions'][0]['id'] == 'dataSource'


@pytest.mark.asyncio
async def test_analyze_properties_file(mock_config_agent, mock_properties_content):
    """Tests parsing of a .properties file."""
    with patch('pathlib.Path.exists', return_value=True):
        with patch('pathlib.Path.read_text', return_value=mock_properties_content):
            result = await mock_config_agent.analyze_properties_file("dummy.properties")

            assert result['total_properties'] == 2
            assert result['properties']['database.url'] == 'jdbc:mysql://localhost:3306/mydb'
            assert result['properties']['database.user'] == 'root'