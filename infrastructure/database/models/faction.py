import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, TimestampMixin


class FactionModel(Base, TimestampMixin):
    __tablename__ = "factions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    series_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("series.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)

    series = relationship("SeriesModel", back_populates="factions")
