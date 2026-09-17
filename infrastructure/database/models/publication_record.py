import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin


class PublicationRecordModel(Base, TimestampMixin):
    __tablename__ = "publication_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    review_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("review_items.id"), nullable=False
    )
    event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("events.id"), nullable=True
    )

    status: Mapped[str] = mapped_column(
        String, nullable=False
    )  # PENDING, PUBLISHED, FAILED, SKIPPED
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    actor_id: Mapped[str | None] = mapped_column(String, nullable=True)
