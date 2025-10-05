"""
Unit tests for GraphBuilder.
"""

import pytest
import tempfile
from pathlib import Path
import json

from graph.graph_builder import GraphBuilder
from graph.schema import Node, Edge, NodeType, EdgeType


class TestGraphBuilderInit:
    """Test GraphBuilder initialization."""

    def test_init(self):
        """Test basic initialization."""
        builder = GraphBuilder()

        assert len(builder.nodes) == 0
        assert len(builder.file_index) == 0
        assert builder.graph.number_of_nodes() == 0
        assert builder.graph.number_of_edges() == 0


class TestAddNode:
    """Test adding nodes to the graph."""

    def test_add_single_node(self):
        """Test adding a single node."""
        builder = GraphBuilder()

        node = Node(
            id="com.example.UserService",
            type=NodeType.SERVICE,
            name="UserService",
            file_path="src/UserService.java"
        )

        result = builder.add_node(node)

        assert result is True
        assert len(builder.nodes) == 1
        assert builder.nodes["com.example.UserService"] == node
        assert builder.file_index["src/UserService.java"] == "com.example.UserService"
        assert builder.graph.number_of_nodes() == 1

    def test_add_duplicate_node(self):
        """Test that adding duplicate node returns False."""
        builder = GraphBuilder()

        node1 = Node(id="test", type=NodeType.SERVICE, name="Test")
        node2 = Node(id="test", type=NodeType.CONTROLLER, name="DifferentTest")

        assert builder.add_node(node1) is True
        assert builder.add_node(node2) is False  # Duplicate ID
        assert len(builder.nodes) == 1

    def test_file_index_updated(self):
        """Test that file index is updated when adding nodes."""
        builder = GraphBuilder()

        node = Node(
            id="test.A",
            type=NodeType.SERVICE,
            name="A",
            file_path="/path/to/file.java"
        )

        builder.add_node(node)

        assert "/path/to/file.java" in builder.file_index
        assert builder.file_index["/path/to/file.java"] == "test.A"


class TestAddEdge:
    """Test adding edges to the graph."""

    def test_add_valid_edge(self):
        """Test adding a valid edge."""
        builder = GraphBuilder()

        # Add nodes first
        controller = Node(id="controller", type=NodeType.CONTROLLER, name="C")
        service = Node(id="service", type=NodeType.SERVICE, name="S")
        builder.add_node(controller)
        builder.add_node(service)

        # Add edge
        edge = Edge(
            source="controller",
            target="service",
            type=EdgeType.CALLS_SERVICE
        )

        result = builder.add_edge(edge)

        assert result is True
        assert builder.graph.number_of_edges() == 1

    def test_add_edge_source_not_found(self):
        """Test that adding edge with missing source raises error."""
        builder = GraphBuilder()

        service = Node(id="service", type=NodeType.SERVICE, name="S")
        builder.add_node(service)

        edge = Edge(
            source="missing",
            target="service",
            type=EdgeType.CALLS_SERVICE
        )

        with pytest.raises(ValueError, match="Source node not found"):
            builder.add_edge(edge)

    def test_add_edge_target_not_found(self):
        """Test that adding edge with missing target raises error."""
        builder = GraphBuilder()

        controller = Node(id="controller", type=NodeType.CONTROLLER, name="C")
        builder.add_node(controller)

        edge = Edge(
            source="controller",
            target="missing",
            type=EdgeType.CALLS_SERVICE
        )

        with pytest.raises(ValueError, match="Target node not found"):
            builder.add_edge(edge)

    def test_add_invalid_edge_pattern(self):
        """Test that invalid edge patterns are rejected."""
        builder = GraphBuilder()

        jsp = Node(id="jsp", type=NodeType.JSP, name="JSP")
        service = Node(id="service", type=NodeType.SERVICE, name="S")
        builder.add_node(jsp)
        builder.add_node(service)

        # JSP cannot call service directly (invalid pattern)
        edge = Edge(
            source="jsp",
            target="service",
            type=EdgeType.CALLS_SERVICE
        )

        result = builder.add_edge(edge)
        assert result is False  # Should be rejected

    def test_add_duplicate_edge(self):
        """Test that adding duplicate edge returns False."""
        builder = GraphBuilder()

        controller = Node(id="controller", type=NodeType.CONTROLLER, name="C")
        service = Node(id="service", type=NodeType.SERVICE, name="S")
        builder.add_node(controller)
        builder.add_node(service)

        edge = Edge(
            source="controller",
            target="service",
            type=EdgeType.CALLS_SERVICE
        )

        assert builder.add_edge(edge) is True
        assert builder.add_edge(edge) is False  # Duplicate

    def test_add_parallel_edges(self):
        """Test that MultiDiGraph supports parallel edges."""
        builder = GraphBuilder()

        controller = Node(id="controller", type=NodeType.CONTROLLER, name="C")
        service = Node(id="service", type=NodeType.SERVICE, name="S")
        builder.add_node(controller)
        builder.add_node(service)

        edge1 = Edge(
            source="controller",
            target="service",
            type=EdgeType.CALLS_SERVICE
        )
        edge2 = Edge(
            source="controller",
            target="service",
            type=EdgeType.DEPENDS_ON
        )

        assert builder.add_edge(edge1) is True
        assert builder.add_edge(edge2) is True
        assert builder.graph.number_of_edges() == 2  # Both edges added


class TestGetNode:
    """Test node retrieval methods."""

    def test_get_node_by_id(self):
        """Test getting node by ID."""
        builder = GraphBuilder()

        node = Node(id="test", type=NodeType.SERVICE, name="Test")
        builder.add_node(node)

        retrieved = builder.get_node("test")
        assert retrieved == node

    def test_get_node_not_found(self):
        """Test getting non-existent node returns None."""
        builder = GraphBuilder()

        assert builder.get_node("missing") is None

    def test_get_node_by_file_path(self):
        """Test getting node by file path."""
        builder = GraphBuilder()

        node = Node(
            id="test",
            type=NodeType.SERVICE,
            name="Test",
            file_path="/path/to/file.java"
        )
        builder.add_node(node)

        retrieved = builder.get_node_by_file_path("/path/to/file.java")
        assert retrieved == node

    def test_get_node_by_file_path_not_found(self):
        """Test getting node by non-existent file path returns None."""
        builder = GraphBuilder()

        assert builder.get_node_by_file_path("/missing/file.java") is None


class TestGraphQueries:
    """Test graph query methods."""

    def setup_method(self):
        """Set up test graph."""
        self.builder = GraphBuilder()

        # Create a small graph: Controller -> Service -> Mapper -> Table
        self.controller = Node(id="controller", type=NodeType.CONTROLLER, name="C")
        self.service = Node(id="service", type=NodeType.SERVICE, name="S")
        self.mapper = Node(id="mapper", type=NodeType.MAPPER, name="M")
        self.table = Node(id="table", type=NodeType.DATABASE_TABLE, name="T")

        self.builder.add_node(self.controller)
        self.builder.add_node(self.service)
        self.builder.add_node(self.mapper)
        self.builder.add_node(self.table)

        self.builder.add_edge(Edge("controller", "service", EdgeType.CALLS_SERVICE))
        self.builder.add_edge(Edge("service", "mapper", EdgeType.USES_MAPPER))
        self.builder.add_edge(Edge("mapper", "table", EdgeType.QUERIES_TABLE))

    def test_get_neighbors_outgoing(self):
        """Test getting outgoing neighbors."""
        neighbors = self.builder.get_neighbors("controller", direction="outgoing")

        assert len(neighbors) == 1
        assert neighbors[0].id == "service"

    def test_get_neighbors_incoming(self):
        """Test getting incoming neighbors."""
        neighbors = self.builder.get_neighbors("service", direction="incoming")

        assert len(neighbors) == 1
        assert neighbors[0].id == "controller"

    def test_get_neighbors_both(self):
        """Test getting both incoming and outgoing neighbors."""
        neighbors = self.builder.get_neighbors("service", direction="both")

        assert len(neighbors) == 2
        neighbor_ids = {n.id for n in neighbors}
        assert neighbor_ids == {"controller", "mapper"}

    def test_find_shortest_path(self):
        """Test finding shortest path."""
        path = self.builder.find_shortest_path("controller", "table")

        assert path is not None
        assert len(path) == 4
        assert [n.id for n in path] == ["controller", "service", "mapper", "table"]

    def test_find_shortest_path_no_path(self):
        """Test that finding path returns None when no path exists."""
        # Add isolated node
        isolated = Node(id="isolated", type=NodeType.SERVICE, name="I")
        self.builder.add_node(isolated)

        path = self.builder.find_shortest_path("controller", "isolated")
        assert path is None

    def test_find_all_dependencies(self):
        """Test finding all dependencies."""
        deps = self.builder.find_all_dependencies("controller")

        assert len(deps) == 3
        dep_ids = {d.id for d in deps}
        assert dep_ids == {"service", "mapper", "table"}

    def test_find_all_dependents(self):
        """Test finding all dependents."""
        dependents = self.builder.find_all_dependents("table")

        assert len(dependents) == 3
        dependent_ids = {d.id for d in dependents}
        assert dependent_ids == {"mapper", "service", "controller"}

    def test_find_dependencies_with_max_depth(self):
        """Test dependency finding with depth limit."""
        deps = self.builder.find_all_dependencies("controller", max_depth=1)

        assert len(deps) == 1  # Only direct dependency
        assert list(deps)[0].id == "service"

    def test_analyze_impact(self):
        """Test impact analysis."""
        impact = self.builder.analyze_impact("service")

        assert impact["node"].id == "service"
        assert len(impact["direct_dependencies"]) == 1
        assert len(impact["direct_dependents"]) == 1
        assert len(impact["all_dependencies"]) == 2  # mapper, table
        assert len(impact["all_dependents"]) == 1  # controller
        assert impact["impact_score"] == 3  # 2 deps + 1 dependent


class TestGraphStats:
    """Test graph statistics."""

    def test_empty_graph_stats(self):
        """Test stats for empty graph."""
        builder = GraphBuilder()
        stats = builder.get_stats()

        assert stats["total_nodes"] == 0
        assert stats["total_edges"] == 0
        assert stats["density"] == 0.0

    def test_graph_stats(self):
        """Test stats for non-empty graph."""
        builder = GraphBuilder()

        # Add some nodes and edges
        controller = Node(id="controller", type=NodeType.CONTROLLER, name="C")
        service = Node(id="service", type=NodeType.SERVICE, name="S")
        builder.add_node(controller)
        builder.add_node(service)
        builder.add_edge(Edge("controller", "service", EdgeType.CALLS_SERVICE))

        stats = builder.get_stats()

        assert stats["total_nodes"] == 2
        assert stats["total_edges"] == 1
        assert stats["node_counts"]["controller"] == 1
        assert stats["node_counts"]["service"] == 1
        assert stats["edge_counts"]["calls_service"] == 1
        assert stats["density"] > 0


class TestGraphPersistence:
    """Test graph save/load functionality."""

    def test_save_load_json(self):
        """Test saving and loading graph in JSON format."""
        builder = GraphBuilder()

        # Create graph
        node = Node(id="test", type=NodeType.SERVICE, name="Test")
        builder.add_node(node)

        # Save
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "graph.json"
            builder.save_graph(str(output_path), format="json")

            # Load
            builder2 = GraphBuilder()
            builder2.load_graph(str(output_path), format="json")

            # Verify
            assert len(builder2.nodes) == 1
            assert "test" in builder2.nodes
            assert builder2.nodes["test"].type == NodeType.SERVICE

    def test_export_dot(self):
        """Test exporting to DOT format."""
        builder = GraphBuilder()

        controller = Node(id="controller", type=NodeType.CONTROLLER, name="C")
        service = Node(id="service", type=NodeType.SERVICE, name="S")
        builder.add_node(controller)
        builder.add_node(service)
        builder.add_edge(Edge("controller", "service", EdgeType.CALLS_SERVICE))

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "graph.dot"
            builder.export_dot(str(output_path))

            # Verify file was created
            assert output_path.exists()

            # Verify content
            content = output_path.read_text()
            assert "digraph SpringMVC" in content
            assert "controller" in content
            assert "service" in content

    def test_export_d3_json(self):
        """Test exporting to D3.js JSON format."""
        builder = GraphBuilder()

        controller = Node(id="controller", type=NodeType.CONTROLLER, name="C")
        service = Node(id="service", type=NodeType.SERVICE, name="S")
        builder.add_node(controller)
        builder.add_node(service)
        builder.add_edge(Edge("controller", "service", EdgeType.CALLS_SERVICE))

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "graph.json"
            builder.export_d3_json(str(output_path))

            # Verify file was created
            assert output_path.exists()

            # Verify structure
            data = json.loads(output_path.read_text())
            assert "nodes" in data
            assert "links" in data
            assert len(data["nodes"]) == 2
            assert len(data["links"]) == 1

    def test_export_cytoscape_json(self):
        """Test exporting to Cytoscape.js JSON format."""
        builder = GraphBuilder()

        controller = Node(id="controller", type=NodeType.CONTROLLER, name="C")
        builder.add_node(controller)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "graph.json"
            builder.export_cytoscape_json(str(output_path))

            # Verify file was created
            assert output_path.exists()

            # Verify structure
            data = json.loads(output_path.read_text())
            assert "elements" in data
            assert len(data["elements"]) == 1
            assert data["elements"][0]["group"] == "nodes"


class TestBuildFromAnalysisResults:
    """Test building graph from analysis results."""

    def test_build_empty_results(self):
        """Test building from empty results."""
        builder = GraphBuilder()

        nodes_added, edges_added = builder.build_from_analysis_results({})

        assert nodes_added == 0
        assert edges_added == 0

    def test_build_with_controller(self):
        """Test building with controller analysis."""
        builder = GraphBuilder()

        analysis_results = {
            "UserController.java": {
                "agent": "controller",
                "analysis": {
                    "class_name": "UserController",
                    "package": "com.example",
                    "mappings": [],
                    "dependencies": []
                },
                "confidence": 0.95
            }
        }

        nodes_added, edges_added = builder.build_from_analysis_results(analysis_results)

        assert nodes_added == 1
        assert "com.example.UserController" in builder.nodes

    def test_build_with_invalid_results(self):
        """Test that invalid results raise ValueError."""
        builder = GraphBuilder()

        with pytest.raises(ValueError, match="must be a dictionary"):
            builder.build_from_analysis_results("not a dict")


class TestIsCustomModel:
    """Test _is_custom_model helper method."""

    def test_primitive_types(self):
        """Test that primitive types are excluded."""
        builder = GraphBuilder()

        assert not builder._is_custom_model("int")
        assert not builder._is_custom_model("long")
        assert not builder._is_custom_model("boolean")
        assert not builder._is_custom_model("void")

    def test_java_standard_library(self):
        """Test that Java standard library types are excluded."""
        builder = GraphBuilder()

        assert not builder._is_custom_model("java.lang.String")
        assert not builder._is_custom_model("java.util.List")
        assert not builder._is_custom_model("javax.servlet.HttpServletRequest")

    def test_spring_framework(self):
        """Test that Spring framework types are excluded."""
        builder = GraphBuilder()

        assert not builder._is_custom_model("org.springframework.ui.Model")
        assert not builder._is_custom_model("org.springframework.web.bind.annotation.RequestMapping")

    def test_wrapper_types(self):
        """Test that wrapper types are excluded."""
        builder = GraphBuilder()

        assert not builder._is_custom_model("String")
        assert not builder._is_custom_model("Integer")
        assert not builder._is_custom_model("Boolean")

    def test_collection_types(self):
        """Test that collection types are excluded."""
        builder = GraphBuilder()

        assert not builder._is_custom_model("List")
        assert not builder._is_custom_model("Map")
        assert not builder._is_custom_model("Set")

    def test_custom_models(self):
        """Test that custom models are accepted."""
        builder = GraphBuilder()

        assert builder._is_custom_model("com.example.User")
        assert builder._is_custom_model("com.example.dto.UserDTO")
        assert builder._is_custom_model("UserModel")
