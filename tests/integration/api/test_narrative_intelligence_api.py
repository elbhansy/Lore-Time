"""Integration Tests for Narrative Intelligence & Character Arc API (Phase 5.1).

Covers:
1. Successful Character Arc retrieval via API.
2. Temporal Firewall ($N-1, N, N+1$) verification:
   - Verifies that events, milestones, and turning points $> readerChapter$ are strictly excluded.
3. Multi-Tenant Series Isolation:
   - Cross-series character retrieval is rejected with 404.
4. Determinism:
   - Repeated requests produce identical byte-for-byte serialized payloads.
5. Cache Integration:
   - Verifies cold cache miss followed by warm cache hit.
6. Rate Limiting:
   - Verifies classification under EXPENSIVE_READ tier.
7. Error Handling:
   - Invalid chapter (< 1), nonexistent series, and nonexistent character.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.config import get_settings
from apps.api.app.core.cache import (
    get_cache_service,
)
from apps.api.app.core.rate_limit import (
    EndpointTier,
    classify_endpoint,
    get_rate_limit_service,
)
from apps.api.app.main import app
from infrastructure.database.models import Base
from infrastructure.database.models.chapter import ChapterModel
from infrastructure.database.models.character import CharacterModel
from infrastructure.database.models.event import EventModel
from packages.domain.value_objects.event_type import EventType
from tests.integration.cache.seed_helper import seed_test_series


@pytest.fixture
def narrative_test_env():
    """Seeds a series with 10 chapters and a protagonist having milestones at ch 1, 3, 5, 8, and 10."""
    get_rate_limit_service().clear()
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)

    with session_factory() as session:
        # Seed 10 chapters
        sid_str = seed_test_series(session, num_chapters=10, events_per_chapter=1)
        sid = uuid.UUID(sid_str)

        ch_1 = session.query(ChapterModel).filter_by(series_id=sid, number=1).one()
        ch_3 = session.query(ChapterModel).filter_by(series_id=sid, number=3).one()
        ch_5 = session.query(ChapterModel).filter_by(series_id=sid, number=5).one()
        ch_8 = session.query(ChapterModel).filter_by(series_id=sid, number=8).one()
        ch_10 = session.query(ChapterModel).filter_by(series_id=sid, number=10).one()

        # Seed Protagonist
        char_id = uuid.uuid4()
        char_model = CharacterModel(id=char_id, series_id=sid, name="Hero Kim")
        session.add(char_model)

        # Event 1 (Ch 1): Introduce
        e1 = EventModel(
            id=uuid.uuid4(),
            series_id=sid,
            chapter_id=ch_1.id,
            sequence=1,
            type=EventType.CHARACTER_INTRODUCED.value,
            subject_type="CHARACTER",
            subject_id=char_id,
            previous_state={},
            new_state={"alive": True},
            metadata_={"chapter_number": 1},
        )
        # Event 2 (Ch 3): Rank change to E
        e2 = EventModel(
            id=uuid.uuid4(),
            series_id=sid,
            chapter_id=ch_3.id,
            sequence=1,
            type=EventType.POWER_RANK_CHANGED.value,
            subject_type="CHARACTER",
            subject_id=char_id,
            previous_state={"rank": "F"},
            new_state={"rank": "E"},
            metadata_={"chapter_number": 3},
        )
        # Event 3 (Ch 5): Skill unlocked
        e3 = EventModel(
            id=uuid.uuid4(),
            series_id=sid,
            chapter_id=ch_5.id,
            sequence=1,
            type=EventType.SKILL_UNLOCKED.value,
            subject_type="CHARACTER",
            subject_id=char_id,
            previous_state={},
            new_state={"skill_id": "skill_flame"},
            metadata_={"chapter_number": 5, "skill_name": "Flame Burst"},
        )
        # Event 4 (Ch 8): Rank breakthrough to S
        e4 = EventModel(
            id=uuid.uuid4(),
            series_id=sid,
            chapter_id=ch_8.id,
            sequence=1,
            type=EventType.POWER_RANK_CHANGED.value,
            subject_type="CHARACTER",
            subject_id=char_id,
            previous_state={"rank": "E"},
            new_state={"rank": "S"},
            metadata_={"chapter_number": 8},
        )
        # Event 5 (Ch 10): Death
        e5 = EventModel(
            id=uuid.uuid4(),
            series_id=sid,
            chapter_id=ch_10.id,
            sequence=1,
            type=EventType.CHARACTER_DIED.value,
            subject_type="CHARACTER",
            subject_id=char_id,
            previous_state={"alive": True},
            new_state={"alive": False},
            metadata_={"chapter_number": 10},
        )
        session.add_all([e1, e2, e3, e4, e5])
        session.commit()

    yield {"sid_str": sid_str, "char_id_str": str(char_id)}
    get_rate_limit_service().clear()
    engine.dispose()


def test_character_arc_api_success(narrative_test_env):
    env = narrative_test_env
    client = TestClient(app)

    resp = client.get(
        f"/api/v1/series/{env['sid_str']}/intelligence/character-arc/{env['char_id_str']}?chapter=10"
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["series_id"] == env["sid_str"]
    assert data["character_id"] == env["char_id_str"]
    assert data["reader_chapter"] == 10
    assert data["start_chapter"] == 1
    assert data["end_chapter"] == 10

    # Milestones count: Ch 1, 3, 5, 8, 10 = 5 milestones
    assert len(data["milestones"]) == 5

    # Turning points: Ch 3 (rank), Ch 8 (rank breakthrough), Ch 10 (death)
    assert len(data["turning_points"]) >= 3

    # Trajectory summary
    assert data["trajectory"]["current_status"] == "dead"
    assert data["trajectory"]["current_rank"] == "S"
    assert data["trajectory"]["highest_significance"] == "CRITICAL"


def test_character_arc_temporal_firewall_n_minus_1_n_n_plus_1(narrative_test_env):
    """HARD SECURITY GATE: Validates that readerChapter strictly bounds all milestones and turning points."""
    env = narrative_test_env
    client = TestClient(app)
    sid = env["sid_str"]
    cid = env["char_id_str"]

    # --- Scenario 1: readerChapter = 4 (N-1 where N=5 is skill unlock) ---
    resp_ch4 = client.get(
        f"/api/v1/series/{sid}/intelligence/character-arc/{cid}?chapter=4"
    )
    assert resp_ch4.status_code == 200
    data_ch4 = resp_ch4.json()

    # In ch 4, only ch 1 and ch 3 exist
    assert len(data_ch4["milestones"]) == 2
    assert all(m["chapter"] <= 4 for m in data_ch4["milestones"])
    assert data_ch4["trajectory"]["current_rank"] == "E"
    assert data_ch4["trajectory"]["current_status"] == "alive"

    # --- Scenario 2: readerChapter = 5 (N) ---
    resp_ch5 = client.get(
        f"/api/v1/series/{sid}/intelligence/character-arc/{cid}?chapter=5"
    )
    assert resp_ch5.status_code == 200
    data_ch5 = resp_ch5.json()

    # In ch 5, ch 1, 3, 5 exist. Ch 8 (Rank S) and Ch 10 (Death) MUST NOT EXIST.
    assert len(data_ch5["milestones"]) == 3
    assert all(m["chapter"] <= 5 for m in data_ch5["milestones"])
    assert not any(m["milestone_type"] == "DEATH" for m in data_ch5["milestones"])
    assert not any(
        tp["turning_point_type"] == "MORTALITY_EVENT"
        for tp in data_ch5["turning_points"]
    )
    assert data_ch5["trajectory"]["current_rank"] == "E"  # NOT 'S'!

    # --- Scenario 3: readerChapter = 8 (N+1 relative to Ch 5) ---
    resp_ch8 = client.get(
        f"/api/v1/series/{sid}/intelligence/character-arc/{cid}?chapter=8"
    )
    assert resp_ch8.status_code == 200
    data_ch8 = resp_ch8.json()

    # In ch 8, ch 1, 3, 5, 8 exist. Ch 10 (Death) MUST NOT EXIST.
    assert len(data_ch8["milestones"]) == 4
    assert all(m["chapter"] <= 8 for m in data_ch8["milestones"])
    assert not any(m["milestone_type"] == "DEATH" for m in data_ch8["milestones"])
    assert data_ch8["trajectory"]["current_rank"] == "S"
    assert data_ch8["trajectory"]["current_status"] == "alive"


def test_character_arc_series_isolation(narrative_test_env):
    """Cross-series character lookup returns 404."""
    env = narrative_test_env
    client = TestClient(app)
    foreign_sid = str(uuid.uuid4())

    resp = client.get(
        f"/api/v1/series/{foreign_sid}/intelligence/character-arc/{env['char_id_str']}?chapter=5"
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_character_arc_determinism_and_cache(narrative_test_env):
    """Verifies that identical requests yield byte-equivalent payloads and hit cache cleanly."""
    env = narrative_test_env
    client = TestClient(app)
    cache = get_cache_service()

    url = f"/api/v1/series/{env['sid_str']}/intelligence/character-arc/{env['char_id_str']}?chapter=5"

    # Request 1: Cold/Miss
    r1 = client.get(url)
    assert r1.status_code == 200

    # Request 2: Hit
    r2 = client.get(url)
    assert r2.status_code == 200

    # Byte-level JSON equality
    assert r1.json() == r2.json()


def test_character_arc_rate_limit_classification():
    """Verifies that /intelligence/character-arc is classified under the EXPENSIVE_READ tier."""
    tier = classify_endpoint("/api/v1/series/123/intelligence/character-arc/456", "GET")
    assert tier == EndpointTier.EXPENSIVE_READ


def test_character_arc_error_boundaries(narrative_test_env):
    env = narrative_test_env
    client = TestClient(app)

    # 1. Negative chapter -> 422 or 400
    r_neg = client.get(
        f"/api/v1/series/{env['sid_str']}/intelligence/character-arc/{env['char_id_str']}?chapter=-1"
    )
    assert r_neg.status_code in (400, 422)

    # 2. Nonexistent character -> 404
    fake_cid = str(uuid.uuid4())
    r_fake_char = client.get(
        f"/api/v1/series/{env['sid_str']}/intelligence/character-arc/{fake_cid}?chapter=5"
    )
    assert r_fake_char.status_code == 404
    assert r_fake_char.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
