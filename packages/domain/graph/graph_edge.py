from dataclasses import dataclass

from .edge_type import EdgeType


@dataclass(frozen=True)
class GraphEdge:
    source_id: str
    target_id: str
    type: EdgeType
    metadata: dict | None = None
