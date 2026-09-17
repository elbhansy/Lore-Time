from dataclasses import dataclass


@dataclass
class CanonicalSearchQuery:
    series_id: str
    q: str | None = None
    page: int = 1
    limit: int = 50
    cursor: str | None = None  # For future keyset pagination
    chapter_id: str | None = None
    event_type: str | None = None
    subject_id: str | None = None
    target_id: str | None = None
