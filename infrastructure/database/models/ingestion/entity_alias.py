import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base, TimestampMixin


class EntityAliasModel(Base, TimestampMixin):
    __tablename__ = "entity_aliases"

    __table_args__ = (
        UniqueConstraint(
            "series_id",
            "entity_type",
            "normalized_alias",
            name="uq_series_type_normalized_alias",
        ),
        Index("idx_alias_series_normalized", "series_id", "normalized_alias"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    series_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("series.id"), nullable=False
    )

    # entity_id is not a hard FK to a single table because it could point to characters, factions, skills, etc.
    # Therefore we store it as a generic UUID.
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    entity_type: Mapped[str] = mapped_column(String, nullable=False)

    alias: Mapped[str] = mapped_column(String, nullable=False)
    normalized_alias: Mapped[str] = mapped_column(String, nullable=False)

    source: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
