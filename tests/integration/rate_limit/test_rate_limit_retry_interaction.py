"""Integration tests verifying Rate Limiting interaction with Retries (COMMAND 14).

Using Phase 4.9 Rate Limiting & Phase 4.11 Retry Semantics:
Tests:
- repeated requests
- duplicate requests
- concurrent requests
- failed requests (400, 404, 500)
- successful retries

Verifies that:
1. Rate limiting still works and enforces tier budgets.
2. Retries cannot bypass abuse protection (each HTTP retry consumes client quota).
3. Internal recovery (e.g. database retry, dirty cache bypass, internal retry loops)
   does not consume user HTTP budget.
4. /health remains available and exempt under retry storms.
5. /ready behavior remains correct and exempt under retry storms.

Acceptance:
0 skipped, 0 failed.
"""

import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.application.publishing.publish_review_item import (
    PublishReviewItemUseCase,
)
from apps.api.app.config import get_settings
from apps.api.app.core.rate_limit import get_rate_limit_service
from apps.api.app.main import app
from packages.domain.review.review_item import ReviewItem
from packages.domain.review.review_status import ReviewStatus
from tests.integration.cache.seed_helper import seed_test_series


@pytest.fixture(autouse=True)
def reset_limiter():
    """Ensure clean rate limiter state before and after each test."""
    limiter = get_rate_limit_service()
    limiter.clear()
    yield
    limiter.clear()


def test_repeated_requests_trip_rate_limit():
    """Verify that repeated client requests across identical endpoint trip rate limit."""
    settings = get_settings()
    client = TestClient(app)
    limiter = get_rate_limit_service()

    burst = settings.RATE_LIMIT_DEFAULT_BURST  # 30
    client_ip = "192.168.10.1"

    # Send requests up to burst limit
    for i in range(burst):
        resp = client.get(
            "/api/v1/unknown-endpoint", headers={"X-Forwarded-For": client_ip}
        )
        assert resp.status_code == 404

    # The burst + 1 request must be rejected with 429
    blocked = client.get(
        "/api/v1/unknown-endpoint", headers={"X-Forwarded-For": client_ip}
    )
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert "Retry-After" in blocked.headers
    assert limiter.stats()["rejected"] >= 1


def test_duplicate_requests_cannot_bypass_rate_limit():
    """Verify that sending duplicate identical requests with identical query params
    or headers still consumes rate limit tokens and trips 429 once budget is exhausted.
    """
    settings = get_settings()
    client = TestClient(app)

    series_id = uuid.uuid4()
    endpoint = f"/api/v1/series/{series_id}/world-state?chapter=1"
    expensive_burst = settings.RATE_LIMIT_EXPENSIVE_BURST  # 10
    client_ip = "192.168.10.2"

    # Exactly 10 identical duplicate requests allowed
    for _ in range(expensive_burst):
        resp = client.get(endpoint, headers={"X-Forwarded-For": client_ip})
        assert resp.status_code in (200, 404)

    # 11th duplicate request MUST trip 429
    blocked = client.get(endpoint, headers={"X-Forwarded-For": client_ip})
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_concurrent_retries_respect_concurrency_and_rate_limits():
    """Verify that concurrent retries from multiple threads against the same identity
    are accurately bounded by the token bucket with zero race conditions.
    """
    settings = get_settings()
    client = TestClient(app)

    expensive_burst = settings.RATE_LIMIT_EXPENSIVE_BURST  # 10
    total_concurrent_requests = 25
    client_ip = "192.168.10.3"
    endpoint = f"/api/v1/series/{uuid.uuid4()}/world-state?chapter=1"

    def fire_request():
        return client.get(endpoint, headers={"X-Forwarded-For": client_ip}).status_code

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(fire_request) for _ in range(total_concurrent_requests)
        ]
        codes = [f.result() for f in futures]

    allowed = sum(1 for c in codes if c != 429)
    rejected = sum(1 for c in codes if c == 429)

    assert allowed == expensive_burst
    assert rejected == total_concurrent_requests - expensive_burst


def test_failed_requests_consume_http_budget_preventing_brute_force():
    """Verify that failed client requests (400 Invalid Chapter, 404 Not Found)
    consume rate limit budget, preventing an attacker from spamming failed queries.
    """
    settings = get_settings()
    client = TestClient(app)

    client_ip = "192.168.10.4"
    expensive_burst = settings.RATE_LIMIT_EXPENSIVE_BURST  # 10

    # Flood with invalid chapter queries (400 validation error because ge=1 on EXPENSIVE_READ tier)
    for _ in range(expensive_burst):
        resp = client.get(
            "/api/v1/series/11111111-1111-1111-1111-111111111111/world-state?chapter=-5",
            headers={"X-Forwarded-For": client_ip},
        )
        assert resp.status_code == 400

    # 11th request must be 429
    over_limit = client.get(
        "/api/v1/series/11111111-1111-1111-1111-111111111111/world-state?chapter=-5",
        headers={"X-Forwarded-For": client_ip},
    )
    assert over_limit.status_code == 429
    assert over_limit.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_successful_retries_consume_budget_per_http_attempt():
    """Verify that each HTTP retry attempt consumes 1 token.
    If a client retries until success, each HTTP trip counts against the client's quota.
    """
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    try:
        series_id = seed_test_series(session, num_chapters=3, events_per_chapter=1)
        client = TestClient(app)
        client_ip = "192.168.10.5"

        endpoint = f"/api/v1/series/{series_id}/world-state?chapter=1"
        expensive_burst = settings.RATE_LIMIT_EXPENSIVE_BURST  # 10

        # Simulate client doing 5 successful retries/requests
        for attempt in range(5):
            resp = client.get(endpoint, headers={"X-Forwarded-For": client_ip})
            assert resp.status_code == 200

        # Next 5 requests consume the rest of the burst
        for _ in range(expensive_burst - 5):
            resp = client.get(endpoint, headers={"X-Forwarded-For": client_ip})
            assert resp.status_code == 200

        # The (expensive_burst + 1)th retry must be throttled
        blocked = client.get(endpoint, headers={"X-Forwarded-For": client_ip})
        assert blocked.status_code == 429
    finally:
        session.close()
        engine.dispose()


def test_internal_recovery_does_not_consume_user_http_budget():
    """Verify that internal domain retries and recovery mechanisms
    (e.g., PublishReviewItemUseCase retrying or handling dirty cache invalidation)
    do NOT consume HTTP client rate limit budget.
    """
    from datetime import datetime

    from packages.domain.extraction.extraction_result import (
        RawExtractedFact,
        RawFactEvidence,
    )
    from packages.domain.extraction.fact_type import FactType
    from packages.domain.provenance.confidence import Confidence
    from packages.domain.provenance.evidence import Evidence
    from packages.domain.provenance.provenance import Provenance

    settings = get_settings()
    limiter = get_rate_limit_service()
    limiter.clear()

    # Create dummy repo and publish use case
    class MockRepo:
        def __init__(self):
            self.lock_calls = 0
            self.events = {}
            self.records = {}
            self.relationships = []
            self.entities = {}

        def execute_in_transaction(self, item, action):
            action()

        def lock_review_item(self, item_id):
            self.lock_calls += 1
            return None

        def save_event(self, data):
            return "ev_1"

        def save_publication_record(self, data):
            pass

        def update_review_status(self, item, status):
            item.status = status

        def ensure_entity_exists(self, *args, **kwargs):
            pass

        def create_relationship(self, *args, **kwargs):
            pass

    repo = MockRepo()
    use_case = PublishReviewItemUseCase(repo)

    fact = RawExtractedFact(
        type=FactType.POWER_RANK_CHANGED,
        subject_raw="Dokja",
        target_raw=None,
        payload={"from_rank": "B", "to_rank": "A", "subject_id": "dokja_uuid"},
        extraction_confidence=0.9,
        evidence=RawFactEvidence(location="p1"),
    )
    prov = Provenance(
        source_id="s1",
        evidence=Evidence(chapter_id="c1", location="p1"),
        confidence=Confidence(1.0, 1.0, 1.0, 1.0),
        captured_at=datetime.now(),
    )
    review_item = ReviewItem(
        id=str(uuid.uuid4()),
        series_id=str(uuid.uuid4()),
        chapter_id="c1",
        fact=fact,
        provenance=prov,
        status=ReviewStatus.APPROVED,
    )

    # Capture baseline stats before internal execution
    initial_stats = limiter.stats()
    initial_allowed = initial_stats.get("allowed", 0)
    initial_rejected = initial_stats.get("rejected", 0)
    initial_active = initial_stats.get("active_identities", 0)

    # Execute multiple internal use-case publications / retries
    for _ in range(15):
        use_case.execute(review_item)

    # Internal recovery / domain publication must not touch HTTP rate limit tokens
    after_stats = limiter.stats()
    assert after_stats.get("allowed", 0) == initial_allowed
    assert after_stats.get("rejected", 0) == initial_rejected
    assert after_stats.get("active_identities", 0) == initial_active


def test_health_and_ready_remain_available_during_retry_storms():
    """Verify that /health and /ready remain 100% available and exempt even when
    the client has completely exhausted their rate limit on other endpoints.
    """
    settings = get_settings()
    client = TestClient(app)
    client_ip = "192.168.10.6"

    burst = settings.RATE_LIMIT_DEFAULT_BURST  # 30

    # 1. Exhaust client budget completely on regular endpoint
    for _ in range(burst):
        client.get(
            "/api/v1/series/non-existent", headers={"X-Forwarded-For": client_ip}
        )

    # Verify regular endpoint returns 429
    blocked = client.get(
        "/api/v1/series/non-existent", headers={"X-Forwarded-For": client_ip}
    )
    assert blocked.status_code == 429

    # 2. Verify /health remains 200 OK without being throttled
    for _ in range(50):
        h_resp = client.get("/health", headers={"X-Forwarded-For": client_ip})
        assert h_resp.status_code == 200
        assert h_resp.json() == {"status": "ok", "service": "timeline-api"}

    # 3. Verify /ready remains available (200 or DB status) and NEVER returns 429
    for _ in range(50):
        r_resp = client.get("/ready", headers={"X-Forwarded-For": client_ip})
        assert r_resp.status_code in (200, 503)
        assert r_resp.status_code != 429
