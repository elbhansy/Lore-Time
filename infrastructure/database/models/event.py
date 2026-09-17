import uuid
from typing import Any

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, TimestampMixin


class EventModel(Base, TimestampMixin):
    __tablename__ = "events"

    __table_args__ = (
        UniqueConstraint(
            "series_id",
            "chapter_id",
            "sequence",
            name="uq_event_series_chapter_sequence",
        ),
        UniqueConstraint(
            "publication_fingerprint", name="uq_event_publication_fingerprint"
        ),
        Index("idx_events_series_chapter", "series_id", "chapter_id"),
        Index("idx_events_series_type", "series_id", "type"),
        Index("idx_events_series_subject", "series_id", "subject_id"),
        Index("idx_events_series_target", "series_id", "target_id"),
        Index("idx_events_search_vector", "search_vector", postgresql_using="gin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    series_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("series.id"), nullable=False
    )
    chapter_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chapters.id"), nullable=False
    )

    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    type: Mapped[str] = mapped_column(String, nullable=False)

    subject_type: Mapped[str] = mapped_column(String, nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    target_type: Mapped[str] = mapped_column(String, nullable=True)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)

    previous_state: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=True)
    new_state: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )

    # New M2.4 column for deterministic deduplication
    publication_fingerprint: Mapped[str] = mapped_column(String, nullable=True)

    # New M2.7 column for full text search
    search_vector: Mapped[Any] = mapped_column(TSVECTOR, nullable=True)

    chapter = relationship("ChapterModel", back_populates="events")
