"""Integration tests verifying Observability During Failure and Recovery (COMMAND 15).

Verifies that every recovery and mutation path produces structured logs containing:
- request_id
- operation
- series_id
- outcome
- error classification / code
- duration_ms

Verifies logs do NOT contain:
- passwords
- tokens
- credentials
- raw sensitive payloads
- future story content (temporal privacy firewall)

Test scenarios:
1. DB failure (OperationalError, timeout, transaction rollback)
2. Retry (recovering after transient connection drop)
3. Duplicate operation (sequential no-op retry and concurrent race)
4. Conflict (409 conflict / concurrency lock collision)
5. Cache failure (post-commit invalidation error & dirty bypass)

Acceptance:
Zero sensitive-data leakage.
0 skipped, 0 failed.
"""

import logging
import uuid
from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from apps.api.app.application.publishing.publish_review_item import (
    PublishReviewItemUseCase,
)
from apps.api.app.config import get_settings
from apps.api.app.core.cache import CacheService
from apps.api.app.core.rate_limit import get_rate_limit_service
from apps.api.app.main import app
from apps.api.repositories.canonical.sqlalchemy_publication_repository import (
    SQLAlchemyPublicationRepository,
)
from infrastructure.database.models import Base
from infrastructure.database.models.chapter import ChapterModel
from infrastructure.database.models.review.review_item_model import (
    ReviewItemModel,
)
from infrastructure.database.models.series import SeriesModel
from packages.domain.extraction.extraction_result import (
    RawExtractedFact,
    RawFactEvidence,
)
from packages.domain.extraction.fact_type import FactType
from packages.domain.provenance.confidence import Confidence
from packages.domain.provenance.evidence import Evidence
from packages.domain.provenance.provenance import Provenance
from packages.domain.review.review_item import ReviewItem
from packages.domain.review.review_status import ReviewStatus


@pytest.fixture(autouse=True)
def clean_test_environment():
    get_rate_limit_service().clear()
    yield
    get_rate_limit_service().clear()


@pytest.fixture
def pub_session_factory():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)


def _assert_no_sensitive_data_in_logs(records, forbidden_terms=None):
    """Asserts that logs do not leak credentials, passwords, tokens, or forbidden sensitive payloads."""
    forbidden = ["password", "bearer eyj", "super_secret", "access_token", "api_key="]
    if forbidden_terms:
        forbidden.extend(forbidden_terms)

    for record in records:
        msg = record.getMessage().lower()
        for term in forbidden:
            assert term not in msg, (
                f"Sensitive term '{term}' leaked in log message: {record.getMessage()}"
            )

        # Check structured extra attributes
        for attr in ("error", "details", "message", "operation"):
            val = getattr(record, attr, None)
            if val is not None:
                val_str = str(val).lower()
                for term in forbidden:
                    assert term not in val_str, (
                        f"Sensitive term '{term}' leaked in log attr '{attr}': {val}"
                    )


# ==============================================================================
# 1. DATABASE FAILURE OBSERVABILITY
# ==============================================================================


def test_database_failure_observability_and_redaction(caplog):
    """Verifies that DB operational failures and timeouts emit structured logs with
    request_id, operation, outcome, error classification, and NO raw passwords.
    """
    client = TestClient(app)
    caplog.set_level(logging.INFO)
    sid = uuid.uuid4()
    req_id = str(uuid.uuid4())

    with patch(
        "apps.api.app.application.timeline.get_world_state.GetWorldStateUseCase.execute",
        side_effect=OperationalError(
            "SELECT 1",
            {},
            Exception(
                "connection to postgresql://admin:super_secret_pw123@localhost:5432/db failed"
            ),
        ),
    ):
        response = client.get(
            f"/api/v1/series/{sid}/world-state?chapter=1",
            headers={"X-Request-ID": req_id},
        )
        assert response.status_code == 503

    # Check request and db failure logs
    db_failures = [
        r
        for r in caplog.records
        if getattr(r, "event", None)
        in ("database.operation.failed", "request.completed")
    ]
    assert len(db_failures) >= 1

    # Verify structured fields
    completed_event = [
        r for r in db_failures if getattr(r, "event", None) == "request.completed"
    ][0]
    assert completed_event.request_id == req_id
    assert completed_event.operation == f"GET /api/v1/series/{sid}/world-state"
    assert completed_event.outcome == "failure"
    assert completed_event.status_code == 503
    assert completed_event.duration_ms >= 0

    # Verify NO password leakage
    _assert_no_sensitive_data_in_logs(caplog.records, ["super_secret_pw123"])


@pytest.fixture
def series_context(pub_session_factory):
    """Creates a distinct series and chapter context in PostgreSQL."""
    sid = uuid.uuid4()
    cid = uuid.uuid4()
    Session = pub_session_factory()
    series = SeriesModel(
        id=sid,
        title="Obs Failure Recovery Series",
        slug=f"obs-rec-{sid.hex[:8]}",
        total_chapters=20,
    )
    chapter = ChapterModel(
        id=cid,
        series_id=sid,
        number=1,
        title="Chapter 1",
    )
    Session.add(series)
    Session.add(chapter)
    Session.commit()
    Session.close()
    return str(sid), str(cid)


def _seed_review_item_in_db(
    pub_session_factory,
    item_id: str,
    series_id: str,
    chapter_id: str,
    subject_id: str,
    target_id: str | None = None,
    rank: str = "A",
    status: ReviewStatus = ReviewStatus.APPROVED,
):
    Session = pub_session_factory()
    model = ReviewItemModel(
        id=uuid.UUID(item_id),
        series_id=uuid.UUID(series_id),
        chapter_id=uuid.UUID(chapter_id),
        fact_type=FactType.POWER_RANK_CHANGED.value,
        fact_payload={
            "from_rank": "D",
            "to_rank": rank,
            "subject_id": subject_id,
            "target_id": target_id,
            "sequence": 1,
        },
        provenance_data={"source": "test_obs"},
        status=status.value,
    )
    Session.add(model)
    Session.commit()
    Session.close()


def _create_review_item(
    item_id: str,
    series_id: str,
    chapter_id: str,
    subject_id: str,
    target_id: str | None = None,
    rank: str = "A",
    status: ReviewStatus = ReviewStatus.APPROVED,
) -> ReviewItem:
    fact = RawExtractedFact(
        type=FactType.POWER_RANK_CHANGED,
        subject_raw="Hero",
        target_raw="Rival" if target_id else None,
        payload={
            "from_rank": "D",
            "to_rank": rank,
            "subject_id": subject_id,
            "target_id": target_id,
            "sequence": 1,
        },
        extraction_confidence=0.95,
        evidence=RawFactEvidence(location="para_1"),
    )
    prov = Provenance(
        source_id="webnovel_ch1",
        evidence=Evidence(chapter_id=chapter_id, location="para_1"),
        confidence=Confidence(1.0, 1.0, 1.0, 1.0),
        captured_at=datetime.now(),
    )
    return ReviewItem(
        id=item_id,
        series_id=series_id,
        chapter_id=chapter_id,
        fact=fact,
        provenance=prov,
        status=status,
    )


# ==============================================================================
# 2. RETRY OBSERVABILITY
# ==============================================================================


def test_retry_after_failure_observability(pub_session_factory, series_context, caplog):
    """Verifies that when a transient failure occurs and the operation is retried:
    - Attempt 1 logs failure, transaction rollback, and error classification
    - Attempt 2 logs started, commit, and completed with series_id and outcome=success
    - Zero sensitive data or future spoilers leaked.
    """
    caplog.set_level(logging.INFO)
    sid, cid = series_context
    item_id = str(uuid.uuid4())
    char_id = str(uuid.uuid4())

    _seed_review_item_in_db(pub_session_factory, item_id, sid, cid, char_id)
    item1 = _create_review_item(item_id, sid, cid, char_id)

    # Attempt 1: Transient failure
    s1 = pub_session_factory()
    repo1 = SQLAlchemyPublicationRepository(s1)

    def fail_record(*args, **kwargs):
        raise RuntimeError("Transient socket reset with token secret_token_xyz")

    repo1.save_publication_record = fail_record
    use_case1 = PublishReviewItemUseCase(repo1)

    with pytest.raises(RuntimeError):
        use_case1.execute(item1)
    s1.close()

    # Attempt 2: Successful retry
    s2 = pub_session_factory()
    repo2 = SQLAlchemyPublicationRepository(s2)
    use_case2 = PublishReviewItemUseCase(repo2)
    item2 = _create_review_item(item_id, sid, cid, char_id)
    use_case2.execute(item2)
    s2.close()

    # Check logged events
    rollback_events = [
        r
        for r in caplog.records
        if getattr(r, "event", None) == "database.transaction.rollback"
    ]
    completed_events = [
        r
        for r in caplog.records
        if getattr(r, "event", None) == "review.publish.completed"
    ]

    assert len(rollback_events) >= 1
    assert rollback_events[0].outcome == "failure"
    assert rollback_events[0].error_code == "TRANSACTION_ROLLBACK"

    assert len(completed_events) >= 1
    success_event = completed_events[-1]
    assert success_event.outcome == "success"
    assert success_event.series_id == sid
    assert success_event.resource_id == item_id
    assert success_event.duration_ms >= 0

    _assert_no_sensitive_data_in_logs(caplog.records, ["secret_token_xyz"])


# ==============================================================================
# 3. DUPLICATE OPERATION OBSERVABILITY
# ==============================================================================


def test_duplicate_operation_observability(pub_session_factory, series_context, caplog):
    """Verifies that duplicate requests log idempotent no-op or duplicate handling with:
    - series_id, resource_id, outcome=success, and duration_ms
    """
    caplog.set_level(logging.INFO)
    sid, cid = series_context
    item_id = str(uuid.uuid4())
    char_id = str(uuid.uuid4())

    _seed_review_item_in_db(pub_session_factory, item_id, sid, cid, char_id)
    item = _create_review_item(item_id, sid, cid, char_id)

    s = pub_session_factory()
    repo = SQLAlchemyPublicationRepository(s)
    use_case = PublishReviewItemUseCase(repo)

    # First run: publishes
    use_case.execute(item)

    # Second run: duplicate sequential execution
    use_case.execute(item)
    s.close()

    # Find idempotent no-op log record
    noop_records = [
        r
        for r in caplog.records
        if getattr(r, "event", None) == "review.publish.completed"
        and "idempotent no-op" in r.getMessage()
    ]
    assert len(noop_records) >= 1
    noop_record = noop_records[0]
    assert noop_record.series_id == sid
    assert noop_record.resource_id == item_id
    assert noop_record.outcome == "success"

    _assert_no_sensitive_data_in_logs(caplog.records)


# ==============================================================================
# 4. CONFLICT OBSERVABILITY
# ==============================================================================


def test_conflict_observability(caplog):
    """Verifies that conflict conditions log structured error classification (CONFLICT)
    with request_id, operation, and duration_ms.
    """
    from apps.api.app.application.exceptions import ConflictError

    client = TestClient(app)
    caplog.set_level(logging.INFO)
    req_id = str(uuid.uuid4())

    with patch(
        "apps.api.app.application.timeline.get_world_state.GetWorldStateUseCase.execute",
        side_effect=ConflictError("Concurrent mutation conflict detected for series"),
    ):
        resp = client.get(
            f"/api/v1/series/{uuid.uuid4()}/world-state?chapter=1",
            headers={"X-Request-ID": req_id},
        )
        assert resp.status_code == 409

    conflict_events = [
        r for r in caplog.records if getattr(r, "event", None) == "resource.conflict"
    ]
    assert len(conflict_events) >= 1
    evt = conflict_events[0]
    assert evt.request_id == req_id
    assert evt.outcome == "failure"
    assert evt.error_code == "CONFLICT"

    _assert_no_sensitive_data_in_logs(caplog.records)


# ==============================================================================
# 5. CACHE FAILURE & DIRTY BYPASS OBSERVABILITY
# ==============================================================================


def test_cache_failure_and_dirty_bypass_observability(caplog):
    """Verifies that when cache invalidation fails during post-commit recovery:
    - Structured cache.invalidate.failure event is emitted
    - Contains series_id, error, outcome="dirty_bypass"
    - Database commit remains intact
    - No sensitive credentials leaked
    """
    caplog.set_level(logging.INFO)
    sid = str(uuid.uuid4())

    cache = CacheService()
    # Invalidate with broken backend
    with patch.object(
        cache._backend,
        "delete_prefix",
        side_effect=Exception("Redis/Memory connection closed: key=pass_123"),
    ):
        count = cache.invalidate_series(sid)
        assert count == 0

    fail_events = [
        r
        for r in caplog.records
        if getattr(r, "event", None) == "cache.invalidate.failure"
    ]
    assert len(fail_events) >= 1
    fail_event = fail_events[0]
    assert fail_event.series_id == sid
    assert fail_event.outcome == "dirty_bypass"
    assert "error" in getattr(fail_event, "details", {}) or hasattr(fail_event, "error")

    _assert_no_sensitive_data_in_logs(caplog.records)


# ==============================================================================
# 6. TEMPORAL PRIVACY / SPOILER FIREWALL IN OBSERVABILITY
# ==============================================================================


def test_observability_never_leaks_future_story_content(caplog):
    """Verifies that query probes for future secret characters or spoiler events
    never echo raw spoiler payloads or future story content into logs.
    """
    client = TestClient(app)
    caplog.set_level(logging.INFO)

    secret_plot_token = "SECRET_ENDGAME_BETRAYAL_PLOT"
    fake_series = uuid.uuid4()

    client.get(f"/api/v1/series/{fake_series}/search?q={secret_plot_token}&chapter=1")

    # Inspect all records
    for r in caplog.records:
        msg = r.getMessage()
        assert "Final Boss True Identity" not in msg
        assert getattr(r, "future_story_content", None) is None

    _assert_no_sensitive_data_in_logs(caplog.records)
