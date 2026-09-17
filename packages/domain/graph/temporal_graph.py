from dataclasses import dataclass

from .graph_edge import GraphEdge
from .graph_node import GraphNode


@dataclass(frozen=True)
class TemporalGraph:
    reader_chapter: int
    nodes: list[GraphNode]
    edges: list[GraphEdge]
