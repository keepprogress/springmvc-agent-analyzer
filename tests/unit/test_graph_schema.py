"""
Unit tests for graph schema (nodes, edges, validation).
"""

import pytest
from graph.schema import Node, Edge, NodeType, EdgeType, GraphSchema


class TestNodeType:
    """Test NodeType enum."""

    def test_all_types_defined(self):
        """Test that all expected node types are defined."""
        expected_types = {
            "controller", "jsp", "service", "mapper",
            "procedure", "endpoint", "model", "table"
        }
        actual_types = {nt.value for nt in NodeType}
        assert actual_types == expected_types


class TestEdgeType:
    """Test EdgeType enum."""

    def test_all_types_defined(self):
        """Test that all expected edge types are defined."""
        expected_types = {
            "depends_on", "calls_service", "renders_jsp", "exposes_endpoint",
            "submits_to", "ajax_call", "includes", "uses_model",
            "uses_mapper", "calls_procedure", "orchestrates",
            "queries_table", "executes_procedure",
            "produces", "consumes", "transforms"
        }
        actual_types = {et.value for et in EdgeType}
        assert actual_types == expected_types


class TestNode:
    """Test Node dataclass."""

    def test_create_node(self):
        """Test creating a basic node."""
        node = Node(
            id="com.example.UserController",
            type=NodeType.CONTROLLER,
            name="UserController",
            file_path="src/main/java/com/example/UserController.java"
        )

        assert node.id == "com.example.UserController"
        assert node.type == NodeType.CONTROLLER
        assert node.name == "UserController"
        assert node.file_path == "src/main/java/com/example/UserController.java"
        assert node.metadata == {}

    def test_node_with_metadata(self):
        """Test creating a node with metadata."""
        node = Node(
            id="com.example.UserController",
            type=NodeType.CONTROLLER,
            name="UserController",
            metadata={"package": "com.example", "confidence": 0.95}
        )

        assert node.metadata["package"] == "com.example"
        assert node.metadata["confidence"] == 0.95

    def test_node_equality(self):
        """Test node equality based on ID."""
        node1 = Node(
            id="test.Node",
            type=NodeType.SERVICE,
            name="Node"
        )
        node2 = Node(
            id="test.Node",
            type=NodeType.CONTROLLER,  # Different type
            name="Different"  # Different name
        )
        node3 = Node(
            id="test.Different",
            type=NodeType.SERVICE,
            name="Node"
        )

        assert node1 == node2  # Same ID
        assert node1 != node3  # Different ID

    def test_node_hashable(self):
        """Test that nodes can be used in sets/dicts."""
        node1 = Node(id="test.A", type=NodeType.SERVICE, name="A")
        node2 = Node(id="test.B", type=NodeType.SERVICE, name="B")
        node3 = Node(id="test.A", type=NodeType.CONTROLLER, name="A")

        node_set = {node1, node2, node3}
        assert len(node_set) == 2  # node1 and node3 are same (same ID)


class TestEdge:
    """Test Edge dataclass."""

    def test_create_edge(self):
        """Test creating a basic edge."""
        edge = Edge(
            source="com.example.UserController",
            target="com.example.UserService",
            type=EdgeType.CALLS_SERVICE
        )

        assert edge.source == "com.example.UserController"
        assert edge.target == "com.example.UserService"
        assert edge.type == EdgeType.CALLS_SERVICE
        assert edge.metadata == {}

    def test_edge_with_metadata(self):
        """Test creating an edge with metadata."""
        edge = Edge(
            source="controller",
            target="service",
            type=EdgeType.CALLS_SERVICE,
            metadata={"method": "getUser", "param": "id"}
        )

        assert edge.metadata["method"] == "getUser"
        assert edge.metadata["param"] == "id"

    def test_edge_equality(self):
        """Test edge equality based on source, target, and type."""
        edge1 = Edge("A", "B", EdgeType.CALLS_SERVICE)
        edge2 = Edge("A", "B", EdgeType.CALLS_SERVICE, metadata={"foo": "bar"})
        edge3 = Edge("A", "B", EdgeType.DEPENDS_ON)
        edge4 = Edge("A", "C", EdgeType.CALLS_SERVICE)

        assert edge1 == edge2  # Same source/target/type, different metadata
        assert edge1 != edge3  # Different type
        assert edge1 != edge4  # Different target

    def test_edge_hashable(self):
        """Test that edges can be used in sets/dicts."""
        edge1 = Edge("A", "B", EdgeType.CALLS_SERVICE)
        edge2 = Edge("A", "B", EdgeType.DEPENDS_ON)
        edge3 = Edge("A", "B", EdgeType.CALLS_SERVICE)

        edge_set = {edge1, edge2, edge3}
        assert len(edge_set) == 2  # edge1 and edge3 are same


class TestGraphSchema:
    """Test GraphSchema validation."""

    def test_valid_controller_patterns(self):
        """Test valid controller edge patterns."""
        schema = GraphSchema()

        assert schema.validate_edge(
            NodeType.CONTROLLER,
            EdgeType.CALLS_SERVICE,
            NodeType.SERVICE
        )

        assert schema.validate_edge(
            NodeType.CONTROLLER,
            EdgeType.RENDERS_JSP,
            NodeType.JSP
        )

        assert schema.validate_edge(
            NodeType.CONTROLLER,
            EdgeType.EXPOSES_ENDPOINT,
            NodeType.ENDPOINT
        )

    def test_valid_service_patterns(self):
        """Test valid service edge patterns."""
        schema = GraphSchema()

        assert schema.validate_edge(
            NodeType.SERVICE,
            EdgeType.USES_MAPPER,
            NodeType.MAPPER
        )

        assert schema.validate_edge(
            NodeType.SERVICE,
            EdgeType.ORCHESTRATES,
            NodeType.SERVICE
        )

    def test_valid_jsp_patterns(self):
        """Test valid JSP edge patterns."""
        schema = GraphSchema()

        assert schema.validate_edge(
            NodeType.JSP,
            EdgeType.SUBMITS_TO,
            NodeType.ENDPOINT
        )

        assert schema.validate_edge(
            NodeType.JSP,
            EdgeType.AJAX_CALL,
            NodeType.ENDPOINT
        )

        assert schema.validate_edge(
            NodeType.JSP,
            EdgeType.INCLUDES,
            NodeType.JSP
        )

    def test_invalid_patterns(self):
        """Test that invalid patterns are rejected."""
        schema = GraphSchema()

        # JSP cannot call service directly
        assert not schema.validate_edge(
            NodeType.JSP,
            EdgeType.CALLS_SERVICE,
            NodeType.SERVICE
        )

        # Table cannot query mapper (reverse relationship)
        assert not schema.validate_edge(
            NodeType.DATABASE_TABLE,
            EdgeType.QUERIES_TABLE,
            NodeType.MAPPER
        )

        # Endpoint cannot render JSP
        assert not schema.validate_edge(
            NodeType.ENDPOINT,
            EdgeType.RENDERS_JSP,
            NodeType.JSP
        )

    def test_get_allowed_edges(self):
        """Test getting allowed edges for a node type."""
        schema = GraphSchema()

        controller_edges = schema.get_allowed_edges(NodeType.CONTROLLER)
        assert EdgeType.CALLS_SERVICE in controller_edges
        assert EdgeType.RENDERS_JSP in controller_edges
        assert EdgeType.EXPOSES_ENDPOINT in controller_edges

        service_edges = schema.get_allowed_edges(NodeType.SERVICE)
        assert EdgeType.USES_MAPPER in service_edges
        assert EdgeType.ORCHESTRATES in service_edges

    def test_get_allowed_targets(self):
        """Test getting allowed targets for source + edge combination."""
        schema = GraphSchema()

        targets = schema.get_allowed_targets(
            NodeType.CONTROLLER,
            EdgeType.CALLS_SERVICE
        )
        assert NodeType.SERVICE in targets

        targets = schema.get_allowed_targets(
            NodeType.SERVICE,
            EdgeType.USES_MAPPER
        )
        assert NodeType.MAPPER in targets
