from dataclasses import dataclass, field

from ..value_objects.entity_id import EntityId


@dataclass
class FactionState:
    faction_id: EntityId
    exists: bool = False
    name: str | None = None
    leader_id: EntityId | None = None
    members: set[EntityId] = field(default_factory=set)
