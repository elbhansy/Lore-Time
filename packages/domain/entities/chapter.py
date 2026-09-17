from dataclasses import dataclass

from ..value_objects.chapter_number import ChapterNumber
from ..value_objects.entity_id import EntityId


@dataclass(frozen=True)
class Chapter:
    id: EntityId
    series_id: EntityId
    number: ChapterNumber
    title: str
