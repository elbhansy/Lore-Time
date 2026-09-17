from dataclasses import dataclass

from ..value_objects.entity_id import EntityId


@dataclass(frozen=True)
class PowerSystem:
    id: EntityId
    series_id: EntityId
    name: str
    slug: str
    description: str | None = None
