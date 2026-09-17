import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base, TimestampMixin


class SourceModel(Base, TimestampMixin):
    __tablename__ = "sources"

    __table_args__ = (
        UniqueConstraint(
            "series_id",
            "type",
            "name",
            "version",
            name="uq_source_series_type_name_version",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    series_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("series.id"), nullable=False
    )

    type: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    uri: Mapped[str | None] = mapped_column(String, nullable=True)
    version: Mapped[str] = mapped_column(
        String, nullable=False, default=""
    )  # Strict fallback for PostgreSQL uniqueness

    status: Mapped[str] = mapped_column(String, nullable=False)
