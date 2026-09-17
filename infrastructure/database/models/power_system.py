import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, TimestampMixin


class PowerSystemModel(Base, TimestampMixin):
    __tablename__ = "power_systems"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    series_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("series.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("series_id", "slug", name="uq_power_system_series_slug"),
    )

    series = relationship("SeriesModel", back_populates="power_systems")
    ranks = relationship(
        "RankModel", back_populates="power_system", cascade="all, delete-orphan"
    )
    skills = relationship(
        "SkillModel", back_populates="power_system", cascade="all, delete-orphan"
    )
