"""
Graph Builder for constructing knowledge graph from analysis results.

This module builds a NetworkX directed graph connecting all analyzed components
(Controllers, JSPs, Services, Mappers, Procedures) with their relationships.
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from pathlib import Path
import logging
import networkx as nx
import json
import itertools

from graph.schema import Node, Edge, NodeType, EdgeType, GraphSchema


class GraphBuilder:
    """
    Builds and manages the knowledge graph from agent analysis results.

    Uses NetworkX MultiDiGraph for efficient graph operations and queries.
    MultiDiGraph supports parallel edges (multiple relationships between same nodes).

    Attributes:
        graph: NetworkX multi-directed graph
        nodes: Dictionary mapping node IDs to Node objects
        file_index: Reverse mapping from file_path to node_id
        schema: Graph schema for validation
        logger: Logger instance
    """

    def __init__(self):
        """Initialize the Graph Builder."""
        self.graph = nx.MultiDiGraph()
        self.nodes: Dict[str, Node] = {}
        self.file_index: Dict[str, str] = {}  # file_path -> node_id
        self.schema = GraphSchema()
        self.logger = logging.getLogger("graph.graph_builder")

        self.logger.info("GraphBuilder initialized")

    def add_node(self, node: Node) -> bool:
        """
        Add a node to the graph.

        Args:
            node: Node object to add

        Returns:
            True if node was added, False if already exists
        """
        if node.id in self.nodes:
            self.logger.debug(f"Node {node.id} already exists, skipping")
            return False

        self.nodes[node.id] = node
        self.graph.add_node(
            node.id,
            type=node.type.value,
            name=node.name,
            file_path=node.file_path,
            **node.metadata
        )

        # Update file index if file_path is provided
        if node.file_path:
            self.file_index[node.file_path] = node.id

        self.logger.debug(f"Added node: {node.id} (type={node.type.value})")
        return True

    def add_edge(self, edge: Edge) -> bool:
        """
        Add an edge to the graph with schema validation.

        Args:
            edge: Edge object to add

        Returns:
            True if edge was added, False if validation failed or already exists

        Raises:
            ValueError: If source or target node doesn't exist
        """
        # Check nodes exist
        if edge.source not in self.nodes:
            raise ValueError(f"Source node not found: {edge.source}")
        if edge.target not in self.nodes:
            raise ValueError(f"Target node not found: {edge.target}")

        # Validate edge pattern
        source_type = self.nodes[edge.source].type
        target_type = self.nodes[edge.target].type

        if not self.schema.validate_edge(source_type, edge.type, target_type):
            self.logger.warning(
                f"Invalid edge pattern: {source_type.value} --{edge.type.value}--> {target_type.value}"
            )
            return False

        # Check if edge with same source, target, AND type already exists
        # In MultiDiGraph, graph[source][target] returns dict of {edge_key: edge_data}
        if self.graph.has_edge(edge.source, edge.target):
            edges_between = self.graph[edge.source][edge.target]
            for edge_key, edge_data in edges_between.items():
                if edge_data.get("type") == edge.type.value:
                    self.logger.debug(
                        f"Edge already exists: {edge.source} --{edge.type.value}--> {edge.target}"
                    )
                    return False

        # Add edge
        self.graph.add_edge(
            edge.source,
            edge.target,
            type=edge.type.value,
            **edge.metadata
        )

        self.logger.debug(
            f"Added edge: {edge.source} --{edge.type.value}--> {edge.target}"
        )
        return True

    def build_from_analysis_results(
        self,
        analysis_results: Dict[str, Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        Build graph from agent analysis results.

        Args:
            analysis_results: Dictionary mapping file paths to analysis results
                Format: {
                    "path/to/Controller.java": {
                        "agent": "controller",
                        "analysis": {...},
                        "confidence": 0.95,
                        ...
                    },
                    ...
                }

        Returns:
            Tuple of (nodes_added, edges_added)

        Raises:
            ValueError: If analysis_results is invalid
        """
        # Validate input
        if not isinstance(analysis_results, dict):
            raise ValueError(
                f"analysis_results must be a dictionary, got {type(analysis_results)}"
            )

        if not analysis_results:
            self.logger.warning("Empty analysis_results provided, nothing to build")
            return 0, 0

        nodes_added = 0
        edges_added = 0

        total_results = len(analysis_results)
        self.logger.info(f"Building graph from {total_results} analysis results")

        # First pass: Create all nodes
        self.logger.info(f"Phase 1/2: Creating nodes from {total_results} results")
        for idx, (file_path, result) in enumerate(analysis_results.items(), 1):
            agent_type = result.get("agent", "unknown")
            analysis = result.get("analysis", {})
            confidence = result.get("confidence", 0.0)

            # Create node based on agent type
            if agent_type == "controller":
                node = self._create_controller_node(file_path, analysis, confidence)
            elif agent_type == "jsp":
                node = self._create_jsp_node(file_path, analysis, confidence)
            elif agent_type == "service":
                node = self._create_service_node(file_path, analysis, confidence)
            elif agent_type == "mapper":
                node = self._create_mapper_node(file_path, analysis, confidence)
            elif agent_type == "procedure":
                node = self._create_procedure_node(file_path, analysis, confidence)
            else:
                self.logger.warning(f"Unknown agent type: {agent_type} for {file_path}")
                continue

            if node and self.add_node(node):
                nodes_added += 1

            # Log progress every 20 nodes or at the end
            if idx % 20 == 0 or idx == total_results:
                self.logger.info(f"  Progress: {idx}/{total_results} nodes processed")

        self.logger.info(f"Phase 1/2 complete: {nodes_added} nodes created")

        # Second pass: Create edges (relationships)
        self.logger.info(f"Phase 2/2: Extracting relationships from {total_results} results")
        for idx, (file_path, result) in enumerate(analysis_results.items(), 1):
            agent_type = result.get("agent", "unknown")
            analysis = result.get("analysis", {})

            # Extract relationships based on agent type
            if agent_type == "controller":
                edges_added += self._extract_controller_edges(file_path, analysis)
            elif agent_type == "jsp":
                edges_added += self._extract_jsp_edges(file_path, analysis)
            elif agent_type == "service":
                edges_added += self._extract_service_edges(file_path, analysis)
            elif agent_type == "mapper":
                edges_added += self._extract_mapper_edges(file_path, analysis)
            elif agent_type == "procedure":
                edges_added += self._extract_procedure_edges(file_path, analysis)

            # Log progress every 20 files or at the end
            if idx % 20 == 0 or idx == total_results:
                self.logger.info(f"  Progress: {idx}/{total_results} relationships extracted")

        self.logger.info(f"Phase 2/2 complete: {edges_added} edges created")
        self.logger.info(
            f"Graph built: {nodes_added} nodes added, {edges_added} edges added"
        )

        return nodes_added, edges_added

    def _create_controller_node(
        self,
        file_path: str,
        analysis: Dict[str, Any],
        confidence: float
    ) -> Optional[Node]:
        """Create node from controller analysis."""
        class_name = analysis.get("class_name", "unknown")
        package = analysis.get("package", "unknown")

        node_id = f"{package}.{class_name}" if package != "unknown" else class_name

        return Node(
            id=node_id,
            type=NodeType.CONTROLLER,
            name=class_name,
            file_path=file_path,
            metadata={
                "package": package,
                "controller_type": analysis.get("controller_type", "@Controller"),
                "mappings": analysis.get("mappings", []),
                "dependencies": analysis.get("dependencies", []),
                "confidence": confidence
            }
        )

    def _create_jsp_node(
        self,
        file_path: str,
        analysis: Dict[str, Any],
        confidence: float
    ) -> Optional[Node]:
        """Create node from JSP analysis."""
        file_name = analysis.get("file_name", Path(file_path).name)
        node_id = f"jsp:{file_name}"

        return Node(
            id=node_id,
            type=NodeType.JSP,
            name=file_name,
            file_path=file_path,
            metadata={
                "model_attributes": analysis.get("model_attributes", []),
                "forms": analysis.get("forms", []),
                "backend_dependencies": analysis.get("backend_dependencies", []),
                "confidence": confidence
            }
        )

    def _create_service_node(
        self,
        file_path: str,
        analysis: Dict[str, Any],
        confidence: float
    ) -> Optional[Node]:
        """Create node from service analysis."""
        class_name = analysis.get("class_name", "unknown")
        package = analysis.get("package", "unknown")

        node_id = f"{package}.{class_name}" if package != "unknown" else class_name

        return Node(
            id=node_id,
            type=NodeType.SERVICE,
            name=class_name,
            file_path=file_path,
            metadata={
                "package": package,
                "dependencies": analysis.get("dependencies", []),
                "methods": analysis.get("methods", []),
                "business_patterns": analysis.get("business_patterns", []),
                "confidence": confidence
            }
        )

    def _create_mapper_node(
        self,
        file_path: str,
        analysis: Dict[str, Any],
        confidence: float
    ) -> Optional[Node]:
        """Create node from mapper analysis."""
        namespace = analysis.get("namespace", "unknown")
        node_id = f"mapper:{namespace}"

        return Node(
            id=node_id,
            type=NodeType.MAPPER,
            name=namespace.split(".")[-1] if namespace != "unknown" else "unknown",
            file_path=file_path,
            metadata={
                "namespace": namespace,
                "statements": analysis.get("statements", []),
                "tables_accessed": analysis.get("tables_accessed", []),
                "confidence": confidence
            }
        )

    def _create_procedure_node(
        self,
        file_path: str,
        analysis: Dict[str, Any],
        confidence: float
    ) -> Optional[Node]:
        """Create node from procedure analysis."""
        procedure_name = analysis.get("procedure_name", "unknown")
        package_name = analysis.get("package_name")

        if package_name:
            node_id = f"{package_name}.{procedure_name}"
        else:
            node_id = f"procedure:{procedure_name}"

        return Node(
            id=node_id,
            type=NodeType.PROCEDURE,
            name=procedure_name,
            file_path=file_path,
            metadata={
                "package": package_name,
                "parameters": analysis.get("parameters", []),
                "tables_accessed": analysis.get("tables_accessed", []),
                "confidence": confidence
            }
        )

    def _extract_controller_edges(
        self,
        file_path: str,
        analysis: Dict[str, Any]
    ) -> int:
        """
        Extract edges from controller analysis.

        Extracts:
        - CALLS_SERVICE: Controller → Service dependencies
        - EXPOSES_ENDPOINT: Controller → Endpoint mappings
        - RENDERS_JSP: Controller → JSP views
        """
        edges_added = 0
        class_name = analysis.get("class_name", "unknown")
        package = analysis.get("package", "unknown")
        controller_id = f"{package}.{class_name}" if package != "unknown" else class_name

        # Dependencies → Services
        for dep in analysis.get("dependencies", []):
            dep_type = dep.get("type", "")
            dep_name = dep.get("field_name", "")

            if "Service" in dep_type:
                # Try multiple heuristics to find service node ID
                # 1. Full package + type name
                service_id = f"{package}.{dep_type}"

                # 2. If not found, try just the type name
                if service_id not in self.nodes:
                    service_id = dep_type

                # 3. If still not found, try with package from type if it contains '.'
                if service_id not in self.nodes and '.' in dep_type:
                    service_id = dep_type

                # Check if service node exists
                if service_id in self.nodes:
                    edge = Edge(
                        source=controller_id,
                        target=service_id,
                        type=EdgeType.CALLS_SERVICE,
                        metadata={"field_name": dep_name}
                    )
                    if self.add_edge(edge):
                        edges_added += 1

        # Mappings → Endpoints and JSPs
        for mapping in analysis.get("mappings", []):
            url = mapping.get("url", "")
            method = mapping.get("method", "GET")
            return_type = mapping.get("return_type", "")

            if url:
                # Create endpoint node if not exists
                endpoint_id = f"endpoint:{url}"
                if endpoint_id not in self.nodes:
                    endpoint_node = Node(
                        id=endpoint_id,
                        type=NodeType.ENDPOINT,
                        name=url,
                        file_path="",
                        metadata={"url": url, "method": method}
                    )
                    self.add_node(endpoint_node)

                # Create EXPOSES_ENDPOINT edge
                edge = Edge(
                    source=controller_id,
                    target=endpoint_id,
                    type=EdgeType.EXPOSES_ENDPOINT,
                    metadata={
                        "method": method,
                        "handler": mapping.get("method_name", "")
                    }
                )
                if self.add_edge(edge):
                    edges_added += 1

            # Check if returns a view (JSP)
            # Heuristic: return type is String, ModelAndView, or contains "view"
            if return_type in ["String", "ModelAndView"] or "view" in return_type.lower():
                view_name = mapping.get("return_value", "")

                if view_name and not view_name.startswith("redirect:"):
                    # Create JSP node ID (try to match existing JSP nodes)
                    jsp_id = f"jsp:{view_name}.jsp"

                    # Check variations
                    if jsp_id not in self.nodes:
                        jsp_id = f"jsp:{view_name}"

                    if jsp_id in self.nodes:
                        edge = Edge(
                            source=controller_id,
                            target=jsp_id,
                            type=EdgeType.RENDERS_JSP,
                            metadata={"view_name": view_name}
                        )
                        if self.add_edge(edge):
                            edges_added += 1

            # Extract model data flow
            # Parameters consumed
            for param in mapping.get("parameters", []):
                param_type = param.get("type", "")

                if self._is_custom_model(param_type):
                    model_id = f"model:{param_type}"

                    # Create model node if not exists
                    if model_id not in self.nodes:
                        model_node = Node(
                            id=model_id,
                            type=NodeType.MODEL,
                            name=param_type.split(".")[-1] if "." in param_type else param_type,
                            file_path="",
                            metadata={"full_name": param_type}
                        )
                        self.add_node(model_node)

                    # Create CONSUMES edge
                    edge = Edge(
                        source=controller_id,
                        target=model_id,
                        type=EdgeType.CONSUMES,
                        metadata={
                            "handler": mapping.get("method_name", ""),
                            "param": param.get("name", "")
                        }
                    )
                    if self.add_edge(edge):
                        edges_added += 1

            # Return type models produced (if not a view)
            if return_type not in ["String", "ModelAndView", "void"] and self._is_custom_model(return_type):
                model_id = f"model:{return_type}"

                # Create model node if not exists
                if model_id not in self.nodes:
                    model_node = Node(
                        id=model_id,
                        type=NodeType.MODEL,
                        name=return_type.split(".")[-1] if "." in return_type else return_type,
                        file_path="",
                        metadata={"full_name": return_type}
                    )
                    self.add_node(model_node)

                # Create PRODUCES edge
                edge = Edge(
                    source=controller_id,
                    target=model_id,
                    type=EdgeType.PRODUCES,
                    metadata={"handler": mapping.get("method_name", "")}
                )
                if self.add_edge(edge):
                    edges_added += 1

        return edges_added

    def _extract_jsp_edges(
        self,
        file_path: str,
        analysis: Dict[str, Any]
    ) -> int:
        """
        Extract edges from JSP analysis.

        Extracts:
        - SUBMITS_TO/AJAX_CALL: JSP → Endpoint
        - INCLUDES: JSP → JSP (includes/imports)
        - CONSUMES: JSP → Model (model attributes)
        """
        edges_added = 0
        file_name = analysis.get("file_name", Path(file_path).name)
        jsp_id = f"jsp:{file_name}"

        # Backend dependencies → Endpoints
        for dep in analysis.get("backend_dependencies", []):
            dep_type = dep.get("type")
            url = dep.get("url", "")

            if dep_type in ["controller-endpoint", "ajax-call"]:
                # Create endpoint node if not exists
                endpoint_id = f"endpoint:{url}"
                if endpoint_id not in self.nodes:
                    endpoint_node = Node(
                        id=endpoint_id,
                        type=NodeType.ENDPOINT,
                        name=url,
                        file_path="",
                        metadata={"url": url, "method": dep.get("method")}
                    )
                    self.add_node(endpoint_node)

                # Create edge
                edge_type = EdgeType.AJAX_CALL if dep_type == "ajax-call" else EdgeType.SUBMITS_TO
                edge = Edge(
                    source=jsp_id,
                    target=endpoint_id,
                    type=edge_type,
                    metadata={"purpose": dep.get("purpose")}
                )
                if self.add_edge(edge):
                    edges_added += 1

            elif dep_type == "jsp-include":
                # JSP includes another JSP
                included_jsp_name = dep.get("file", "")
                if included_jsp_name:
                    included_jsp_id = f"jsp:{included_jsp_name}"

                    # Check variations
                    if included_jsp_id not in self.nodes:
                        # Try without .jsp extension
                        if included_jsp_name.endswith(".jsp"):
                            included_jsp_id = f"jsp:{included_jsp_name[:-4]}"

                    if included_jsp_id in self.nodes:
                        edge = Edge(
                            source=jsp_id,
                            target=included_jsp_id,
                            type=EdgeType.INCLUDES,
                            metadata={"include_type": dep.get("include_type", "static")}
                        )
                        if self.add_edge(edge):
                            edges_added += 1

        # Model attributes consumed by JSP
        for attr in analysis.get("model_attributes", []):
            attr_name = attr.get("name", "")
            attr_type = attr.get("type", "")

            if attr_type and self._is_custom_model(attr_type):
                model_id = f"model:{attr_type}"

                # Create model node if not exists
                if model_id not in self.nodes:
                    model_node = Node(
                        id=model_id,
                        type=NodeType.MODEL,
                        name=attr_type.split(".")[-1] if "." in attr_type else attr_type,
                        file_path="",
                        metadata={"full_name": attr_type}
                    )
                    self.add_node(model_node)

                # Create CONSUMES edge
                edge = Edge(
                    source=jsp_id,
                    target=model_id,
                    type=EdgeType.CONSUMES,
                    metadata={"attribute_name": attr_name}
                )
                if self.add_edge(edge):
                    edges_added += 1

        return edges_added

    def _extract_service_edges(
        self,
        file_path: str,
        analysis: Dict[str, Any]
    ) -> int:
        """
        Extract edges from service analysis.

        Extracts:
        - USES_MAPPER: Service → Mapper/Repository dependencies
        - ORCHESTRATES: Service → Service dependencies
        - PRODUCES/CONSUMES: Service → Model data flow
        """
        edges_added = 0
        class_name = analysis.get("class_name", "unknown")
        package = analysis.get("package", "unknown")
        service_id = f"{package}.{class_name}" if package != "unknown" else class_name

        # Dependencies → Mappers or other Services
        for dep in analysis.get("dependencies", []):
            dep_type = dep.get("type", "")
            purpose = dep.get("purpose", "")
            field_name = dep.get("field_name", "")

            if purpose == "repository" or "Mapper" in dep_type or "Repository" in dep_type:
                # Try multiple heuristics to find mapper node ID
                mapper_id = None

                # 1. Try with mapper: prefix and full package
                candidate = f"mapper:{package}.{dep_type}"
                if candidate in self.nodes:
                    mapper_id = candidate

                # 2. Try with mapper: prefix and type name only
                if not mapper_id:
                    candidate = f"mapper:{dep_type}"
                    if candidate in self.nodes:
                        mapper_id = candidate

                # 3. Try extracting namespace if dep_type contains full path
                if not mapper_id and '.' in dep_type:
                    candidate = f"mapper:{dep_type}"
                    if candidate in self.nodes:
                        mapper_id = candidate

                if mapper_id:
                    edge = Edge(
                        source=service_id,
                        target=mapper_id,
                        type=EdgeType.USES_MAPPER,
                        metadata={"field_name": field_name}
                    )
                    if self.add_edge(edge):
                        edges_added += 1

            elif purpose == "service" or "Service" in dep_type:
                # Try multiple heuristics to find service node ID
                target_service_id = None

                # 1. Try with full package
                candidate = f"{package}.{dep_type}"
                if candidate in self.nodes and candidate != service_id:
                    target_service_id = candidate

                # 2. Try with just the type name
                if not target_service_id:
                    candidate = dep_type
                    if candidate in self.nodes and candidate != service_id:
                        target_service_id = candidate

                # 3. Try if dep_type already contains package
                if not target_service_id and '.' in dep_type:
                    candidate = dep_type
                    if candidate in self.nodes and candidate != service_id:
                        target_service_id = candidate

                if target_service_id:
                    edge = Edge(
                        source=service_id,
                        target=target_service_id,
                        type=EdgeType.ORCHESTRATES,
                        metadata={"field_name": field_name}
                    )
                    if self.add_edge(edge):
                        edges_added += 1

        # Extract method-level data flow (models produced/consumed)
        for method in analysis.get("methods", []):
            method_name = method.get("name", "")

            # Models consumed (method parameters)
            for param in method.get("parameters", []):
                param_type = param.get("type", "")

                # Check if it's a custom model (not primitive, not java.*, not org.springframework.*)
                if self._is_custom_model(param_type):
                    model_id = f"model:{param_type}"

                    # Create model node if not exists
                    if model_id not in self.nodes:
                        model_node = Node(
                            id=model_id,
                            type=NodeType.MODEL,
                            name=param_type.split(".")[-1] if "." in param_type else param_type,
                            file_path="",
                            metadata={"full_name": param_type}
                        )
                        self.add_node(model_node)

                    # Create CONSUMES edge
                    edge = Edge(
                        source=service_id,
                        target=model_id,
                        type=EdgeType.CONSUMES,
                        metadata={"method": method_name, "param": param.get("name", "")}
                    )
                    if self.add_edge(edge):
                        edges_added += 1

            # Models produced (return type)
            return_type = method.get("return_type", "")
            if self._is_custom_model(return_type):
                model_id = f"model:{return_type}"

                # Create model node if not exists
                if model_id not in self.nodes:
                    model_node = Node(
                        id=model_id,
                        type=NodeType.MODEL,
                        name=return_type.split(".")[-1] if "." in return_type else return_type,
                        file_path="",
                        metadata={"full_name": return_type}
                    )
                    self.add_node(model_node)

                # Create PRODUCES edge
                edge = Edge(
                    source=service_id,
                    target=model_id,
                    type=EdgeType.PRODUCES,
                    metadata={"method": method_name}
                )
                if self.add_edge(edge):
                    edges_added += 1

        return edges_added

    def _is_custom_model(self, type_name: str) -> bool:
        """
        Check if a type is a custom model/DTO (not primitive or framework class).

        Args:
            type_name: Fully qualified or simple type name

        Returns:
            True if it's likely a custom model
        """
        if not type_name:
            return False

        # Exclude primitives
        primitives = {"int", "long", "double", "float", "boolean", "char", "byte", "short", "void"}
        if type_name.lower() in primitives:
            return False

        # Exclude Java standard library
        if type_name.startswith("java.") or type_name.startswith("javax."):
            return False

        # Exclude Spring framework
        if type_name.startswith("org.springframework."):
            return False

        # Exclude common wrappers
        wrappers = {"String", "Integer", "Long", "Double", "Float", "Boolean", "Character", "Byte", "Short"}
        if type_name in wrappers:
            return False

        # Exclude collections
        if type_name.startswith("List") or type_name.startswith("Map") or type_name.startswith("Set"):
            return False

        # Likely a custom model
        return True

    def _extract_mapper_edges(
        self,
        file_path: str,
        analysis: Dict[str, Any]
    ) -> int:
        """
        Extract edges from mapper analysis.

        Extracts:
        - QUERIES_TABLE: Mapper → Database Table
        - EXECUTES_PROCEDURE: Mapper → Stored Procedure
        """
        edges_added = 0
        namespace = analysis.get("namespace", "unknown")
        mapper_id = f"mapper:{namespace}"

        # Tables accessed
        for table in analysis.get("tables_accessed", []):
            # Create table node if not exists
            table_id = f"table:{table}"
            if table_id not in self.nodes:
                table_node = Node(
                    id=table_id,
                    type=NodeType.DATABASE_TABLE,
                    name=table,
                    file_path="",
                    metadata={"table_name": table}
                )
                self.add_node(table_node)

            # Create edge
            edge = Edge(
                source=mapper_id,
                target=table_id,
                type=EdgeType.QUERIES_TABLE
            )
            if self.add_edge(edge):
                edges_added += 1

        # Stored procedures called
        for stmt in analysis.get("statements", []):
            stmt_type = stmt.get("type", "")
            procedure_name = stmt.get("procedure_name", "")

            if stmt_type == "procedure-call" and procedure_name:
                # Try to find procedure node with multiple heuristics
                procedure_id = None

                # 1. Try with package.procedure format (matches procedure_node creation)
                # Extract potential package from namespace
                if namespace != "unknown" and "." in namespace:
                    # Assume same package as mapper
                    package_parts = namespace.rsplit(".", 1)
                    if len(package_parts) == 2:
                        package = package_parts[0]
                        candidate = f"{package}.{procedure_name}"
                        if candidate in self.nodes:
                            procedure_id = candidate

                # 2. Try with procedure: prefix
                if not procedure_id:
                    candidate = f"procedure:{procedure_name}"
                    if candidate in self.nodes:
                        procedure_id = candidate

                # 3. Try exact procedure name
                if not procedure_id:
                    if procedure_name in self.nodes:
                        procedure_id = procedure_name

                if procedure_id:
                    edge = Edge(
                        source=mapper_id,
                        target=procedure_id,
                        type=EdgeType.EXECUTES_PROCEDURE,
                        metadata={"statement_id": stmt.get("id", "")}
                    )
                    if self.add_edge(edge):
                        edges_added += 1

        return edges_added

    def _extract_procedure_edges(
        self,
        file_path: str,
        analysis: Dict[str, Any]
    ) -> int:
        """Extract edges from procedure analysis."""
        edges_added = 0
        procedure_name = analysis.get("procedure_name", "unknown")
        package_name = analysis.get("package_name")

        if package_name:
            procedure_id = f"{package_name}.{procedure_name}"
        else:
            procedure_id = f"procedure:{procedure_name}"

        # Tables accessed by procedure
        for table in analysis.get("tables_accessed", []):
            # Create table node if not exists
            table_id = f"table:{table}"
            if table_id not in self.nodes:
                table_node = Node(
                    id=table_id,
                    type=NodeType.DATABASE_TABLE,
                    name=table,
                    metadata={"table_name": table}
                )
                self.add_node(table_node)

            # Create edge from procedure to table
            edge = Edge(
                source=procedure_id,
                target=table_id,
                type=EdgeType.QUERIES_TABLE
            )
            if self.add_edge(edge):
                edges_added += 1

        return edges_added

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get node by ID."""
        return self.nodes.get(node_id)

    def get_node_by_file_path(self, file_path: str) -> Optional[Node]:
        """
        Get node by file path using reverse index.

        Args:
            file_path: File path to look up

        Returns:
            Node object if found, None otherwise
        """
        node_id = self.file_index.get(file_path)
        if node_id:
            return self.nodes.get(node_id)
        return None

    def get_neighbors(
        self,
        node_id: str,
        direction: str = "outgoing",
        edge_type: Optional[EdgeType] = None
    ) -> List[Node]:
        """
        Get neighboring nodes.

        Args:
            node_id: Node ID
            direction: "outgoing", "incoming", or "both"
            edge_type: Optional filter by specific edge type

        Returns:
            List of neighbor nodes
        """
        if node_id not in self.graph:
            return []

        neighbor_ids = []

        if direction in ["outgoing", "both"]:
            for target in self.graph.successors(node_id):
                # MultiDiGraph: check each edge
                edges = self.graph[node_id][target]
                for edge_key, edge_data in edges.items():
                    if edge_type is None or edge_data.get("type") == edge_type.value:
                        neighbor_ids.append(target)
                        break  # Add target only once

        if direction in ["incoming", "both"]:
            for source in self.graph.predecessors(node_id):
                # MultiDiGraph: check each edge
                edges = self.graph[source][node_id]
                for edge_key, edge_data in edges.items():
                    if edge_type is None or edge_data.get("type") == edge_type.value:
                        if source not in neighbor_ids:  # Avoid duplicates
                            neighbor_ids.append(source)
                        break

        return [self.nodes[nid] for nid in neighbor_ids if nid in self.nodes]

    def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_length: Optional[int] = None
    ) -> List[List[Node]]:
        """
        Find all simple paths between two nodes.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            max_length: Maximum path length (None for unlimited)

        Returns:
            List of paths, where each path is a list of nodes
        """
        if source_id not in self.graph or target_id not in self.graph:
            return []

        try:
            if max_length:
                paths = nx.all_simple_paths(
                    self.graph,
                    source_id,
                    target_id,
                    cutoff=max_length
                )
            else:
                paths = nx.all_simple_paths(self.graph, source_id, target_id)

            # Convert to node objects
            result = []
            for path in paths:
                result.append([self.nodes[nid] for nid in path if nid in self.nodes])

            return result

        except nx.NetworkXNoPath:
            return []

    def find_shortest_path(
        self,
        source_id: str,
        target_id: str
    ) -> Optional[List[Node]]:
        """
        Find shortest path between two nodes.

        Args:
            source_id: Source node ID
            target_id: Target node ID

        Returns:
            List of nodes in shortest path, or None if no path exists
        """
        if source_id not in self.graph or target_id not in self.graph:
            return None

        try:
            path = nx.shortest_path(self.graph, source_id, target_id)
            return [self.nodes[nid] for nid in path if nid in self.nodes]
        except nx.NetworkXNoPath:
            return None

    def find_all_dependencies(
        self,
        node_id: str,
        max_depth: Optional[int] = None
    ) -> Set[Node]:
        """
        Find all dependencies of a node (transitive closure of outgoing edges).

        Args:
            node_id: Node ID to analyze
            max_depth: Maximum depth to traverse (None for unlimited)

        Returns:
            Set of all dependent nodes

        Raises:
            ValueError: If max_depth is negative
        """
        if max_depth is not None and max_depth < 0:
            raise ValueError(f"max_depth must be non-negative, got {max_depth}")

        if node_id not in self.graph:
            return set()

        dependencies = set()
        visited = set()
        queue = [(node_id, 0)]

        while queue:
            current_id, depth = queue.pop(0)

            if current_id in visited:
                continue

            visited.add(current_id)

            # Skip root node
            if current_id != node_id:
                if current_id in self.nodes:
                    dependencies.add(self.nodes[current_id])

            # Check depth limit
            if max_depth is not None and depth >= max_depth:
                continue

            # Add successors
            for successor in self.graph.successors(current_id):
                if successor not in visited:
                    queue.append((successor, depth + 1))

        return dependencies

    def find_all_dependents(
        self,
        node_id: str,
        max_depth: Optional[int] = None
    ) -> Set[Node]:
        """
        Find all dependents of a node (reverse transitive closure).

        Args:
            node_id: Node ID to analyze
            max_depth: Maximum depth to traverse (None for unlimited)

        Returns:
            Set of all dependent nodes (nodes that depend on this node)

        Raises:
            ValueError: If max_depth is negative
        """
        if max_depth is not None and max_depth < 0:
            raise ValueError(f"max_depth must be non-negative, got {max_depth}")

        if node_id not in self.graph:
            return set()

        dependents = set()
        visited = set()
        queue = [(node_id, 0)]

        while queue:
            current_id, depth = queue.pop(0)

            if current_id in visited:
                continue

            visited.add(current_id)

            # Skip root node
            if current_id != node_id:
                if current_id in self.nodes:
                    dependents.add(self.nodes[current_id])

            # Check depth limit
            if max_depth is not None and depth >= max_depth:
                continue

            # Add predecessors
            for predecessor in self.graph.predecessors(current_id):
                if predecessor not in visited:
                    queue.append((predecessor, depth + 1))

        return dependents

    def analyze_impact(
        self,
        node_id: str,
        max_depth: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze impact of changing a node.

        Returns both dependencies and dependents to show full impact.

        Args:
            node_id: Node ID to analyze
            max_depth: Maximum depth to traverse (None for unlimited)

        Returns:
            Dictionary with impact analysis:
            {
                "node": Node,
                "direct_dependencies": List[Node],
                "all_dependencies": Set[Node],
                "direct_dependents": List[Node],
                "all_dependents": Set[Node],
                "impact_score": float  # Total affected nodes
            }
        """
        if node_id not in self.nodes:
            return {}

        node = self.nodes[node_id]
        direct_deps = self.get_neighbors(node_id, direction="outgoing")
        all_deps = self.find_all_dependencies(node_id, max_depth)
        direct_dependents = self.get_neighbors(node_id, direction="incoming")
        all_dependents = self.find_all_dependents(node_id, max_depth)

        return {
            "node": node,
            "direct_dependencies": direct_deps,
            "all_dependencies": all_deps,
            "direct_dependents": direct_dependents,
            "all_dependents": all_dependents,
            "impact_score": len(all_deps) + len(all_dependents)
        }

    def extract_subgraph(
        self,
        node_ids: List[str],
        include_neighbors: bool = False
    ) -> nx.MultiDiGraph:
        """
        Extract a subgraph containing specified nodes.

        Args:
            node_ids: List of node IDs to include
            include_neighbors: If True, also include direct neighbors

        Returns:
            NetworkX MultiDiGraph subgraph
        """
        nodes_to_include = set(node_ids)

        if include_neighbors:
            for node_id in node_ids:
                if node_id in self.graph:
                    nodes_to_include.update(self.graph.successors(node_id))
                    nodes_to_include.update(self.graph.predecessors(node_id))

        return self.graph.subgraph(nodes_to_include).copy()

    def query_by_type(
        self,
        node_type: NodeType,
        limit: Optional[int] = None
    ) -> List[Node]:
        """
        Find all nodes of a specific type.

        Args:
            node_type: Node type to query
            limit: Maximum number of results (None for all)

        Returns:
            List of matching nodes
        """
        results = [
            node for node in self.nodes.values()
            if node.type == node_type
        ]

        if limit:
            return results[:limit]

        return results

    def query_by_metadata(
        self,
        **criteria
    ) -> List[Node]:
        """
        Find nodes matching metadata criteria.

        Args:
            **criteria: Key-value pairs to match in node metadata

        Returns:
            List of matching nodes

        Example:
            query_by_metadata(package="com.example.service", confidence=0.9)
        """
        results = []

        for node in self.nodes.values():
            match = True
            for key, value in criteria.items():
                if key not in node.metadata or node.metadata[key] != value:
                    match = False
                    break

            if match:
                results.append(node)

        return results

    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive graph statistics.

        Returns:
            Dictionary with node counts, edge counts, connectivity metrics, etc.
        """
        node_counts = {}
        for node_type in NodeType:
            node_counts[node_type.value] = sum(
                1 for n in self.nodes.values() if n.type == node_type
            )

        edge_counts = {}
        for edge_type in EdgeType:
            edge_counts[edge_type.value] = sum(
                1 for _, _, data in self.graph.edges(data=True)
                if data.get("type") == edge_type.value
            )

        # Find orphan nodes (nodes with no edges)
        orphan_nodes = [
            node_id for node_id in self.graph.nodes()
            if self.graph.degree(node_id) == 0
        ]

        # Calculate average degree
        if len(self.nodes) > 0:
            avg_degree = sum(dict(self.graph.degree()).values()) / len(self.nodes)
        else:
            avg_degree = 0.0

        # Strongly connected components (for understanding circular dependencies)
        # Note: For directed graphs, we use weakly connected components
        num_weakly_connected = nx.number_weakly_connected_components(self.graph)
        largest_wcc_size = len(max(
            nx.weakly_connected_components(self.graph), default=[], key=len
        ))

        # Check for cycles (limit to prevent exponential time on large graphs)
        try:
            # Limit cycle detection for performance - only check first 1000 cycles
            cycles_iter = nx.simple_cycles(self.graph)
            cycles = list(itertools.islice(cycles_iter, 1000))
            has_cycles = len(cycles) > 0
            num_cycles = len(cycles) if len(cycles) < 1000 else "1000+"
        except (nx.NetworkXError, MemoryError, RecursionError) as e:
            # Graph may be too large or complex for cycle detection
            self.logger.warning(f"Cycle detection failed: {e}")
            has_cycles = False
            num_cycles = 0

        return {
            "total_nodes": len(self.nodes),
            "total_edges": self.graph.number_of_edges(),
            "node_counts": node_counts,
            "edge_counts": edge_counts,
            "density": nx.density(self.graph) if len(self.nodes) > 1 else 0.0,
            "average_degree": avg_degree,
            "orphan_nodes": len(orphan_nodes),
            "orphan_node_ids": orphan_nodes[:10],  # First 10 for reference
            "weakly_connected_components": num_weakly_connected,
            "largest_component_size": largest_wcc_size,
            "has_cycles": has_cycles,
            "num_cycles": num_cycles
        }

    def save_graph(self, output_path: str, format: str = "graphml"):
        """
        Save graph to disk in specified format.

        Args:
            output_path: Path to output file
            format: Output format - "graphml", "gexf", "json", "pickle", "dot", "d3", "cytoscape"

        Raises:
            ValueError: If format is not supported
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if format == "graphml":
            nx.write_graphml(self.graph, str(path))
            self.logger.info(f"Graph saved to {path} (GraphML format)")

        elif format == "gexf":
            nx.write_gexf(self.graph, str(path))
            self.logger.info(f"Graph saved to {path} (GEXF format)")

        elif format == "json":
            # Save as node-link JSON format
            data = nx.node_link_data(self.graph)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            self.logger.info(f"Graph saved to {path} (JSON format)")

        elif format == "pickle":
            nx.write_gpickle(self.graph, str(path))
            self.logger.info(f"Graph saved to {path} (Pickle format)")

        elif format == "dot":
            self.export_dot(str(path))
            self.logger.info(f"Graph saved to {path} (DOT format)")

        elif format == "d3":
            self.export_d3_json(str(path))
            self.logger.info(f"Graph saved to {path} (D3.js JSON format)")

        elif format == "cytoscape":
            self.export_cytoscape_json(str(path))
            self.logger.info(f"Graph saved to {path} (Cytoscape.js JSON format)")

        else:
            raise ValueError(
                f"Unsupported format: {format}. "
                "Supported formats: graphml, gexf, json, pickle, dot, d3, cytoscape"
            )

    def load_graph(self, input_path: str, format: str = "graphml"):
        """
        Load graph from disk in specified format.

        This replaces the current graph with the loaded one.

        Args:
            input_path: Path to input file
            format: Input format - "graphml", "gexf", "json", or "pickle"

        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If format is not supported
        """
        path = Path(input_path)

        if not path.exists():
            raise FileNotFoundError(f"Graph file not found: {input_path}")

        if format == "graphml":
            self.graph = nx.read_graphml(str(path))
            self.logger.info(f"Graph loaded from {path} (GraphML format)")

        elif format == "gexf":
            self.graph = nx.read_gexf(str(path))
            self.logger.info(f"Graph loaded from {path} (GEXF format)")

        elif format == "json":
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.graph = nx.node_link_graph(data, multigraph=True, directed=True)
            self.logger.info(f"Graph loaded from {path} (JSON format)")

        elif format == "pickle":
            self.graph = nx.read_gpickle(str(path))
            self.logger.info(f"Graph loaded from {path} (Pickle format)")

        else:
            raise ValueError(
                f"Unsupported format: {format}. "
                "Supported formats: graphml, gexf, json, pickle"
            )

        # Rebuild nodes dictionary and file_index from graph
        self._rebuild_indices()

    def export_dot(self, output_path: str):
        """
        Export graph to DOT format for Graphviz visualization.

        Args:
            output_path: Path to output .dot file
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Use NetworkX's to_agraph if pygraphviz is available, otherwise write manually
        try:
            from networkx.drawing.nx_agraph import write_dot
            write_dot(self.graph, str(path))
        except ImportError:
            # Manual DOT generation
            with open(path, 'w', encoding='utf-8') as f:
                f.write("digraph SpringMVC {\n")
                f.write("  rankdir=LR;\n")
                f.write("  node [shape=box, style=rounded];\n\n")

                # Write nodes with styling based on type
                node_colors = {
                    "controller": "#FF6B6B",
                    "jsp": "#4ECDC4",
                    "service": "#45B7D1",
                    "mapper": "#FFA07A",
                    "procedure": "#98D8C8",
                    "endpoint": "#F7DC6F",
                    "model": "#BB8FCE",
                    "table": "#85C1E2"
                }

                for node_id, node_data in self.graph.nodes(data=True):
                    node_type = node_data.get("type", "unknown")
                    color = node_colors.get(node_type, "#CCCCCC")
                    label = node_data.get("name", node_id)

                    f.write(f'  "{node_id}" [label="{label}", fillcolor="{color}", style=filled];\n')

                f.write("\n")

                # Write edges with labels
                for source, target, edge_key, edge_data in self.graph.edges(data=True, keys=True):
                    edge_type = edge_data.get("type", "")
                    f.write(f'  "{source}" -> "{target}" [label="{edge_type}"];\n')

                f.write("}\n")

    def export_d3_json(self, output_path: str):
        """
        Export graph to D3.js-friendly JSON format.

        Args:
            output_path: Path to output .json file
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Build D3 force-directed graph format
        nodes = []
        links = []

        # Create node index mapping
        node_index = {node_id: idx for idx, node_id in enumerate(self.graph.nodes())}

        # Add nodes with full metadata
        for node_id in self.graph.nodes():
            node = self.nodes.get(node_id)
            if node:
                nodes.append({
                    "id": node.id,
                    "name": node.name,
                    "type": node.type.value,
                    "file_path": node.file_path,
                    "metadata": node.metadata
                })

        # Add links (edges)
        for source, target, edge_key, edge_data in self.graph.edges(data=True, keys=True):
            links.append({
                "source": node_index[source],
                "target": node_index[target],
                "type": edge_data.get("type", ""),
                "metadata": {k: v for k, v in edge_data.items() if k != "type"}
            })

        data = {
            "nodes": nodes,
            "links": links,
            "metadata": {
                "total_nodes": len(nodes),
                "total_links": len(links),
                "graph_stats": self.get_stats()
            }
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def export_cytoscape_json(self, output_path: str):
        """
        Export graph to Cytoscape.js JSON format.

        Args:
            output_path: Path to output .json file
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        elements = []

        # Add nodes
        for node_id in self.graph.nodes():
            node = self.nodes.get(node_id)
            if node:
                elements.append({
                    "data": {
                        "id": node.id,
                        "label": node.name,
                        "type": node.type.value,
                        "file_path": node.file_path,
                        **node.metadata
                    },
                    "group": "nodes",
                    "classes": node.type.value
                })

        # Add edges
        edge_id = 0
        for source, target, edge_key, edge_data in self.graph.edges(data=True, keys=True):
            elements.append({
                "data": {
                    "id": f"e{edge_id}",
                    "source": source,
                    "target": target,
                    "label": edge_data.get("type", ""),
                    "type": edge_data.get("type", ""),
                    **{k: v for k, v in edge_data.items() if k != "type"}
                },
                "group": "edges",
                "classes": edge_data.get("type", "")
            })
            edge_id += 1

        data = {
            "elements": elements,
            "metadata": self.get_stats()
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def _rebuild_indices(self):
        """
        Rebuild nodes dictionary and file_index from loaded graph.

        Called after loading a graph from disk to reconstruct in-memory structures.
        """
        self.nodes.clear()
        self.file_index.clear()

        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]

            # Reconstruct Node object
            node = Node(
                id=node_id,
                type=NodeType(node_data.get("type", "unknown")),
                name=node_data.get("name", node_id),
                file_path=node_data.get("file_path", ""),
                metadata={
                    k: v for k, v in node_data.items()
                    if k not in ["type", "name", "file_path"]
                }
            )

            self.nodes[node_id] = node

            # Update file_index
            if node.file_path:
                self.file_index[node.file_path] = node_id

        self.logger.info(
            f"Indices rebuilt: {len(self.nodes)} nodes, {len(self.file_index)} file mappings"
        )

    def diff_graphs(self, other: 'GraphBuilder') -> Dict[str, Any]:
        """
        Compare this graph with another graph to find differences.

        Args:
            other: Another GraphBuilder instance to compare against

        Returns:
            Dictionary containing:
            {
                "nodes_added": List[str],  # Node IDs in other but not in self
                "nodes_removed": List[str],  # Node IDs in self but not in other
                "nodes_modified": List[Dict],  # Nodes with changed metadata
                "edges_added": List[Dict],  # Edges in other but not in self
                "edges_removed": List[Dict],  # Edges in self but not in other
                "summary": {
                    "total_changes": int,
                    "has_changes": bool
                }
            }
        """
        diff = {
            "nodes_added": [],
            "nodes_removed": [],
            "nodes_modified": [],
            "edges_added": [],
            "edges_removed": []
        }

        # Compare nodes
        self_node_ids = set(self.nodes.keys())
        other_node_ids = set(other.nodes.keys())

        # Nodes added in other
        diff["nodes_added"] = list(other_node_ids - self_node_ids)

        # Nodes removed in other
        diff["nodes_removed"] = list(self_node_ids - other_node_ids)

        # Check for modified nodes (same ID but different metadata)
        common_nodes = self_node_ids & other_node_ids
        for node_id in common_nodes:
            self_node = self.nodes[node_id]
            other_node = other.nodes[node_id]

            # Compare metadata
            if self_node.metadata != other_node.metadata:
                diff["nodes_modified"].append({
                    "node_id": node_id,
                    "old_metadata": self_node.metadata,
                    "new_metadata": other_node.metadata
                })

        # Compare edges
        self_edges = set()
        for u, v, key, data in self.graph.edges(keys=True, data=True):
            self_edges.add((u, v, data.get("type")))

        other_edges = set()
        for u, v, key, data in other.graph.edges(keys=True, data=True):
            other_edges.add((u, v, data.get("type")))

        # Edges added
        for edge in other_edges - self_edges:
            diff["edges_added"].append({
                "source": edge[0],
                "target": edge[1],
                "type": edge[2]
            })

        # Edges removed
        for edge in self_edges - other_edges:
            diff["edges_removed"].append({
                "source": edge[0],
                "target": edge[1],
                "type": edge[2]
            })

        # Summary
        total_changes = (
            len(diff["nodes_added"]) +
            len(diff["nodes_removed"]) +
            len(diff["nodes_modified"]) +
            len(diff["edges_added"]) +
            len(diff["edges_removed"])
        )

        diff["summary"] = {
            "total_changes": total_changes,
            "has_changes": total_changes > 0,
            "nodes_changed": len(diff["nodes_added"]) + len(diff["nodes_removed"]) + len(diff["nodes_modified"]),
            "edges_changed": len(diff["edges_added"]) + len(diff["edges_removed"])
        }

        return diff

    def clear_old_results(self, max_age_seconds: int = 3600):
        """
        Clear analysis results older than specified age.

        This method can be used to free memory when analysis results
        are no longer needed.

        Args:
            max_age_seconds: Maximum age of results to keep (default: 1 hour)

        Note:
            This is a placeholder for future implementation when timestamp
            tracking is added to nodes.
        """
        # Future enhancement: Track node creation timestamps and remove old ones
        self.logger.info(
            f"clear_old_results called with max_age={max_age_seconds}s "
            "(not yet implemented - requires timestamp tracking)"
        )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<GraphBuilder("
            f"nodes={len(self.nodes)}, "
            f"edges={self.graph.number_of_edges()}"
            f")>"
        )
