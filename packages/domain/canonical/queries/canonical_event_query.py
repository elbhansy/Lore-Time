from dataclasses import dataclass


@dataclass
class CanonicalEventQuery:
    series_id: str
    page: int = 1
    limit: int = 50
    chapter_id: str | None = None
    event_type: str | None = None
    subject_id: str | None = None
    target_id: str | None = None
