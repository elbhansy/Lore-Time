from dataclasses import dataclass

from ..value_objects.entity_id import EntityId


@dataclass(frozen=True)
class Character:
    id: EntityId
    series_id: EntityId
    name: str
    description: str

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Character name cannot be empty.")
