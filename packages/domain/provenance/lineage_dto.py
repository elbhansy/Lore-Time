from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PublicationAuditDTO:
    id: str
    status: str
    attempted_at: datetime
    actor_id: str | None
    error_message: str | None


@dataclass(frozen=True)
class ExtractedFactAuditDTO:
    type: str
    subject_raw: str
    target_raw: str | None
    payload: dict


@dataclass(frozen=True)
class ReviewItemAuditDTO:
    id: str
    status: str
    reviewer_id: str | None
    reviewed_at: datetime


@dataclass(frozen=True)
class ProvenanceAuditDTO:
    status: str  # "available" or "unavailable"
    source_id: str | None = None
    evidence_location: str | None = None
    confidence_score: float | None = None
    reason: str | None = None


@dataclass(frozen=True)
class CanonicalEventAuditDTO:
    id: str
    series_id: str
    chapter_id: str
    type: str
    published_at: datetime


@dataclass(frozen=True)
class CanonicalEventLineageDTO:
    event: CanonicalEventAuditDTO
    review_item: ReviewItemAuditDTO
    publications: list[PublicationAuditDTO]  # History of all attempts
    extracted_fact: ExtractedFactAuditDTO
    provenance: ProvenanceAuditDTO
