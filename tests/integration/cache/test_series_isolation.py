"""Phase 4.8 Integration Tests: Series Isolation."""

import uuid

import pytest
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


@pytest.fixture
def clean_cache():
    service = CacheService()
    reset_cache_service_for_testing(service)
    yield service
    service.clear()
    reset_cache_service_for_testing(None)


def test_cross_series_cache_isolation(clean_cache):
    """Prove: Series A + same resource + same chapter != Series B + same resource + same chapter.
    Verify that no cached result crosses series boundaries.
    """
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    try:
        # Seed two distinct series
        sid_a_str = seed_test_series(session, num_chapters=5, events_per_chapter=3)
        sid_b_str = seed_test_series(session, num_chapters=5, events_per_chapter=3)

        sid_a = uuid.UUID(sid_a_str)
        sid_b = uuid.UUID(sid_b_str)
        assert sid_a != sid_b

        series_repo = SQLAlchemySeriesRepository(session)
        event_repo = SQLAlchemyEventRepository(session)
        builder = WorldStateBuilder(EventApplier())
        use_case = GetWorldStateUseCase(
            series_repo, event_repo, builder, cache_service=clean_cache
        )

        # 1. Fetch & Cache Series A at chapter 3
        ws_a = use_case.execute(sid_a, reader_chapter=3)
        assert ws_a.series_id.value == sid_a

        # 2. Fetch & Cache Series B at chapter 3
        ws_b = use_case.execute(sid_b, reader_chapter=3)
        assert ws_b.series_id.value == sid_b

        # 3. Fetch Series A again (Cache Hit)
        ws_a_cached = use_case.execute(sid_a, reader_chapter=3)

        # 4. Fetch Series B again (Cache Hit)
        ws_b_cached = use_case.execute(sid_b, reader_chapter=3)

        # Verification
        assert ws_a_cached.series_id.value == sid_a
        assert ws_b_cached.series_id.value == sid_b
        assert ws_a_cached.series_id.value != ws_b_cached.series_id.value

        # Character keys must belong to their respective series
        chars_a = set(ws_a_cached.characters.keys())
        chars_b = set(ws_b_cached.characters.keys())
        assert chars_a.isdisjoint(chars_b)

    finally:
        session.close()
        engine.dispose()
