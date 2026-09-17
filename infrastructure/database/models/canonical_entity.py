from sqlalchemy import JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database.base import Base, TimestampMixin


class CanonicalEntityModel(Base, TimestampMixin):
    __tablename__ = "canonical_entities"

    __table_args__ = (
        UniqueConstraint("series_id", "id", name="uq_canonical_entity_series_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    series_id: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
