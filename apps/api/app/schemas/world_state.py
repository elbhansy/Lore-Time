import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict

from .character import CharacterStateResponse


class RelationshipStateResponse(BaseModel):
    subject_id: uuid.UUID
    target_id: uuid.UUID
    relationship_type: str
    active: bool

    model_config = ConfigDict(from_attributes=True)


class WorldStateResponse(BaseModel):
    series_id: uuid.UUID
    chapter: int
    characters: dict[uuid.UUID, CharacterStateResponse]
    factions: dict[uuid.UUID, Any]
    powers: dict[uuid.UUID, Any]
    relationships: list[RelationshipStateResponse]

    model_config = ConfigDict(from_attributes=True)
