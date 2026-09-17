"""Integration tests for Rate Limiting and Phase 4.8 Caching interaction."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.config import get_settings
from apps.api.app.core.cache import get_cache_service
from apps.api.app.core.rate_limit import get_rate_limit_service
from apps.api.app.main import app
from tests.integration.cache.seed_helper import seed_test_series


def test_cache_hits_and_misses_both_consume_rate_limit_budget():
    """Verify that hitting a cached endpoint still consumes rate limit budget,
    preventing attackers from using cache to flood the server.
    """
    settings = get_settings()
    cache = get_cache_service()
    limiter = get_rate_limit_service()
    cache.clear()
    limiter.clear()

    engine = create_engine(settings.DATABASE_URL)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    try:
        series_id_str = seed_test_series(session, num_chapters=5, events_per_chapter=2)
        sid = uuid.UUID(series_id_str)

        client = TestClient(app)
        endpoint = f"/api/v1/series/{sid}/world-state?chapter=1"

        # 1. Request 1: Cache Miss -> Rate Limit Budget Consumed
        r1 = client.get(endpoint)
        assert r1.status_code == 200

        # Verify cache has item
        assert cache.stats()["entries"] >= 1

        # 2. Consume remainder of expensive burst (limit 10)
        for _ in range(settings.RATE_LIMIT_EXPENSIVE_BURST - 1):
            r_hit = client.get(endpoint)
            assert r_hit.status_code == 200

        # Verify cache hit rate increased
        assert cache.stats()["hits"] >= 1

        # 3. 11th request (even though cached in memory) MUST be rejected with 429
        r_blocked = client.get(endpoint)
        assert r_blocked.status_code == 429

    finally:
        session.close()
        engine.dispose()
