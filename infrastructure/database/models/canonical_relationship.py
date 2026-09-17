import uuid

from sqlalchemy import Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database.base import Base, TimestampMixin


class CanonicalRelationshipModel(Base, TimestampMixin):
    __tablename__ = "canonical_relationships"

    __table_args__ = (
        Index("idx_rel_series_source", "series_id", "source_entity_id"),
        Index("idx_rel_series_target", "series_id", "target_entity_id"),
        Index("idx_rel_series_type", "series_id", "type"),
        Index("idx_rel_event", "event_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    series_id: Mapped[str] = mapped_column(String, nullable=False)
    source_entity_id: Mapped[str] = mapped_column(String, nullable=False)
    target_entity_id: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)

    # Provenance linking back to the Canonical Event
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
