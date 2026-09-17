from fastapi import Depends
from sqlalchemy.orm import Session

from apps.api.repositories.sqlalchemy_character_repository import (
    SQLAlchemyCharacterRepository,
)
from apps.api.repositories.sqlalchemy_event_repository import SQLAlchemyEventRepository
from apps.api.repositories.sqlalchemy_power_system_repository import (
    SQLAlchemyPowerSystemRepository,
)
from apps.api.repositories.sqlalchemy_rank_repository import SQLAlchemyRankRepository
from apps.api.repositories.sqlalchemy_series_repository import (
    SQLAlchemySeriesRepository,
)
from packages.domain.repositories.character_repository import CharacterRepository
from packages.domain.repositories.event_repository import EventRepository
from packages.domain.repositories.power_system_repository import PowerSystemRepository
from packages.domain.repositories.rank_repository import RankRepository
from packages.domain.repositories.series_repository import SeriesRepository

from .database import get_db


def get_series_repository(db: Session = Depends(get_db)) -> SeriesRepository:
    return SQLAlchemySeriesRepository(db)


def get_event_repository(db: Session = Depends(get_db)) -> EventRepository:
    return SQLAlchemyEventRepository(db)


def get_character_repository(db: Session = Depends(get_db)) -> CharacterRepository:
    return SQLAlchemyCharacterRepository(db)


def get_power_system_repository(db: Session = Depends(get_db)) -> PowerSystemRepository:
    return SQLAlchemyPowerSystemRepository(db)


def get_rank_repository(db: Session = Depends(get_db)) -> RankRepository:
    return SQLAlchemyRankRepository(db)
