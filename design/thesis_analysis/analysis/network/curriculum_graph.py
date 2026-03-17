"""
Network analysis of curriculum structure.

Builds and analyzes graphs of course co-occurrence and
competency-course mappings.
"""

from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
from pathlib import Path

import pandas as pd
import numpy as np

from ...config import settings
from ...data_processing.ukrainian_nlp import normalize_course_name


@dataclass
class NetworkMetrics:
    """Network-level metrics."""

    num_nodes: int
    num_edges: int
    density: float
    avg_degree: float
    avg_clustering: float
    num_components: int
    largest_component_size: int
    diameter: Optional[int] = None


@dataclass
class NodeMetrics:
    """Node-level centrality metrics."""

    node: str
    degree: int
    degree_centrality: float
    betweenness_centrality: float
    closeness_centrality: float
    eigenvector_centrality: float
    clustering_coefficient: float
    community: int = -1


@dataclass
class CommunityInfo:
    """Information about detected community."""

    community_id: int
    size: int
    members: List[str]
    top_nodes: List[Tuple[str, float]]  # (node, degree)
    label: str = ""


@dataclass
class GraphAnalysisResult:
    """Complete graph analysis results."""

    network_metrics: NetworkMetrics
    node_metrics: List[NodeMetrics]
    communities: List[CommunityInfo]
    edge_list: List[Tuple[str, str, float]]


class CurriculumGraphAnalyzer:
    """Analyzes curriculum structure as a network."""

    def __init__(
        self,
        min_edge_weight: int = 2,
        normalize_names: bool = True,
    ):
        self.min_edge_weight = min_edge_weight
        self.normalize_names = normalize_names
        self._graph = None

    def build_course_cooccurrence_graph(
        self,
        df_courses: pd.DataFrame,
    ):
        """
        Build graph where edges represent course co-occurrence in programs.

        Nodes: Unique courses
        Edges: Weighted by number of programs containing both courses
        """
        try:
            import networkx as nx
        except ImportError:
            raise ImportError("networkx not installed. Run: pip install networkx")

        # Group courses by program
        programs = df_courses.groupby("case_id")["name"].apply(list).to_dict()

        # Count co-occurrences
        cooccurrence = defaultdict(int)

        for case_id, courses in programs.items():
            # Normalize course names
            if self.normalize_names:
                courses = [normalize_course_name(c) for c in courses]

            # Remove empty strings and duplicates within program
            courses = list(set(c for c in courses if c and c.strip()))

            # Count pairs
            for i, c1 in enumerate(courses):
                for c2 in courses[i + 1:]:
                    pair = tuple(sorted([c1, c2]))
                    cooccurrence[pair] += 1

        # Build graph
        G = nx.Graph()

        # Add nodes (all unique courses, excluding empty strings)
        all_courses = set()
        for courses in programs.values():
            if self.normalize_names:
                courses = [normalize_course_name(c) for c in courses]
            all_courses.update(c for c in courses if c and c.strip())

        G.add_nodes_from(all_courses)

        # Add edges with weight filter
        for (c1, c2), weight in cooccurrence.items():
            if weight >= self.min_edge_weight:
                G.add_edge(c1, c2, weight=weight)

        self._graph = G
        return G

    def build_competency_graph(
        self,
        df_competencies: pd.DataFrame,
        df_courses: pd.DataFrame,
    ):
        """
        Build bipartite graph of competencies and courses.

        Nodes: Competencies (one partition) + Courses (other partition)
        Edges: Competency is covered by Course
        """
        try:
            import networkx as nx
        except ImportError:
            raise ImportError("networkx not installed")

        G = nx.Graph()

        # Add competency nodes
        competencies = df_competencies["code"].unique()
        for comp in competencies:
            G.add_node(comp, bipartite=0, node_type="competency")

        # Add course nodes
        courses = df_courses["name"].unique()
        for course in courses:
            name = normalize_course_name(course) if self.normalize_names else course
            G.add_node(name, bipartite=1, node_type="course")

        # Add edges from competency mappings
        # This would require competency-course mapping data from Tab 14
        # For now, we create a placeholder structure

        self._graph = G
        return G

    def analyze(self) -> GraphAnalysisResult:
        """Perform comprehensive network analysis."""
        import networkx as nx

        if self._graph is None:
            raise ValueError("No graph built. Call build_*_graph first.")

        G = self._graph

        # Network-level metrics
        network_metrics = self._compute_network_metrics(G)

        # Node-level metrics
        node_metrics = self._compute_node_metrics(G)

        # Community detection
        communities = self._detect_communities(G)

        # Edge list
        edge_list = [
            (u, v, d.get("weight", 1.0))
            for u, v, d in G.edges(data=True)
        ]

        return GraphAnalysisResult(
            network_metrics=network_metrics,
            node_metrics=node_metrics,
            communities=communities,
            edge_list=edge_list,
        )

    def _compute_network_metrics(self, G) -> NetworkMetrics:
        """Compute network-level metrics."""
        import networkx as nx

        num_nodes = G.number_of_nodes()
        num_edges = G.number_of_edges()

        if num_nodes == 0:
            return NetworkMetrics(0, 0, 0, 0, 0, 0, 0)

        density = nx.density(G)
        avg_degree = 2 * num_edges / num_nodes if num_nodes > 0 else 0

        # Clustering coefficient
        try:
            avg_clustering = nx.average_clustering(G)
        except Exception:
            avg_clustering = 0

        # Connected components
        if G.is_directed():
            components = list(nx.weakly_connected_components(G))
        else:
            components = list(nx.connected_components(G))

        num_components = len(components)
        largest_component_size = max(len(c) for c in components) if components else 0

        # Diameter (only for connected graphs)
        diameter = None
        if num_components == 1 and num_nodes > 1:
            try:
                diameter = nx.diameter(G)
            except Exception:
                pass

        return NetworkMetrics(
            num_nodes=num_nodes,
            num_edges=num_edges,
            density=density,
            avg_degree=avg_degree,
            avg_clustering=avg_clustering,
            num_components=num_components,
            largest_component_size=largest_component_size,
            diameter=diameter,
        )

    def _compute_node_metrics(self, G) -> List[NodeMetrics]:
        """Compute centrality metrics for all nodes."""
        import networkx as nx

        if G.number_of_nodes() == 0:
            return []

        # Compute centralities
        degree = dict(G.degree())
        degree_centrality = nx.degree_centrality(G)

        try:
            betweenness = nx.betweenness_centrality(G)
        except Exception:
            betweenness = {n: 0 for n in G.nodes()}

        try:
            closeness = nx.closeness_centrality(G)
        except Exception:
            closeness = {n: 0 for n in G.nodes()}

        try:
            eigenvector = nx.eigenvector_centrality(G, max_iter=1000)
        except Exception:
            eigenvector = {n: 0 for n in G.nodes()}

        clustering = nx.clustering(G)

        # Build node metrics list
        metrics = []
        for node in G.nodes():
            metrics.append(NodeMetrics(
                node=node,
                degree=degree[node],
                degree_centrality=degree_centrality[node],
                betweenness_centrality=betweenness[node],
                closeness_centrality=closeness[node],
                eigenvector_centrality=eigenvector[node],
                clustering_coefficient=clustering[node],
            ))

        # Sort by degree
        metrics.sort(key=lambda x: x.degree, reverse=True)

        return metrics

    def _detect_communities(self, G) -> List[CommunityInfo]:
        """Detect communities using Louvain algorithm."""
        import networkx as nx

        if G.number_of_nodes() == 0:
            return []

        try:
            import community as community_louvain
            partition = community_louvain.best_partition(G)
        except ImportError:
            # Fallback to greedy modularity
            try:
                from networkx.algorithms.community import greedy_modularity_communities
                communities_gen = greedy_modularity_communities(G)
                partition = {}
                for idx, comm in enumerate(communities_gen):
                    for node in comm:
                        partition[node] = idx
            except Exception:
                return []

        # Group nodes by community
        comm_members = defaultdict(list)
        for node, comm_id in partition.items():
            comm_members[comm_id].append(node)

        # Build community info
        communities = []
        degree = dict(G.degree())

        for comm_id, members in comm_members.items():
            # Sort members by degree
            sorted_members = sorted(members, key=lambda x: degree[x], reverse=True)
            top_nodes = [(n, degree[n]) for n in sorted_members[:5]]

            # Generate label from top nodes
            label = ", ".join(n[:20] for n, _ in top_nodes[:3])

            communities.append(CommunityInfo(
                community_id=comm_id,
                size=len(members),
                members=members,
                top_nodes=top_nodes,
                label=label,
            ))

        # Sort by size
        communities.sort(key=lambda x: x.size, reverse=True)

        return communities

    def get_top_courses(self, n: int = 20) -> List[Tuple[str, int]]:
        """Get courses with highest degree (most co-occurrences)."""
        if self._graph is None:
            return []

        degree = dict(self._graph.degree())
        sorted_courses = sorted(degree.items(), key=lambda x: x[1], reverse=True)
        return sorted_courses[:n]

    def get_course_neighbors(self, course: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """Get courses most commonly paired with given course."""
        if self._graph is None:
            return []

        if self.normalize_names:
            course = normalize_course_name(course)

        if course not in self._graph:
            return []

        neighbors = []
        for neighbor in self._graph.neighbors(course):
            weight = self._graph[course][neighbor].get("weight", 1)
            neighbors.append((neighbor, weight))

        neighbors.sort(key=lambda x: x[1], reverse=True)
        return neighbors[:top_n]

    def export_for_visualization(self, output_path: Path) -> None:
        """Export graph data for external visualization (Gephi, etc.)."""
        import networkx as nx

        if self._graph is None:
            return

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Export as GEXF (Gephi format)
        nx.write_gexf(self._graph, output_path.with_suffix(".gexf"))

        # Export as edge list CSV
        edges = []
        for u, v, d in self._graph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "weight": d.get("weight", 1),
            })

        pd.DataFrame(edges).to_csv(
            output_path.with_suffix(".csv"),
            index=False,
        )

    def generate_report(self, result: GraphAnalysisResult) -> str:
        """Generate text report of network analysis (English only)."""
        lines = []
        lines.append("=" * 60)
        lines.append("CURRICULUM NETWORK ANALYSIS REPORT")
        lines.append("Ukrainian Design Education Programs (022)")
        lines.append("=" * 60)

        nm = result.network_metrics
        lines.append("\n## NETWORK OVERVIEW\n")
        lines.append(f"Nodes (courses): {nm.num_nodes}")
        lines.append(f"Edges (co-occurrences): {nm.num_edges}")
        lines.append(f"Density: {nm.density:.4f}")
        lines.append(f"Average degree: {nm.avg_degree:.2f}")
        lines.append(f"Average clustering coefficient: {nm.avg_clustering:.4f}")
        lines.append(f"Connected components: {nm.num_components}")
        lines.append(f"Largest component size: {nm.largest_component_size} nodes")
        if nm.diameter:
            lines.append(f"Diameter: {nm.diameter}")

        lines.append("\n## TOP CENTRAL COURSES (by degree)\n")
        lines.append("  Deg | Betweenness | Course Name (English)")
        lines.append("  " + "-" * 50)
        for node_m in result.node_metrics[:15]:
            english_name = self._translate_course_name(node_m.node)
            lines.append(
                f"  {node_m.degree:3d} | {node_m.betweenness_centrality:.4f}    | "
                f"{english_name[:40]}"
            )

        lines.append("\n## COMMUNITY DETECTION (Louvain)\n")
        for i, comm in enumerate(result.communities[:10], 1):
            # Translate top course names
            top_courses_en = [self._translate_course_name(n) for n, _ in comm.top_nodes[:3]]
            label_en = ", ".join(top_courses_en)
            lines.append(f"\nCommunity {i} ({comm.size} courses):")
            lines.append(f"  Representative courses: {label_en}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)

    def _translate_course_name(self, name: str) -> str:
        """Translate Ukrainian course name to English."""
        if not name:
            return ""

        # Import translation dict
        from ...visualization.plots import COURSE_TRANSLATIONS

        name_lower = name.lower().strip()

        # Direct match
        if name_lower in COURSE_TRANSLATIONS:
            return COURSE_TRANSLATIONS[name_lower]

        # Partial match
        for uk, en in COURSE_TRANSLATIONS.items():
            if uk in name_lower:
                return en

        # Check if already English
        if all(ord(c) < 128 or c in ' -_' for c in name):
            return name.title()

        return name[:30] + "..." if len(name) > 30 else name
