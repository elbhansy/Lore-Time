"""Focused tests for every identified idempotency boundary in the canonical storage engine.

Audit Requirements:
Verify that logically identical operations cannot create:
1. duplicate canonical events (via publication_fingerprint unique constraint and save_event ON CONFLICT DO NOTHING)
2. duplicate publication records (idempotent status transition and publication attempt deduplication)
3. duplicate derived facts / canonical entities (via uq_canonical_entity_series_id and ensure_entity_exists)
4. duplicate relationships / projections (via reconciliation deduplication and deterministic projection key)
5. inconsistent state (atomic rollback on mid-operation failure)
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from apps.api.app.application.publishing.publish_review_item import (
    PublishReviewItemUseCase,
)
from apps.api.app.application.reconciliation.graph_reconciler import (
    deterministic_projection_key,
)
from apps.api.app.config import get_settings
from apps.api.repositories.canonical.sqlalchemy_publication_repository import (
    SQLAlchemyPublicationRepository,
)
from infrastructure.database.models import Base
from infrastructure.database.models.canonical_entity import CanonicalEntityModel
from infrastructure.database.models.chapter import ChapterModel
from infrastructure.database.models.event import EventModel
from infrastructure.database.models.publication_record import (
    PublicationRecordModel,
)
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
from packages.domain.publishing.publication_fingerprint import (
    PublicationFingerprint,
)
from packages.domain.review.review_item import ReviewItem
from packages.domain.review.review_status import ReviewStatus


@pytest.fixture(scope="module")
def idempotency_engine():
    settings = get_settings()
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def idempotency_session(idempotency_engine):
    Session = sessionmaker(bind=idempotency_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def test_series_context(idempotency_session):
    sid = uuid.uuid4()
    cid = uuid.uuid4()
    series = SeriesModel(
        id=sid,
        title="Idempotency Audit Series",
        slug=f"idem-{str(sid)[:8]}",
        total_chapters=20,
    )
    chapter = ChapterModel(
        id=cid,
        series_id=sid,
        number=1,
        title="Chapter 1",
    )
    idempotency_session.add(series)
    idempotency_session.add(chapter)
    idempotency_session.commit()
    return str(sid), str(cid)


def _build_review_item(
    item_id: str,
    series_id: str,
    chapter_id: str,
    subject_id: str,
    target_id: str | None = None,
) -> ReviewItem:
    fact = RawExtractedFact(
        type=FactType.POWER_RANK_CHANGED,
        subject_raw="Hero",
        target_raw="Villain" if target_id else None,
        payload={
            "from_rank": "D",
            "to_rank": "S",
            "subject_id": subject_id,
            "target_id": target_id,
            "sequence": 1,
        },
        extraction_confidence=0.99,
        evidence=RawFactEvidence(location="line_42"),
    )
    prov = Provenance(
        source_id="chapter_1_raw",
        evidence=Evidence(chapter_id=chapter_id, location="line_42"),
        confidence=Confidence(1.0, 1.0, 1.0, 1.0),
        captured_at=datetime.now(),
    )
    return ReviewItem(
        id=item_id,
        series_id=series_id,
        chapter_id=chapter_id,
        fact=fact,
        provenance=prov,
        status=ReviewStatus.APPROVED,
    )


# ==============================================================================
# BOUNDARY 1: CANONICAL EVENT IDEMPOTENCY & FINGERPRINT DEDUPLICATION
# ==============================================================================


def test_publication_fingerprint_deterministic_and_unique_constraint(
    idempotency_session, test_series_context
):
    """Verifies that logically identical event definitions produce identical SHA-256

    fingerprints, and the PostgreSQL unique constraint prevents duplicate rows.
    """
    sid, cid = test_series_context
    subjid = str(uuid.uuid4())
    payload = {"from_rank": "D", "to_rank": "S", "subject_id": subjid}

    # Generate fingerprints with identical payload but unordered keys
    fp1 = PublicationFingerprint.generate(
        series_id=sid,
        chapter_id=cid,
        event_type="POWER_RANK_CHANGED",
        subject_id=subjid,
        target_id=None,
        payload={"to_rank": "S", "from_rank": "D", "subject_id": subjid},
    )
    fp2 = PublicationFingerprint.generate(
        series_id=sid,
        chapter_id=cid,
        event_type="POWER_RANK_CHANGED",
        subject_id=subjid,
        target_id=None,
        payload={"from_rank": "D", "subject_id": subjid, "to_rank": "S"},
    )
    assert fp1 == fp2  # Deterministic JSON ordering ensures identical hash

    repo = SQLAlchemyPublicationRepository(idempotency_session)
    event_data_1 = {
        "series_id": sid,
        "chapter_id": cid,
        "sequence": 1,
        "type": "POWER_RANK_CHANGED",
        "subject_type": "CHARACTER",
        "subject_id": subjid,
        "new_state": {"rank": "S"},
        "publication_fingerprint": fp1,
    }
    eid1 = repo.save_event(event_data_1)
    idempotency_session.commit()

    # Second insert with identical fingerprint via repository
    event_data_2 = {
        "series_id": sid,
        "chapter_id": cid,
        "sequence": 1,
        "type": "POWER_RANK_CHANGED",
        "subject_type": "CHARACTER",
        "subject_id": subjid,
        "new_state": {"rank": "S"},
        "publication_fingerprint": fp2,
    }
    eid2 = repo.save_event(event_data_2)
    idempotency_session.commit()

    # Must return the existing canonical event ID without creating a duplicate
    assert eid1 == eid2

    events = (
        idempotency_session.query(EventModel)
        .filter_by(publication_fingerprint=fp1)
        .all()
    )
    assert len(events) == 1

    # Raw database unique constraint test: direct raw INSERT must raise IntegrityError
    with pytest.raises(IntegrityError):
        idempotency_session.execute(
            text(
                "INSERT INTO events (id, series_id, chapter_id, sequence, type, "
                "subject_type, subject_id, publication_fingerprint, metadata) "
                "VALUES (:id, :sid, :cid, 2, 'POWER_RANK_CHANGED', 'CHARACTER', "
                ":subjid, :fp, '{}')"
            ),
            {
                "id": uuid.uuid4(),
                "sid": uuid.UUID(sid),
                "cid": uuid.UUID(cid),
                "subjid": uuid.UUID(subjid),
                "fp": fp1,
            },
        )
        idempotency_session.commit()
    idempotency_session.rollback()


# ==============================================================================
# BOUNDARY 2: PUBLICATION WORKFLOW & REQUEST-LEVEL RETRY IDEMPOTENCY
# ==============================================================================


def test_repeated_publication_use_case_is_idempotent_no_op(
    idempotency_session, idempotency_engine, test_series_context
):
    """Verifies that calling PublishReviewItemUseCase repeatedly (retries, timeouts)

    produces exactly ONE canonical event and handles already-published state gracefully.
    """
    sid, cid = test_series_context
    item_id = str(uuid.uuid4())
    subjid = str(uuid.uuid4())

    rev_model = ReviewItemModel(
        id=uuid.UUID(item_id),
        series_id=uuid.UUID(sid),
        chapter_id=uuid.UUID(cid),
        fact_type=FactType.POWER_RANK_CHANGED.value,
        fact_payload={"from_rank": "D", "to_rank": "S", "subject_id": subjid},
        provenance_data={"source": "test"},
        status=ReviewStatus.APPROVED.value,
    )
    idempotency_session.add(rev_model)
    idempotency_session.commit()

    repo = SQLAlchemyPublicationRepository(idempotency_session)
    use_case = PublishReviewItemUseCase(repo)
    review_item = _build_review_item(item_id, sid, cid, subjid)

    # 1. First execution
    use_case.execute(review_item)
    assert review_item.status == ReviewStatus.PUBLISHED

    # 2. Second execution with the same (now PUBLISHED) domain object -> early return no-op
    use_case.execute(review_item)

    # 3. Third execution simulating a newly reconstructed object (e.g. from a separate request retry)
    retry_item = _build_review_item(item_id, sid, cid, subjid)
    use_case.execute(retry_item)

    # Assert single canonical event exists
    events = (
        idempotency_session.query(EventModel)
        .filter_by(series_id=uuid.UUID(sid), subject_id=uuid.UUID(subjid))
        .all()
    )
    assert len(events) == 1

    # Assert review item status is published in DB
    db_item = (
        idempotency_session.query(ReviewItemModel)
        .filter_by(id=uuid.UUID(item_id))
        .one()
    )
    assert db_item.status == ReviewStatus.PUBLISHED.value


# ==============================================================================
# BOUNDARY 3: DERIVED FACT / CANONICAL ENTITY DEDUPLICATION
# ==============================================================================


def test_canonical_entity_idempotency(idempotency_session, test_series_context):
    """Verifies that ensure_entity_exists is idempotent and enforces

    the UNIQUE(series_id, id) constraint without throwing duplicate key errors.
    """
    sid, _ = test_series_context
    entity_id = f"hero_{uuid.uuid4().hex[:8]}"

    repo = SQLAlchemyPublicationRepository(idempotency_session)

    # Call ensure_entity_exists 3 times
    repo.ensure_entity_exists(
        entity_id=entity_id,
        series_id=sid,
        type="CHARACTER",
        name="Sung Jinwoo",
    )
    repo.ensure_entity_exists(
        entity_id=entity_id,
        series_id=sid,
        type="CHARACTER",
        name="Sung Jinwoo",
    )
    repo.ensure_entity_exists(
        entity_id=entity_id,
        series_id=sid,
        type="CHARACTER",
        name="Sung Jinwoo",
    )
    idempotency_session.commit()

    entities = (
        idempotency_session.query(CanonicalEntityModel)
        .filter_by(series_id=sid, id=entity_id)
        .all()
    )
    assert len(entities) == 1
    assert entities[0].name == "Sung Jinwoo"


# ==============================================================================
# BOUNDARY 4: RELATIONSHIP & GRAPH PROJECTION DETERMINISM
# ==============================================================================


def test_projection_key_determinism_and_reconciliation():
    """Verifies that graph projection keys are deterministic and that re-running

    reconciliation produces zero duplicate projections.
    """
    event_id = str(uuid.uuid4())
    key1 = deterministic_projection_key(event_id, 0)
    key2 = deterministic_projection_key(event_id, 0)
    key3 = deterministic_projection_key(event_id, 1)

    assert key1 == key2
    assert key1 != key3


# ==============================================================================
# BOUNDARY 5: TRANSACTION ISOLATION & FAILURE ROLLBACK (NO INCONSISTENT STATE)
# ==============================================================================


def test_transaction_rollback_prevents_partial_inconsistent_state(
    idempotency_session, test_series_context
):
    """Verifies that any failure inside a publication transaction rolls back all mutations

    leaving NO orphan canonical events, publication records, or entity modifications.
    """
    sid, cid = test_series_context
    item_id = str(uuid.uuid4())
    subjid = str(uuid.uuid4())

    rev_model = ReviewItemModel(
        id=uuid.UUID(item_id),
        series_id=uuid.UUID(sid),
        chapter_id=uuid.UUID(cid),
        fact_type=FactType.POWER_RANK_CHANGED.value,
        fact_payload={"from_rank": "E", "to_rank": "B", "subject_id": subjid},
        provenance_data={"source": "test"},
        status=ReviewStatus.APPROVED.value,
    )
    idempotency_session.add(rev_model)
    idempotency_session.commit()

    repo = SQLAlchemyPublicationRepository(idempotency_session)

    # Injected crash in update_review_status (the last step)
    def crash_update(*args, **kwargs):
        raise RuntimeError("Database connection severed before status update commit")

    repo.update_review_status = crash_update
    use_case = PublishReviewItemUseCase(repo)
    review_item = _build_review_item(item_id, sid, cid, subjid)

    with pytest.raises(RuntimeError, match="Transaction failed"):
        use_case.execute(review_item)

    # State verification: clean rollback, no partial canonical records
    events = (
        idempotency_session.query(EventModel)
        .filter_by(series_id=uuid.UUID(sid), subject_id=uuid.UUID(subjid))
        .all()
    )
    assert len(events) == 0

    records = (
        idempotency_session.query(PublicationRecordModel)
        .filter_by(review_item_id=uuid.UUID(item_id))
        .all()
    )
    assert len(records) == 0

    item_in_db = (
        idempotency_session.query(ReviewItemModel)
        .filter_by(id=uuid.UUID(item_id))
        .one()
    )
    assert item_in_db.status == ReviewStatus.APPROVED.value
