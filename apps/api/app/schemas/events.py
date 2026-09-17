from typing import Any

from pydantic import BaseModel


class EventDTO(BaseModel):
    id: str
    series_id: str
    chapter_id: str
    sequence: int
    type: str
    subject_type: str
    subject_id: str
    target_type: str | None
    target_id: str | None
    previous_state: dict[str, Any]
    new_state: dict[str, Any]
    metadata: dict[str, Any]


class EventQueryResultDTO(BaseModel):
    reader_chapter: int
    from_chapter: int
    to_chapter: int
    items: list[EventDTO]
    page: int
    page_size: int
    total: int
    has_next: bool
