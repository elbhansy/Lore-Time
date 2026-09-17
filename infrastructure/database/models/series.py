import uuid

from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, TimestampMixin


class SeriesModel(Base, TimestampMixin):
    __tablename__ = "series"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    total_chapters: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    chapters = relationship(
        "ChapterModel", back_populates="series", cascade="all, delete-orphan"
    )
    characters = relationship(
        "CharacterModel", back_populates="series", cascade="all, delete-orphan"
    )
    factions = relationship(
        "FactionModel", back_populates="series", cascade="all, delete-orphan"
    )
    power_systems = relationship(
        "PowerSystemModel", back_populates="series", cascade="all, delete-orphan"
    )
