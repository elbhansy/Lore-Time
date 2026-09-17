"""Phase 4.8 Integration Tests: Cache Disabled Mode (CACHE_ENABLED=False)."""

import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from apps.api.app.config import Environment, Settings
from apps.api.app.core.cache import CacheService, reset_cache_service_for_testing
from apps.api.repositories.sqlalchemy_event_repository import SQLAlchemyEventRepository
from apps.api.repositories.sqlalchemy_series_repository import (
    SQLAlchemySeriesRepository,
)
from packages.domain.services.event_applier import EventApplier
from packages.domain.services.world_state_builder import WorldStateBuilder
from tests.integration.cache.seed_helper import seed_test_series


def test_cache_disabled_mode_matches_enabled_mode_deterministically():
    """Verify:
    When CACHE_ENABLED=False:
    1. Zero cache entries are saved.
    2. Zero hits occur.
    3. The computed result matches the cache-enabled result 100% deterministically.
    """
    settings_disabled = Settings(
        ENVIRONMENT=Environment.DEVELOPMENT,
        CACHE_ENABLED=False,
    )
    disabled_service = CacheService(settings=settings_disabled)
    reset_cache_service_for_testing(disabled_service)

    engine = create_engine(settings_disabled.DATABASE_URL)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    try:
        series_id_str = seed_test_series(session, num_chapters=4, events_per_chapter=3)
        sid = uuid.UUID(series_id_str)

        series_repo = SQLAlchemySeriesRepository(session)
        event_repo = SQLAlchemyEventRepository(session)
        builder = WorldStateBuilder(EventApplier())

        # Execute with disabled cache
        use_case_disabled = GetWorldStateUseCase(
            series_repo, event_repo, builder, cache_service=disabled_service
        )
        ws_disabled_1 = use_case_disabled.execute(sid, reader_chapter=3)
        ws_disabled_2 = use_case_disabled.execute(sid, reader_chapter=3)

        assert disabled_service.stats()["entries"] == 0
        assert disabled_service.stats()["hits"] == 0
        assert ws_disabled_1 == ws_disabled_2

        # Execute with enabled cache
        enabled_service = CacheService()
        use_case_enabled = GetWorldStateUseCase(
            series_repo, event_repo, builder, cache_service=enabled_service
        )
        ws_enabled = use_case_enabled.execute(sid, reader_chapter=3)

        # Invariant: Output is byte-for-byte / structurally identical
        assert ws_disabled_1 == ws_enabled

    finally:
        reset_cache_service_for_testing(None)
        session.close()
        engine.dispose()
