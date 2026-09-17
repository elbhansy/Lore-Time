from dataclasses import dataclass, field
from typing import Any

from ..value_objects.entity_id import EntityId
from ..value_objects.entity_type import EntityType
from ..value_objects.event_type import EventType


@dataclass(frozen=True)
class Event:
    id: EntityId
    chapter_id: EntityId
    sequence: int
    type: EventType
    subject_type: EntityType
    subject_id: EntityId
    series_id: EntityId | None = None
    target_type: EntityType | None = None
    target_id: EntityId | None = None
    previous_state: dict[str, Any] = field(default_factory=dict)
    new_state: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
