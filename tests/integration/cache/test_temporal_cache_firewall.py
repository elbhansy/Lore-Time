"""Phase 4.8 Integration Tests: Temporal Cache Firewall & Boundary Triads."""

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.application.timeline.get_timeline_events import (
    GetTimelineEventsUseCase,
)
from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from apps.api.app.config import get_settings
from apps.api.app.core.cache import (
    CacheService,
    reset_cache_service_for_testing,
)
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


def test_temporal_cache_firewall_world_state(clean_cache):
    """Prove: request(readerChapter=5) cannot receive cached result(readerChapter=10)
    and request(readerChapter=10) cannot contaminate request(readerChapter=5).
    """
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    try:
        # Seed 10 chapters with known events
        series_id_str = seed_test_series(session, num_chapters=10, events_per_chapter=5)
        sid = uuid.UUID(series_id_str)

        series_repo = SQLAlchemySeriesRepository(session)
        event_repo = SQLAlchemyEventRepository(session)
        builder = WorldStateBuilder(EventApplier())

        use_case = GetWorldStateUseCase(
            series_repo, event_repo, builder, cache_service=clean_cache
        )

        # 1. Query readerChapter = 5 (Cold / Cache Miss -> Populates Cache)
        ws_ch5_miss = use_case.execute(sid, reader_chapter=5)
        assert ws_ch5_miss.chapter.value == 5
        # At chapter 5, exactly 25 events were processed (5 per ch)

        # 2. Query readerChapter = 10 (Cold / Cache Miss -> Populates Cache)
        ws_ch10_miss = use_case.execute(sid, reader_chapter=10)
        assert ws_ch10_miss.chapter.value == 10

        # 3. Query readerChapter = 5 (Warm / Cache Hit)
        ws_ch5_hit = use_case.execute(sid, reader_chapter=5)
        assert ws_ch5_hit.chapter.value == 5

        # Invariant Verification:
        # ws_ch5_hit must match ws_ch5_miss exactly, and have ZERO state from chapters 6-10
        stats = clean_cache.stats()
        assert stats["hits"] >= 1

        # Check character ranks / existence in chapter 5 vs chapter 10
        # In seed_temporal_series, characters progress ranks over chapters
        # Verify no future contamination
        assert ws_ch5_hit == ws_ch5_miss
        assert ws_ch5_hit != ws_ch10_miss

        # 4. Test boundary triad N-1, N, N+1 around Chapter 5
        ws_ch4 = use_case.execute(sid, reader_chapter=4)
        ws_ch5 = use_case.execute(sid, reader_chapter=5)
        ws_ch6 = use_case.execute(sid, reader_chapter=6)

        assert ws_ch4.chapter.value == 4
        assert ws_ch5.chapter.value == 5
        assert ws_ch6.chapter.value == 6

        assert ws_ch4 != ws_ch5
        assert ws_ch5 != ws_ch6

    finally:
        session.close()
        engine.dispose()


def test_temporal_cache_firewall_timeline_events(clean_cache):
    """Ensure timeline envelopes cached for readerChapter=5 cannot leak future events to readerChapter=4
    and readerChapter=10 cannot contaminate readerChapter=5.
    """
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    try:
        series_id_str = seed_test_series(session, num_chapters=8, events_per_chapter=4)
        sid = uuid.UUID(series_id_str)

        series_repo = SQLAlchemySeriesRepository(session)
        event_repo = SQLAlchemyEventRepository(session)
        use_case = GetTimelineEventsUseCase(
            series_repo, event_repo, cache_service=clean_cache
        )

        # Request up to chapter 4
        events_ch4 = use_case.execute(
            sid, reader_chapter=4, from_chapter=1, to_chapter=4
        )
        assert all(env.chapter_number.value <= 4 for env in events_ch4)

        # Request up to chapter 7
        events_ch7 = use_case.execute(
            sid, reader_chapter=7, from_chapter=1, to_chapter=7
        )
        assert len(events_ch7) > len(events_ch4)

        # Re-request chapter 4 (cache hit)
        events_ch4_hit = use_case.execute(
            sid, reader_chapter=4, from_chapter=1, to_chapter=4
        )
        assert len(events_ch4_hit) == len(events_ch4)
        assert all(env.chapter_number.value <= 4 for env in events_ch4_hit)

        # Re-request with reader_chapter=3 bounded (must not see chapter 4)
        events_ch3 = use_case.execute(
            sid, reader_chapter=3, from_chapter=1, to_chapter=4
        )
        assert all(env.chapter_number.value <= 3 for env in events_ch3)

    finally:
        session.close()
        engine.dispose()
