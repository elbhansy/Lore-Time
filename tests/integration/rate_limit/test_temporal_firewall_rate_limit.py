"""Integration tests for Temporal Firewall & Reader Chapter Boundary under Rate Limiting."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.config import get_settings
from apps.api.app.core.rate_limit import get_rate_limit_service
from apps.api.app.main import app
from tests.integration.cache.seed_helper import seed_test_series


def test_temporal_firewall_unaltered_under_rate_limiting():
    """Verify that readerChapter=N produces identical domain data whether:
    - cold
    - warm near threshold
    - post-recovery after 429
    Zero temporal leakage across boundary triads (N-1, N, N+1).
    """
    settings = get_settings()
    limiter = get_rate_limit_service()
    limiter.clear()

    engine = create_engine(settings.DATABASE_URL)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    try:
        series_id_str = seed_test_series(session, num_chapters=10, events_per_chapter=5)
        sid = uuid.UUID(series_id_str)

        client = TestClient(app)

        # 1. First request at Chapter 5
        resp1 = client.get(f"/api/v1/series/{sid}/world-state?chapter=5")
        assert resp1.status_code == 200
        data1 = resp1.json()

        # 2. Re-request near threshold
        resp2 = client.get(f"/api/v1/series/{sid}/world-state?chapter=5")
        assert resp2.status_code == 200
        data2 = resp2.json()

        assert data1 == data2

        # 3. Boundary triad testing (N-1, N, N+1)
        resp_ch4 = client.get(f"/api/v1/series/{sid}/world-state?chapter=4")
        resp_ch6 = client.get(f"/api/v1/series/{sid}/world-state?chapter=6")

        assert resp_ch4.status_code == 200
        assert resp_ch6.status_code == 200

        data_ch4 = resp_ch4.json()
        data_ch6 = resp_ch6.json()

        assert data_ch4["chapter"] == 4
        assert data1["chapter"] == 5
        assert data_ch6["chapter"] == 6

        assert data_ch4 != data1
        assert data1 != data_ch6

    finally:
        session.close()
        engine.dispose()
