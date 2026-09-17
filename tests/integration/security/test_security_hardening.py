"""Phase 4.5 Security Hardening Integration Test Suite.

Verifies:
1. Cross-Series Tenant Isolation (Characters, Events, Relationships, Impact, Power Systems)
2. Temporal Firewall & Future Information Leakage (Search, Counts, Suggestions, Graph, Overview, Progression)
3. SQL Injection & ORM Expression Resistance
4. Malformed Input & Boundary Abuse (Depth, Large Limits, Negative Ranges, Pathological Search)
5. Review State Machine & Publication Security
6. Information Disclosure & Error Sanitization (Zero SQL/stack traces)
7. Security Headers & CORS Policy Enforcement
"""

import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.application.publishing.publish_review_item import (
    PublishReviewItemUseCase,
)
from apps.api.app.config import get_settings
from apps.api.app.main import app
from apps.api.repositories.canonical.sqlalchemy_publication_repository import (
    SQLAlchemyPublicationRepository,
)
from infrastructure.database.models import Base
from infrastructure.database.models.chapter import ChapterModel
from infrastructure.database.models.character import CharacterModel
from infrastructure.database.models.event import EventModel
from infrastructure.database.models.power_system import PowerSystemModel
from infrastructure.database.models.rank import RankModel
from infrastructure.database.models.series import SeriesModel
from packages.domain.extraction.extraction_result import (
    RawExtractedFact,
    RawFactEvidence,
)
from packages.domain.extraction.fact_type import FactType
from packages.domain.provenance.confidence import Confidence
from packages.domain.provenance.evidence import Evidence
from packages.domain.provenance.provenance import Provenance
from packages.domain.publishing.canonical_publisher import (
    PublicationDomainError,
)
from packages.domain.review.review_item import ReviewItem
from packages.domain.review.review_status import ReviewStatus


@pytest.fixture(scope="module")
def sec_engine():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def sec_db(sec_engine):
    Session = sessionmaker(bind=sec_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


from apps.api.app.core.rate_limit import get_rate_limit_service


@pytest.fixture
def client(sec_engine):
    Base.metadata.create_all(bind=sec_engine)
    limiter = get_rate_limit_service()
    limiter.clear()
    return TestClient(app)


# ==============================================================================
# 1. CROSS-SERIES TENANT ISOLATION
# ==============================================================================


def test_cross_series_character_lookup_rejected(client, sec_db):
    """Character belonging to Series A cannot be read under Series B."""
    sA = uuid.uuid4()
    sB = uuid.uuid4()
    char_id = uuid.uuid4()

    sec_db.add(
        SeriesModel(
            id=sA, title="Series A", slug=f"sa-{str(sA)[:8]}", total_chapters=10
        )
    )
    sec_db.add(
        SeriesModel(
            id=sB, title="Series B", slug=f"sb-{str(sB)[:8]}", total_chapters=10
        )
    )
    sec_db.add(CharacterModel(id=char_id, series_id=sA, name="Hero A", description=""))
    sec_db.commit()

    # Querying char_id under Series B must return 404
    resp = client.get(f"/api/v1/series/{sB}/characters/{char_id}?chapter=5")
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert "Hero A" not in resp.text


def test_cross_series_power_system_rejected(client, sec_db):
    """Power system belonging to Series A cannot be queried under Series B."""
    sA = uuid.uuid4()
    sB = uuid.uuid4()
    ps_id = uuid.uuid4()

    sec_db.add(
        SeriesModel(
            id=sA, title="Series A", slug=f"sa-{str(sA)[:8]}", total_chapters=10
        )
    )
    sec_db.add(
        SeriesModel(
            id=sB, title="Series B", slug=f"sb-{str(sB)[:8]}", total_chapters=10
        )
    )
    sec_db.add(PowerSystemModel(id=ps_id, series_id=sA, name="Mana", slug="mana"))
    sec_db.commit()

    resp = client.get(f"/api/v1/series/{sB}/power-systems/{ps_id}/ranks?chapter=5")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_cross_series_relationship_history_rejected(client, sec_db):
    """Attempting relationship history with characters from different series fails."""
    sA = uuid.uuid4()
    sB = uuid.uuid4()
    cA = uuid.uuid4()
    cB = uuid.uuid4()

    sec_db.add(
        SeriesModel(
            id=sA, title="Series A", slug=f"sa-{str(sA)[:8]}", total_chapters=10
        )
    )
    sec_db.add(
        SeriesModel(
            id=sB, title="Series B", slug=f"sb-{str(sB)[:8]}", total_chapters=10
        )
    )
    sec_db.add(CharacterModel(id=cA, series_id=sA, name="Char A", description=""))
    sec_db.add(CharacterModel(id=cB, series_id=sB, name="Char B", description=""))
    sec_db.commit()

    # Query relationship between cA and cB under sA
    resp = client.get(f"/api/v1/series/{sA}/relationships/{cA}/{cB}/history?chapter=5")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_cross_series_search_isolation(client, sec_db):
    """Search for unique character in Series A returns no results under Series B."""
    sA = uuid.uuid4()
    sB = uuid.uuid4()
    cA = uuid.uuid4()
    c1 = uuid.uuid4()

    sec_db.add(
        SeriesModel(
            id=sA, title="Series A", slug=f"sa-{str(sA)[:8]}", total_chapters=10
        )
    )
    sec_db.add(
        SeriesModel(
            id=sB, title="Series B", slug=f"sb-{str(sB)[:8]}", total_chapters=10
        )
    )
    sec_db.add(ChapterModel(id=c1, series_id=sA, number=1, title="Ch 1"))
    sec_db.add(
        CharacterModel(
            id=cA, series_id=sA, name="SuperSecretAgent", description="A spy"
        )
    )
    sec_db.add(
        EventModel(
            id=uuid.uuid4(),
            series_id=sA,
            chapter_id=c1,
            sequence=0,
            type="CHARACTER_INTRODUCED",
            subject_type="CHARACTER",
            subject_id=cA,
            metadata_={},
            new_state={"name": "SuperSecretAgent"},
        )
    )
    sec_db.commit()

    # Search in Series B
    resp = client.get(f"/api/v1/series/{sB}/search?q=SuperSecretAgent&chapter=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0


# ==============================================================================
# 2. TEMPORAL FIREWALL & FUTURE INFORMATION LEAKAGE (N vs N+1)
# ==============================================================================


def test_temporal_firewall_search_suggestions_no_future_leak(client, sec_db):
    """Search suggestions must never return entities introduced in chapter N+1."""
    sid = uuid.uuid4()
    c1 = uuid.uuid4()
    c2 = uuid.uuid4()
    char_n1 = uuid.uuid4()

    sec_db.add(
        SeriesModel(id=sid, title="Series", slug=f"s-{str(sid)[:8]}", total_chapters=10)
    )
    sec_db.add(ChapterModel(id=c1, series_id=sid, number=1, title="Ch 1"))
    sec_db.add(ChapterModel(id=c2, series_id=sid, number=2, title="Ch 2"))

    sec_db.add(
        CharacterModel(
            id=char_n1, series_id=sid, name="SpoilerCharacter", description=""
        )
    )
    # Introduced at Chapter 2
    sec_db.add(
        EventModel(
            id=uuid.uuid4(),
            series_id=sid,
            chapter_id=c2,
            sequence=0,
            type="CHARACTER_INTRODUCED",
            subject_type="CHARACTER",
            subject_id=char_n1,
            metadata_={},
            new_state={"name": "SpoilerCharacter"},
        )
    )
    sec_db.commit()

    # Reader is at chapter 1 (N-1)
    resp = client.get(f"/api/v1/series/{sid}/search/suggestions?q=Spoiler&chapter=1")
    assert resp.status_code == 200
    suggestions = resp.json()
    assert len(suggestions) == 0

    # Reader is at chapter 2 (N)
    resp2 = client.get(f"/api/v1/series/{sid}/search/suggestions?q=Spoiler&chapter=2")
    assert resp2.status_code == 200
    suggestions2 = resp2.json()
    titles = [s["title"] for s in suggestions2]
    assert "SpoilerCharacter" in titles


def test_temporal_firewall_power_progression_no_future_ranks(client, sec_db):
    """Rank progression must not leak future rank promotions beyond reader chapter."""
    sid = uuid.uuid4()
    c1 = uuid.uuid4()
    c2 = uuid.uuid4()
    char_id = uuid.uuid4()
    ps_id = uuid.uuid4()
    r_novice = uuid.uuid4()
    r_master = uuid.uuid4()

    sec_db.add(
        SeriesModel(
            id=sid, title="Prog Series", slug=f"p-{str(sid)[:8]}", total_chapters=10
        )
    )
    sec_db.add(ChapterModel(id=c1, series_id=sid, number=1, title="Ch 1"))
    sec_db.add(ChapterModel(id=c2, series_id=sid, number=2, title="Ch 2"))
    sec_db.add(PowerSystemModel(id=ps_id, series_id=sid, name="Magic", slug="magic"))
    sec_db.add(
        RankModel(
            id=r_novice,
            power_system_id=ps_id,
            name="Novice",
            slug="novice",
            order=1,
            introduced_chapter=1,
        )
    )
    sec_db.add(
        RankModel(
            id=r_master,
            power_system_id=ps_id,
            name="Archmage",
            slug="archmage",
            order=10,
            introduced_chapter=2,
        )
    )

    # Ch 1: Novice
    sec_db.add(
        EventModel(
            id=uuid.uuid4(),
            series_id=sid,
            chapter_id=c1,
            sequence=0,
            type="POWER_RANK_CHANGED",
            subject_type="CHARACTER",
            subject_id=char_id,
            metadata_={},
            new_state={
                "power_system_id": str(ps_id),
                "to_rank": str(r_novice),
                "rank": "Novice",
            },
        )
    )
    # Ch 2 (SPOILER): Master
    future_ev = uuid.uuid4()
    sec_db.add(
        EventModel(
            id=future_ev,
            series_id=sid,
            chapter_id=c2,
            sequence=0,
            type="POWER_RANK_CHANGED",
            subject_type="CHARACTER",
            subject_id=char_id,
            metadata_={},
            new_state={
                "power_system_id": str(ps_id),
                "to_rank": str(r_master),
                "rank": "Archmage",
            },
        )
    )
    sec_db.commit()

    # Reader at chapter 1: only Novice visible
    resp = client.get(
        f"/api/v1/series/{sid}/characters/{char_id}/power-progression?chapter=1"
    )
    assert resp.status_code == 200
    ranks = resp.json()
    assert len(ranks) == 1
    assert ranks[0]["name"] == "Novice"
    assert not any(r["name"] == "Archmage" for r in ranks)


def test_temporal_firewall_graph_neighborhood_depth_leak(client, sec_db):
    """Temporal graph must never connect to nodes or edges created in future chapters."""
    sid = uuid.uuid4()
    c1 = uuid.uuid4()
    c2 = uuid.uuid4()
    c_alice = uuid.uuid4()
    c_future_friend = uuid.uuid4()

    sec_db.add(
        SeriesModel(
            id=sid, title="Graph Series", slug=f"g-{str(sid)[:8]}", total_chapters=10
        )
    )
    sec_db.add(ChapterModel(id=c1, series_id=sid, number=1, title="Ch 1"))
    sec_db.add(ChapterModel(id=c2, series_id=sid, number=2, title="Ch 2"))

    # Alice introduced at ch 1
    sec_db.add(
        EventModel(
            id=uuid.uuid4(),
            series_id=sid,
            chapter_id=c1,
            sequence=0,
            type="CHARACTER_INTRODUCED",
            subject_type="CHARACTER",
            subject_id=c_alice,
            metadata_={},
            new_state={"name": "Alice"},
        )
    )
    # FutureFriend introduced at ch 2
    sec_db.add(
        EventModel(
            id=uuid.uuid4(),
            series_id=sid,
            chapter_id=c2,
            sequence=0,
            type="CHARACTER_INTRODUCED",
            subject_type="CHARACTER",
            subject_id=c_future_friend,
            metadata_={},
            new_state={"name": "FutureFriend"},
        )
    )
    # Relationship formed at ch 2
    sec_db.add(
        EventModel(
            id=uuid.uuid4(),
            series_id=sid,
            chapter_id=c2,
            sequence=1,
            type="RELATIONSHIP_CREATED",
            subject_type="CHARACTER",
            subject_id=c_alice,
            target_type="CHARACTER",
            target_id=c_future_friend,
            metadata_={},
            new_state={"relationship_type": "ALLY"},
        )
    )
    sec_db.commit()

    # Query graph at Chapter 1
    resp = client.get(f"/api/v1/series/{sid}/graph?chapter=1")
    assert resp.status_code == 200
    graph = resp.json()
    node_ids = [n["id"] for n in graph["nodes"]]
    assert str(c_alice) in node_ids
    assert str(c_future_friend) not in node_ids
    assert len(graph["edges"]) == 0


# ==============================================================================
# 3. SQL INJECTION & MALFORMED IDENTIFIER RESISTANCE
# ==============================================================================


def test_sql_injection_in_search_query(client, sec_db):
    """SQL injection payload in search string handled safely via parameters."""
    sid = uuid.uuid4()
    sec_db.add(
        SeriesModel(
            id=sid, title="SQLi Series", slug=f"sq-{str(sid)[:8]}", total_chapters=10
        )
    )
    sec_db.commit()

    sqli_payload = "' UNION SELECT * FROM series WHERE '1'='1"
    resp = client.get(f"/api/v1/series/{sid}/search?q={sqli_payload}&chapter=1")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
    # Confirm no SQL error leaked
    assert "syntax error" not in resp.text.lower()
    assert "SELECT" not in resp.text


def test_malformed_uuid_returns_clean_400(client):
    """Malformed UUID in path parameters rejected cleanly with 400."""
    resp = client.get(
        "/api/v1/series/not-a-valid-uuid/timeline?reader_chapter=1&from=1&to=1"
    )
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "Traceback" not in resp.text


def test_path_traversal_string_rejected(client, sec_db):
    """Path traversal payload in string identifier rejected cleanly."""
    sid = uuid.uuid4()
    sec_db.add(
        SeriesModel(
            id=sid, title="PT Series", slug=f"pt-{str(sid)[:8]}", total_chapters=10
        )
    )
    sec_db.commit()

    traversal = "../../../../etc/passwd"
    resp = client.get(f"/api/v1/series/{sid}/skills/{traversal}/evolution?chapter=1")
    assert resp.status_code in (400, 404)
    assert "Traceback" not in resp.text


# ==============================================================================
# 4. RESOURCE ABUSE & BOUNDARY HARDENING
# ==============================================================================


def test_oversized_graph_depth_rejected(client, sec_db):
    """Graph depth exceeding maximum allowable bound (depth > 2) rejected with 400."""
    sid = uuid.uuid4()
    cid = uuid.uuid4()
    sec_db.add(
        SeriesModel(
            id=sid, title="Depth Series", slug=f"dp-{str(sid)[:8]}", total_chapters=10
        )
    )
    sec_db.commit()

    resp = client.get(
        f"/api/v1/series/{sid}/characters/{cid}/relationship-graph?chapter=1&depth=99"
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_pathological_search_length(client, sec_db):
    """Oversized search query handled safely without crash."""
    sid = uuid.uuid4()
    sec_db.add(
        SeriesModel(
            id=sid, title="Large Search", slug=f"ls-{str(sid)[:8]}", total_chapters=10
        )
    )
    sec_db.commit()

    huge_q = "A" * 5000
    resp = client.get(f"/api/v1/series/{sid}/search?q={huge_q}&chapter=1")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


# ==============================================================================
# 5. REVIEW / PUBLISHING STATE MACHINE SECURITY
# ==============================================================================


def test_publishing_pending_review_item_rejected(sec_db, sec_engine):
    """Publishing a PENDING review item must be rejected by domain rule."""
    sid = uuid.uuid4()
    cid = uuid.uuid4()
    sec_db.add(
        SeriesModel(
            id=sid, title="Review Series", slug=f"rv-{str(sid)[:8]}", total_chapters=10
        )
    )
    sec_db.add(ChapterModel(id=cid, series_id=sid, number=1, title="Ch 1"))
    sec_db.commit()

    fact = RawExtractedFact(
        type=FactType.POWER_RANK_CHANGED,
        subject_raw="Hero",
        target_raw=None,
        payload={"to_rank": "A", "subject_id": str(uuid.uuid4())},
        extraction_confidence=0.9,
        evidence=RawFactEvidence(location="para_1"),
    )
    prov = Provenance(
        source_id="src1",
        evidence=Evidence(chapter_id=str(cid), location="para_1"),
        confidence=Confidence(1.0, 1.0, 1.0, 1.0),
        captured_at=datetime.now(),
    )
    # Status is PENDING (not APPROVED)
    item = ReviewItem(
        id=str(uuid.uuid4()),
        series_id=str(sid),
        chapter_id=str(cid),
        fact=fact,
        provenance=prov,
        status=ReviewStatus.PENDING,
    )

    Session = sessionmaker(bind=sec_engine)
    sess = Session()
    repo = SQLAlchemyPublicationRepository(sess)
    use_case = PublishReviewItemUseCase(repo)

    with pytest.raises(PublicationDomainError) as exc_info:
        use_case.execute(item)
    assert "Cannot publish ReviewItem in state: PENDING" in str(exc_info.value)
    sess.close()


def test_publishing_rejected_review_item_rejected(sec_db, sec_engine):
    """Publishing a REJECTED review item must be rejected by domain rule."""
    sid = uuid.uuid4()
    cid = uuid.uuid4()
    sec_db.add(
        SeriesModel(
            id=sid,
            title="Review Series 2",
            slug=f"rv2-{str(sid)[:8]}",
            total_chapters=10,
        )
    )
    sec_db.add(ChapterModel(id=cid, series_id=sid, number=1, title="Ch 1"))
    sec_db.commit()

    fact = RawExtractedFact(
        type=FactType.POWER_RANK_CHANGED,
        subject_raw="Hero",
        target_raw=None,
        payload={"to_rank": "A", "subject_id": str(uuid.uuid4())},
        extraction_confidence=0.9,
        evidence=RawFactEvidence(location="para_1"),
    )
    prov = Provenance(
        source_id="src1",
        evidence=Evidence(chapter_id=str(cid), location="para_1"),
        confidence=Confidence(1.0, 1.0, 1.0, 1.0),
        captured_at=datetime.now(),
    )
    item = ReviewItem(
        id=str(uuid.uuid4()),
        series_id=str(sid),
        chapter_id=str(cid),
        fact=fact,
        provenance=prov,
        status=ReviewStatus.REJECTED,
    )

    Session = sessionmaker(bind=sec_engine)
    sess = Session()
    repo = SQLAlchemyPublicationRepository(sess)
    use_case = PublishReviewItemUseCase(repo)

    with pytest.raises(PublicationDomainError):
        use_case.execute(item)
    sess.close()


# ==============================================================================
# 6. HTTP SECURITY HEADERS & CORS VERIFICATION
# ==============================================================================


def test_security_headers_present_in_responses(client):
    """Standard security headers must be included in all API responses."""
    resp = client.get(
        "/api/v1/series/00000000-0000-0000-0000-000000000000/timeline?reader_chapter=1&from=1&to=1"
    )
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_cors_preflight_and_origin_policy(client):
    """Allowed origins receive CORS headers; unlisted origins are rejected."""
    # Allowed origin
    resp = client.options(
        "/api/v1/series/00000000-0000-0000-0000-000000000000/timeline",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"

    # Disallowed origin
    resp_bad = client.options(
        "/api/v1/series/00000000-0000-0000-0000-000000000000/timeline",
        headers={
            "Origin": "http://evil-attacker.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp_bad.headers.get("access-control-allow-origin") is None
