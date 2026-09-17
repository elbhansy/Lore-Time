"""Unit tests for deterministic Cache Key Builder."""

import uuid

from apps.api.app.core.cache.key_builder import build_cache_key, build_series_prefix


def test_build_cache_key_deterministic():
    sid = uuid.uuid4()
    k1 = build_cache_key(
        "v1",
        sid,
        "world_state",
        reader_chapter=5,
        query_params={"limit": 10, "offset": 0},
    )
    k2 = build_cache_key(
        "v1",
        sid,
        "world_state",
        reader_chapter=5,
        query_params={"offset": 0, "limit": 10},
    )

    assert k1 == k2
    assert k1.startswith(f"v1:{sid}:world_state:ch5:")


def test_build_cache_key_series_isolation():
    sid_a = uuid.uuid4()
    sid_b = uuid.uuid4()
    ka = build_cache_key("v1", sid_a, "world_state", reader_chapter=5)
    kb = build_cache_key("v1", sid_b, "world_state", reader_chapter=5)

    assert ka != kb
    assert str(sid_a) in ka
    assert str(sid_b) in kb


def test_build_cache_key_temporal_isolation():
    sid = uuid.uuid4()
    k_ch5 = build_cache_key("v1", sid, "world_state", reader_chapter=5)
    k_ch10 = build_cache_key("v1", sid, "world_state", reader_chapter=10)

    assert k_ch5 != k_ch10
    assert ":ch5:" in k_ch5
    assert ":ch10:" in k_ch10


def test_build_cache_key_versioning():
    sid = uuid.uuid4()
    k_v1 = build_cache_key("v1", sid, "world_state", reader_chapter=5)
    k_v2 = build_cache_key("v2", sid, "world_state", reader_chapter=5)

    assert k_v1 != k_v2
    assert k_v1.startswith("v1:")
    assert k_v2.startswith("v2:")


def test_build_series_prefix():
    sid = uuid.uuid4()
    prefix = build_series_prefix("v1", sid)
    assert prefix == f"v1:{sid}:"
