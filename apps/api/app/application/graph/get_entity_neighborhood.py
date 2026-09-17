import uuid

from packages.domain.graph.graph_edge import GraphEdge
from packages.domain.graph.temporal_graph import TemporalGraph

from .get_temporal_graph import GetTemporalGraphUseCase


class GetEntityNeighborhoodUseCase:
    def __init__(self, get_temporal_graph_uc: GetTemporalGraphUseCase):
        self.get_temporal_graph_uc = get_temporal_graph_uc

    def execute(
        self, series_id: uuid.UUID, entity_id: str, chapter: int, depth: int = 1
    ) -> TemporalGraph:
        # First, generate the full valid graph
        full_graph = self.get_temporal_graph_uc.execute(series_id, chapter)

        # Then, perform BFS to extract the neighborhood
        visited_nodes: set[str] = set([entity_id])
        current_level: set[str] = set([entity_id])

        valid_edges: list[GraphEdge] = []

        for _ in range(depth):
            next_level = set()
            for edge in full_graph.edges:
                if (
                    edge.source_id in current_level
                    and edge.target_id not in visited_nodes
                ):
                    valid_edges.append(edge)
                    next_level.add(edge.target_id)
                elif (
                    edge.target_id in current_level
                    and edge.source_id not in visited_nodes
                ):
                    valid_edges.append(edge)
                    next_level.add(edge.source_id)
                elif (
                    edge.source_id in current_level and edge.target_id in current_level
                ):
                    # Capture edges between nodes in the same level to avoid missing internal connections
                    if edge not in valid_edges:
                        valid_edges.append(edge)

            visited_nodes.update(next_level)
            current_level = next_level

        # Extract valid nodes
        valid_nodes = [n for n in full_graph.nodes if n.id in visited_nodes]

        return TemporalGraph(
            reader_chapter=chapter, nodes=valid_nodes, edges=valid_edges
        )
