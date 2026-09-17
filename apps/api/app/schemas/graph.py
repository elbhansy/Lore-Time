from pydantic import BaseModel


class GraphNodeDTO(BaseModel):
    id: str
    type: str
    label: str
    metadata: dict | None = None


class GraphEdgeDTO(BaseModel):
    source_id: str
    target_id: str
    type: str
    metadata: dict | None = None


class TemporalGraphDTO(BaseModel):
    reader_chapter: int
    nodes: list[GraphNodeDTO]
    edges: list[GraphEdgeDTO]
