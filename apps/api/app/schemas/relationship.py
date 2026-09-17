from pydantic import BaseModel


class CharacterNode(BaseModel):
    id: str
    name: str
    rank: str | None = None
    alive: bool


class RelationshipEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    active: bool


class RelationshipGraphResponse(BaseModel):
    nodes: list[CharacterNode]
    edges: list[RelationshipEdge]


class CharacterGraphResponse(BaseModel):
    root_character_id: str
    chapter: int
    depth: int
    nodes: list[CharacterNode]
    edges: list[RelationshipEdge]


class RelationshipHistoryEvent(BaseModel):
    chapter: int
    type: str


class RelationshipHistoryResponse(BaseModel):
    source_id: str
    target_id: str
    history: list[RelationshipHistoryEvent]
