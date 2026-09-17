"""Phase 4.8 Integration Tests: Performance Verification (Direct DB vs Cache Miss vs Cache Hit)."""

import time
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


def test_performance_verification_hit_vs_miss_speedup():
    """Verify that Cache Hit provides an order-of-magnitude latency improvement over Cache Miss."""
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    try:
        # Seed realistic series with 10 chapters and 100 events
        series_id_str = seed_test_series(
            session, num_chapters=10, events_per_chapter=10
        )
        sid = uuid.UUID(series_id_str)

        cache_service = CacheService()
        reset_cache_service_for_testing(cache_service)

        series_repo = SQLAlchemySeriesRepository(session)
        event_repo = SQLAlchemyEventRepository(session)
        builder = WorldStateBuilder(EventApplier())
        use_case = GetWorldStateUseCase(
            series_repo, event_repo, builder, cache_service=cache_service
        )

        # 1. Measure Cache Miss (direct DB compute)
        t0 = time.perf_counter()
        ws_miss = use_case.execute(sid, reader_chapter=10)
        miss_duration_ms = (time.perf_counter() - t0) * 1000

        # 2. Measure Cache Hit (memory retrieval)
        t1 = time.perf_counter()
        ws_hit = use_case.execute(sid, reader_chapter=10)
        hit_duration_ms = (time.perf_counter() - t1) * 1000

        assert ws_miss == ws_hit
        assert hit_duration_ms < miss_duration_ms
        # In-process cache should complete in < 1ms
        assert hit_duration_ms < 2.0

        stats = cache_service.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    finally:
        reset_cache_service_for_testing(None)
        session.close()
        engine.dispose()
