import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base, TimestampMixin


class ReviewItemModel(Base, TimestampMixin):
    __tablename__ = "review_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    series_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("series.id"), nullable=False
    )
    chapter_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chapters.id"), nullable=False
    )

    # Store ExtractedFact details
    fact_type: Mapped[str] = mapped_column(String, nullable=False)
    fact_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Store Provenance details
    provenance_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    status: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_id: Mapped[str] = mapped_column(String, nullable=True)
