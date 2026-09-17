import uuid

from pydantic import BaseModel, ConfigDict


class CharacterStateResponse(BaseModel):
    exists: bool
    alive: bool
    rank: str | None
    unlocked_skills: set[uuid.UUID]
    faction_id: uuid.UUID | None

    model_config = ConfigDict(from_attributes=True)


class CharacterResponse(BaseModel):
    id: uuid.UUID
    name: str
    state: CharacterStateResponse
    as_of_chapter: int

    model_config = ConfigDict(from_attributes=True)
