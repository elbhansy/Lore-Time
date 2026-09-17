from dataclasses import dataclass, field

from ..value_objects.entity_id import EntityId


@dataclass
class CharacterState:
    character_id: EntityId
    exists: bool = False
    alive: bool = True
    rank: str | None = None
    faction_id: str | None = None
    unlocked_skills: set[str] = field(default_factory=set)
