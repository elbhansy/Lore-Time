from dataclasses import dataclass

from ..value_objects.chapter_number import ChapterNumber
from ..value_objects.entity_id import EntityId


@dataclass(frozen=True)
class Rank:
    id: EntityId
    power_system_id: EntityId
    name: str
    slug: str
    order: int
    introduced_chapter: ChapterNumber
    description: str | None = None
    parent_rank_id: EntityId | None = None
