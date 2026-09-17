from dataclasses import dataclass
from datetime import datetime


@dataclass
class CanonicalEventDTO:
    id: str
    series_id: str
    chapter_id: str
    chapter_number: int  # Very important for UI grouping
    type: str
    subject_id: str
    target_id: str | None
    payload: dict
    provenance: dict
    published_at: datetime
