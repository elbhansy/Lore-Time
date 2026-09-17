import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, TimestampMixin


class SkillModel(Base, TimestampMixin):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    power_system_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("power_systems.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)

    power_system = relationship("PowerSystemModel", back_populates="skills")
