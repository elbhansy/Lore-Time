from dataclasses import dataclass

from packages.domain.entities.event import Event


@dataclass
class EventQueryResult:
    reader_chapter: int
    from_chapter: int
    to_chapter: int
    items: list[Event]
    page: int
    page_size: int
    total: int
    has_next: bool
