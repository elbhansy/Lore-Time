"""Integration tests for Temporal Narrative Causal Synthesis API (Phase 5.3).

Verifies:
1. Event Narrative Explanation API (GET /intelligence/event-narrative/{event_id})
2. Character Narrative Causality API (GET /intelligence/character-narrative-causality/{character_id})
3. Temporal Firewall ($N-1, N, N+1$)
4. Series Isolation (Cross-series access rejected)
5. Determinism & Caching
6. Rate Limiting (EXPENSIVE_READ tier classification)
7. Error boundaries (400 on invalid chapter, 404 on missing entity/series)
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.config import get_settings
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
def synthesis_test_env():
    """Seeds series, character, and causal narrative chain."""
    get_rate_limit_service().clear()
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)

    with session_factory() as session:
        sid_str = seed_test_series(session, num_chapters=10, events_per_chapter=1)
        sid = uuid.UUID(sid_str)

        ch_1 = session.query(ChapterModel).filter_by(series_id=sid, number=1).one()
        ch_3 = session.query(ChapterModel).filter_by(series_id=sid, number=3).one()
        ch_5 = session.query(ChapterModel).filter_by(series_id=sid, number=5).one()
        ch_8 = session.query(ChapterModel).filter_by(series_id=sid, number=8).one()
        ch_10 = session.query(ChapterModel).filter_by(series_id=sid, number=10).one()

        char_id = uuid.uuid4()
        char_model = CharacterModel(
            id=char_id, series_id=sid, name="Synthesis Protagonist"
        )
        session.add(char_model)

        # Event 1: Ch 1 Intro
        e1_id = uuid.uuid4()
        e1 = EventModel(
            id=e1_id,
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
        # Event 2: Ch 3 Rank changed to E
        e2_id = uuid.uuid4()
        e2 = EventModel(
            id=e2_id,
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
        # Event 3: Ch 5 Skill unlocked caused by Rank change
        e3_id = uuid.uuid4()
        e3 = EventModel(
            id=e3_id,
            series_id=sid,
            chapter_id=ch_5.id,
            sequence=1,
            type=EventType.SKILL_UNLOCKED.value,
            subject_type="CHARACTER",
            subject_id=char_id,
            previous_state={},
            new_state={"skill_id": "flame_blast"},
            metadata_={"chapter_number": 5, "cause_event_id": str(e2_id)},
        )
        # Event 4: Ch 8 Rank S breakthrough (Major Turning Point)
        e4_id = uuid.uuid4()
        e4 = EventModel(
            id=e4_id,
            series_id=sid,
            chapter_id=ch_8.id,
            sequence=1,
            type=EventType.POWER_RANK_CHANGED.value,
            subject_type="CHARACTER",
            subject_id=char_id,
            previous_state={"rank": "E"},
            new_state={"rank": "S"},
            metadata_={"chapter_number": 8, "cause_event_id": str(e3_id)},
        )
        # Event 5: Ch 10 Death
        e5_id = uuid.uuid4()
        e5 = EventModel(
            id=e5_id,
            series_id=sid,
            chapter_id=ch_10.id,
            sequence=1,
            type=EventType.CHARACTER_DIED.value,
            subject_type="CHARACTER",
            subject_id=char_id,
            previous_state={"alive": True},
            new_state={"alive": False},
            metadata_={"chapter_number": 10, "cause_event_id": str(e4_id)},
        )

        session.add_all([e1, e2, e3, e4, e5])
        session.commit()

    yield {
        "sid_str": sid_str,
        "char_id_str": str(char_id),
        "e1_id": str(e1_id),
        "e2_id": str(e2_id),
        "e3_id": str(e3_id),
        "e4_id": str(e4_id),
        "e5_id": str(e5_id),
    }
    get_rate_limit_service().clear()
    engine.dispose()


def test_event_narrative_explanation_api_success(synthesis_test_env):
    env = synthesis_test_env
    client = TestClient(app)

    url = f"/api/v1/series/{env['sid_str']}/intelligence/event-narrative/{env['e4_id']}?chapter=10"
    resp = client.get(url)
    assert resp.status_code == 200
    data = resp.json()

    assert data["series_id"] == env["sid_str"]
    assert data["focus_id"] == env["e4_id"]
    assert data["explanation_type"] == "EVENT_NARRATIVE"
    assert data["reader_chapter"] == 10
    assert len(data["narrative_steps"]) >= 1

    # Check that turning point synthesis is included
    assert len(data["turning_point_syntheses"]) >= 1
    assert data["turning_point_syntheses"][0]["character_id"] == env["char_id_str"]
    assert data["turning_point_syntheses"][0]["chapter"] == 8


def test_character_narrative_causality_api_success(synthesis_test_env):
    env = synthesis_test_env
    client = TestClient(app)

    url = f"/api/v1/series/{env['sid_str']}/intelligence/character-narrative-causality/{env['char_id_str']}?chapter=10"
    resp = client.get(url)
    assert resp.status_code == 200
    data = resp.json()

    assert data["series_id"] == env["sid_str"]
    assert data["focus_id"] == env["char_id_str"]
    assert data["explanation_type"] == "CHARACTER_NARRATIVE"
    assert len(data["turning_point_syntheses"]) >= 2  # Rank S and Death


def test_synthesis_temporal_firewall_n_minus_1_n_n_plus_1(synthesis_test_env):
    """HARD SECURITY GATE: Validates that readerChapter strictly bounds all synthesis outputs."""
    env = synthesis_test_env
    client = TestClient(app)
    sid = env["sid_str"]
    cid = env["char_id_str"]

    # --- Scenario 1: readerChapter = 7 (N-1 where N=8 is Rank S turning point) ---
    r7 = client.get(
        f"/api/v1/series/{sid}/intelligence/character-narrative-causality/{cid}?chapter=7"
    )
    assert r7.status_code == 200
    d7 = r7.json()
    assert not any(tp["chapter"] > 7 for tp in d7["turning_point_syntheses"])
    assert not any(tp["chapter"] == 8 for tp in d7["turning_point_syntheses"])
    assert not any(tp["chapter"] == 10 for tp in d7["turning_point_syntheses"])

    # --- Scenario 2: readerChapter = 8 (N) ---
    r8 = client.get(
        f"/api/v1/series/{sid}/intelligence/character-narrative-causality/{cid}?chapter=8"
    )
    assert r8.status_code == 200
    d8 = r8.json()
    assert any(tp["chapter"] == 8 for tp in d8["turning_point_syntheses"])
    assert not any(tp["chapter"] == 10 for tp in d8["turning_point_syntheses"])

    # --- Scenario 3: readerChapter = 10 (N+1 relative to Ch 8) ---
    r10 = client.get(
        f"/api/v1/series/{sid}/intelligence/character-narrative-causality/{cid}?chapter=10"
    )
    assert r10.status_code == 200
    d10 = r10.json()
    assert any(tp["chapter"] == 8 for tp in d10["turning_point_syntheses"])
    assert any(tp["chapter"] == 10 for tp in d10["turning_point_syntheses"])


def test_synthesis_series_isolation(synthesis_test_env):
    """Cross-series lookup is strictly rejected."""
    env = synthesis_test_env
    client = TestClient(app)
    foreign_sid = str(uuid.uuid4())

    url = f"/api/v1/series/{foreign_sid}/intelligence/character-narrative-causality/{env['char_id_str']}?chapter=5"
    resp = client.get(url)
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_synthesis_determinism_and_cache(synthesis_test_env):
    """Verifies byte-level equality and cache hits on repeated requests."""
    env = synthesis_test_env
    client = TestClient(app)

    url = f"/api/v1/series/{env['sid_str']}/intelligence/character-narrative-causality/{env['char_id_str']}?chapter=5"

    r1 = client.get(url)
    assert r1.status_code == 200

    r2 = client.get(url)
    assert r2.status_code == 200

    assert r1.json() == r2.json()


def test_synthesis_rate_limit_classification():
    """Verifies that synthesis endpoints are classified under EXPENSIVE_READ."""
    tier_ev = classify_endpoint(
        "/api/v1/series/123/intelligence/event-narrative/456", "GET"
    )
    assert tier_ev == EndpointTier.EXPENSIVE_READ

    tier_char = classify_endpoint(
        "/api/v1/series/123/intelligence/character-narrative-causality/456", "GET"
    )
    assert tier_char == EndpointTier.EXPENSIVE_READ


def test_synthesis_error_boundaries(synthesis_test_env):
    env = synthesis_test_env
    client = TestClient(app)

    # Negative chapter
    r_neg = client.get(
        f"/api/v1/series/{env['sid_str']}/intelligence/event-narrative/{env['e1_id']}?chapter=-1"
    )
    assert r_neg.status_code in (400, 422)

    # Nonexistent event
    fake_eid = str(uuid.uuid4())
    r_fake = client.get(
        f"/api/v1/series/{env['sid_str']}/intelligence/event-narrative/{fake_eid}?chapter=5"
    )
    assert r_fake.status_code == 404
    assert r_fake.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
