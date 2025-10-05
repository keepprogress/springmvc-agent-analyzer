"""
Knowledge Graph Schema for SpringMVC Application Analysis.

Defines node types, edge types, and relationship patterns for the
dependency graph connecting Controllers, JSPs, Services, Mappers, and Procedures.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


class NodeType(Enum):
    """Types of nodes in the knowledge graph."""

    CONTROLLER = "controller"
    JSP = "jsp"
    SERVICE = "service"
    MAPPER = "mapper"
    PROCEDURE = "procedure"
    ENDPOINT = "endpoint"         # HTTP endpoint (extracted from controller)
    MODEL = "model"               # Data model/DTO
    DATABASE_TABLE = "table"      # Database table


class EdgeType(Enum):
    """Types of relationships between nodes."""

    # Controller relationships
    DEPENDS_ON = "depends_on"              # Generic dependency
    CALLS_SERVICE = "calls_service"        # Controller → Service
    RENDERS_JSP = "renders_jsp"            # Controller → JSP
    EXPOSES_ENDPOINT = "exposes_endpoint"  # Controller → Endpoint

    # JSP relationships
    SUBMITS_TO = "submits_to"              # JSP → Endpoint (form submission)
    AJAX_CALL = "ajax_call"                # JSP → Endpoint (AJAX)
    INCLUDES = "includes"                  # JSP → JSP (include/import)
    USES_MODEL = "uses_model"              # JSP → Model

    # Service relationships
    USES_MAPPER = "uses_mapper"            # Service → Mapper
    CALLS_PROCEDURE = "calls_procedure"    # Service → Procedure (if direct)
    ORCHESTRATES = "orchestrates"          # Service → Service

    # Mapper relationships
    QUERIES_TABLE = "queries_table"        # Mapper → Table
    EXECUTES_PROCEDURE = "executes_procedure"  # Mapper → Procedure

    # Data flow
    PRODUCES = "produces"                  # Component → Model
    CONSUMES = "consumes"                  # Component → Model
    TRANSFORMS = "transforms"              # Component → Model


@dataclass
class Node:
    """
    Represents a node in the knowledge graph.

    Attributes:
        id: Unique identifier (e.g., "com.example.UserController", "users.jsp")
        type: Node type (controller, jsp, service, etc.)
        name: Display name
        file_path: Source file path
        metadata: Additional properties (analysis results, etc.)
    """
    id: str
    type: NodeType
    name: str
    file_path: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.id == other.id


@dataclass
class Edge:
    """
    Represents a directed edge in the knowledge graph.

    Attributes:
        source: Source node ID
        target: Target node ID
        type: Edge type (relationship)
        metadata: Additional properties (method name, parameters, etc.)
    """
    source: str
    target: str
    type: EdgeType
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.source, self.target, self.type))

    def __eq__(self, other):
        if not isinstance(other, Edge):
            return False
        return (self.source == other.source and
                self.target == other.target and
                self.type == other.type)


class GraphSchema:
    """
    Schema definition and validation for knowledge graph.

    Defines valid node-edge-node patterns and constraints.
    """

    # Valid edge patterns: (source_type, edge_type, target_type)
    VALID_PATTERNS = {
        # Controller patterns
        (NodeType.CONTROLLER, EdgeType.CALLS_SERVICE, NodeType.SERVICE),
        (NodeType.CONTROLLER, EdgeType.RENDERS_JSP, NodeType.JSP),
        (NodeType.CONTROLLER, EdgeType.EXPOSES_ENDPOINT, NodeType.ENDPOINT),
        (NodeType.CONTROLLER, EdgeType.DEPENDS_ON, NodeType.SERVICE),

        # JSP patterns
        (NodeType.JSP, EdgeType.SUBMITS_TO, NodeType.ENDPOINT),
        (NodeType.JSP, EdgeType.AJAX_CALL, NodeType.ENDPOINT),
        (NodeType.JSP, EdgeType.INCLUDES, NodeType.JSP),
        (NodeType.JSP, EdgeType.USES_MODEL, NodeType.MODEL),

        # Service patterns
        (NodeType.SERVICE, EdgeType.USES_MAPPER, NodeType.MAPPER),
        (NodeType.SERVICE, EdgeType.CALLS_PROCEDURE, NodeType.PROCEDURE),
        (NodeType.SERVICE, EdgeType.ORCHESTRATES, NodeType.SERVICE),
        (NodeType.SERVICE, EdgeType.DEPENDS_ON, NodeType.SERVICE),
        (NodeType.SERVICE, EdgeType.DEPENDS_ON, NodeType.MAPPER),

        # Mapper patterns
        (NodeType.MAPPER, EdgeType.QUERIES_TABLE, NodeType.DATABASE_TABLE),
        (NodeType.MAPPER, EdgeType.EXECUTES_PROCEDURE, NodeType.PROCEDURE),

        # Data flow patterns
        (NodeType.CONTROLLER, EdgeType.PRODUCES, NodeType.MODEL),
        (NodeType.CONTROLLER, EdgeType.CONSUMES, NodeType.MODEL),
        (NodeType.SERVICE, EdgeType.PRODUCES, NodeType.MODEL),
        (NodeType.SERVICE, EdgeType.CONSUMES, NodeType.MODEL),
        (NodeType.MAPPER, EdgeType.PRODUCES, NodeType.MODEL),
        (NodeType.JSP, EdgeType.CONSUMES, NodeType.MODEL),
    }

    @classmethod
    def validate_edge(
        cls,
        source_type: NodeType,
        edge_type: EdgeType,
        target_type: NodeType
    ) -> bool:
        """
        Validate if edge pattern is allowed.

        Args:
            source_type: Source node type
            edge_type: Edge type
            target_type: Target node type

        Returns:
            True if pattern is valid, False otherwise
        """
        return (source_type, edge_type, target_type) in cls.VALID_PATTERNS

    @classmethod
    def get_allowed_edges(cls, node_type: NodeType) -> List[EdgeType]:
        """
        Get all allowed outgoing edge types for a node type.

        Args:
            node_type: Source node type

        Returns:
            List of allowed edge types
        """
        return [
            edge_type for source, edge_type, _ in cls.VALID_PATTERNS
            if source == node_type
        ]

    @classmethod
    def get_allowed_targets(
        cls,
        source_type: NodeType,
        edge_type: EdgeType
    ) -> List[NodeType]:
        """
        Get allowed target node types for source + edge combination.

        Args:
            source_type: Source node type
            edge_type: Edge type

        Returns:
            List of allowed target node types
        """
        return [
            target for source, edge, target in cls.VALID_PATTERNS
            if source == source_type and edge == edge_type
        ]
