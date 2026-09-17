from dataclasses import dataclass

from .node_type import NodeType


@dataclass(frozen=True)
class GraphNode:
    id: str
    type: NodeType
    label: str
    metadata: dict | None = None
