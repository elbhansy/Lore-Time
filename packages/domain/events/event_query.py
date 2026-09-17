from dataclasses import dataclass, field

from packages.domain.value_objects.event_type import EventType


@dataclass
class EventQuery:
    series_id: str
    reader_chapter: int
    from_chapter: int = 1
    to_chapter: int | None = None
    event_types: list[EventType] = field(default_factory=list)
    subject_id: str | None = None
    target_id: str | None = None
    page: int = 1
    page_size: int = 50

    def __post_init__(self):
        if self.to_chapter is None:
            self.to_chapter = self.reader_chapter

        if self.from_chapter < 1:
            raise ValueError("from_chapter must be >= 1")

        if self.from_chapter > self.to_chapter:
            raise ValueError("from_chapter must be <= to_chapter")

        if self.to_chapter > self.reader_chapter:
            # Strict boundary constraint as requested
            raise ValueError("to_chapter cannot exceed reader_chapter")

        if self.page < 1:
            raise ValueError("page must be >= 1")

        if self.page_size < 1 or self.page_size > 100:
            raise ValueError("page_size must be between 1 and 100")
