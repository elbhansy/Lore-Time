"""Phase 4.8 Integration Tests: Cache Failure Degradation & Fallback."""

import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from apps.api.app.config import get_settings
from apps.api.app.core.cache import CacheService, reset_cache_service_for_testing
from apps.api.repositories.sqlalchemy_event_repository import SQLAlchemyEventRepository
from apps.api.repositories.sqlalchemy_series_repository import (
    SQLAlchemySeriesRepository,
)
from packages.domain.services.event_applier import EventApplier
from packages.domain.services.world_state_builder import WorldStateBuilder
from tests.integration.cache.seed_helper import seed_test_series


class BrokenCacheBackend:
    """Simulates a totally corrupted or crashed cache backend."""

    def get(self, key: str):
        raise ConnectionError("Cache connection refused")

    def set(self, key: str, value, ttl_seconds=None):
        raise TimeoutError("Cache write timed out")

    def delete(self, key: str):
        raise RuntimeError("Delete crashed")

    def delete_prefix(self, prefix: str):
        raise RuntimeError("Delete prefix crashed")

    def mark_dirty(self, namespace: str):
        pass

    def is_dirty(self, namespace: str):
        return False

    def clean_dirty(self, namespace: str):
        pass

    def clear(self):
        pass

    def stats(self):
        return {}


def test_cache_failure_graceful_degradation_to_database():
    """Verify that when cache operations throw severe errors (connection error, timeouts),
    the application layer catches the exception, logs structured error, and safely computes
    the result directly from PostgreSQL without raising a 500 error to the client.
    """
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    try:
        series_id_str = seed_test_series(session, num_chapters=3, events_per_chapter=2)
        sid = uuid.UUID(series_id_str)

        broken_service = CacheService(backend=BrokenCacheBackend())
        reset_cache_service_for_testing(broken_service)

        series_repo = SQLAlchemySeriesRepository(session)
        event_repo = SQLAlchemyEventRepository(session)
        builder = WorldStateBuilder(EventApplier())
        use_case = GetWorldStateUseCase(
            series_repo, event_repo, builder, cache_service=broken_service
        )

        # Execution must succeed despite broken cache
        ws = use_case.execute(sid, reader_chapter=2)
        assert ws is not None
        assert ws.series_id.value == sid
        assert ws.chapter.value == 2

    finally:
        reset_cache_service_for_testing(None)
        session.close()
        engine.dispose()
