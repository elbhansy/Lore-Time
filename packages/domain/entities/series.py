from dataclasses import dataclass

from ..value_objects.entity_id import EntityId


@dataclass(frozen=True)
class Series:
    id: EntityId
    title: str
    slug: str
    total_chapters: int

    def __post_init__(self):
        if not self.title or not self.title.strip():
            raise ValueError("Series title cannot be empty.")
        if not self.slug or not self.slug.strip():
            raise ValueError("Series slug cannot be empty.")
        if self.total_chapters < 0:
            raise ValueError("Total chapters cannot be negative.")
