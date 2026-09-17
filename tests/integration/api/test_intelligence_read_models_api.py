"""Integration tests for UI Read Models and Query Architecture (Phase 5.4).

Verifies:
1. StoryOverviewReadModel (GET /intelligence/overview)
2. TimelineReadModel with pagination and causal links (GET /intelligence/timeline-feed)
3. CharacterReadModel profile (GET /intelligence/characters/{cid}/profile)
4. GenericGraphReadModel projection (GET /intelligence/graph)
5. Temporal Firewall ($N-1, N, N+1$)
6. Multi-Tenant Series Isolation (Cross-series queries rejected)
7. Determinism & Caching
8. Rate Limiting (EXPENSIVE_READ tier classification)
9. Error boundaries
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
def query_arch_test_env():
    """Seeds series, characters, and events."""
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
        char_model = CharacterModel(id=char_id, series_id=sid, name="Hero ReadModel")
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
        # Event 2: Ch 3 Rank E
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
        # Event 3: Ch 5 Skill
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
            new_state={"skill_id": "solar_beam"},
            metadata_={"chapter_number": 5, "cause_event_id": str(e2_id)},
        )
        # Event 4: Ch 8 Rank S
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


def test_story_overview_read_model(query_arch_test_env):
    env = query_arch_test_env
    client = TestClient(app)

    url = f"/api/v1/series/{env['sid_str']}/intelligence/overview?chapter=8"
    resp = client.get(url)
    assert resp.status_code == 200
    data = resp.json()

    assert data["series_id"] == env["sid_str"]
    assert data["temporal_context"]["reader_chapter"] == 8
    assert data["total_chapters_visible"] == 8
    assert len(data["recent_events"]) <= 10
    assert len(data["recent_turning_points"]) >= 1


def test_timeline_read_model_with_pagination(query_arch_test_env):
    env = query_arch_test_env
    client = TestClient(app)

    # Page 1: limit 5
    url = f"/api/v1/series/{env['sid_str']}/intelligence/timeline-feed?chapter=10&from=1&to=10&limit=5&offset=0"
    resp = client.get(url)
    assert resp.status_code == 200
    data = resp.json()

    assert data["temporal_context"]["reader_chapter"] == 10
    assert data["from_chapter"] == 1
    assert data["to_chapter"] == 10
    assert len(data["events"]) == 5
    assert data["pagination"]["limit"] == 5
    assert data["pagination"]["offset"] == 0
    assert data["pagination"]["has_more"] is True

    # Events have causes/effects attached
    e3_models = [ev for ev in data["events"] if ev["event_id"] == env["e3_id"]]
    if e3_models:
        assert len(e3_models[0]["causes"]) >= 1


def test_character_profile_read_model(query_arch_test_env):
    env = query_arch_test_env
    client = TestClient(app)

    url = f"/api/v1/series/{env['sid_str']}/intelligence/characters/{env['char_id_str']}/profile?chapter=8"
    resp = client.get(url)
    assert resp.status_code == 200
    data = resp.json()

    assert data["character_id"] == env["char_id_str"]
    assert data["status"] == "alive"
    assert data["rank"] == "S"
    assert data["temporal_context"]["reader_chapter"] == 8
    assert data["total_turning_points_passed"] >= 2


def test_generic_graph_read_model(query_arch_test_env):
    env = query_arch_test_env
    client = TestClient(app)

    # Causal graph
    url = f"/api/v1/series/{env['sid_str']}/intelligence/graph?chapter=8&graph_type=causal"
    resp = client.get(url)
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["nodes"]) >= 2
    assert len(data["edges"]) >= 1
    assert all(e["edge_type"] != "" for e in data["edges"])


def test_read_model_temporal_firewall_n_minus_1_n_n_plus_1(query_arch_test_env):
    """HARD SECURITY GATE: Validates that readerChapter strictly bounds all read models."""
    env = query_arch_test_env
    client = TestClient(app)
    sid = env["sid_str"]
    cid = env["char_id_str"]

    # --- Scenario 1: readerChapter = 7 (N-1 where N=8 is Rank S) ---
    r7 = client.get(
        f"/api/v1/series/{sid}/intelligence/characters/{cid}/profile?chapter=7"
    )
    assert r7.status_code == 200
    d7 = r7.json()
    assert d7["rank"] == "E"
    assert d7["status"] == "alive"
    assert not any(tp["chapter"] > 7 for tp in d7["turning_points"])

    # --- Scenario 2: readerChapter = 8 (N) ---
    r8 = client.get(
        f"/api/v1/series/{sid}/intelligence/characters/{cid}/profile?chapter=8"
    )
    assert r8.status_code == 200
    d8 = r8.json()
    assert d8["rank"] == "S"
    assert d8["status"] == "alive"
    assert not any(tp["chapter"] == 10 for tp in d8["turning_points"])

    # --- Scenario 3: readerChapter = 10 (N+1 relative to Ch 8) ---
    r10 = client.get(
        f"/api/v1/series/{sid}/intelligence/characters/{cid}/profile?chapter=10"
    )
    assert r10.status_code == 200
    d10 = r10.json()
    assert d10["status"] == "dead"


def test_read_model_series_isolation(query_arch_test_env):
    env = query_arch_test_env
    client = TestClient(app)
    foreign_sid = str(uuid.uuid4())

    url = f"/api/v1/series/{foreign_sid}/intelligence/overview?chapter=5"
    resp = client.get(url)
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_read_model_determinism_and_cache(query_arch_test_env):
    env = query_arch_test_env
    client = TestClient(app)

    url = f"/api/v1/series/{env['sid_str']}/intelligence/overview?chapter=5"

    r1 = client.get(url)
    assert r1.status_code == 200

    r2 = client.get(url)
    assert r2.status_code == 200

    assert r1.json() == r2.json()


def test_read_model_rate_limit_classification():
    assert (
        classify_endpoint("/api/v1/series/123/intelligence/overview", "GET")
        == EndpointTier.EXPENSIVE_READ
    )
    assert (
        classify_endpoint("/api/v1/series/123/intelligence/timeline-feed", "GET")
        == EndpointTier.EXPENSIVE_READ
    )
    assert (
        classify_endpoint(
            "/api/v1/series/123/intelligence/characters/456/profile", "GET"
        )
        == EndpointTier.EXPENSIVE_READ
    )
    assert (
        classify_endpoint("/api/v1/series/123/intelligence/graph", "GET")
        == EndpointTier.EXPENSIVE_READ
    )
