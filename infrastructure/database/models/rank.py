import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, TimestampMixin


class RankModel(Base, TimestampMixin):
    __tablename__ = "ranks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    power_system_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("power_systems.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    introduced_chapter: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    parent_rank_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ranks.id"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("power_system_id", "slug", name="uq_rank_power_system_slug"),
    )

    power_system = relationship("PowerSystemModel", back_populates="ranks")
