from dataclasses import dataclass
from datetime import datetime

from packages.domain.extraction.extraction_result import RawExtractedFact
from packages.domain.provenance.provenance import Provenance
from packages.domain.review.review_status import ReviewStatus


@dataclass
class ReviewItem:
    id: str
    series_id: str
    chapter_id: str
    fact: RawExtractedFact
    provenance: Provenance
    status: ReviewStatus
    reviewer_id: str | None = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
