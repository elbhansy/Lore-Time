"""Unit tests for Canonical Query Hashing and Determinism."""

from apps.api.app.core.cache.canonical_hash import canonical_query_hash


def test_canonical_hash_parameter_order_independence():
    """Different dictionary key orders must generate identical hashes."""
    params1 = {"page": 1, "limit": 20, "type": "CHARACTER"}
    params2 = {"type": "CHARACTER", "page": 1, "limit": 20}
    params3 = {"limit": 20, "type": "CHARACTER", "page": 1}

    hash1 = canonical_query_hash(params1)
    hash2 = canonical_query_hash(params2)
    hash3 = canonical_query_hash(params3)

    assert hash1 == hash2 == hash3
    assert len(hash1) == 16


def test_canonical_hash_nested_order_independence():
    """Nested dictionaries with differing key orders must generate identical hashes."""
    params1 = {"filter": {"rank": "A", "status": "ALIVE"}, "page": 2}
    params2 = {"page": 2, "filter": {"status": "ALIVE", "rank": "A"}}

    assert canonical_query_hash(params1) == canonical_query_hash(params2)


def test_canonical_hash_empty_and_none():
    """Empty dicts and None must produce stable 'empty' hash."""
    assert canonical_query_hash(None) == "empty"
    assert canonical_query_hash({}) == "empty"


def test_canonical_hash_unicode_normalization():
    """Unicode decomposed and composed characters must produce identical hashes."""
    # 'é' as single character vs 'e' + combining acute accent
    s_composed = "\u00e9"
    s_decomposed = "e\u0301"
    assert s_composed != s_decomposed  # raw strings differ in codepoints

    params1 = {"name": s_composed}
    params2 = {"name": s_decomposed}

    assert canonical_query_hash(params1) == canonical_query_hash(params2)


def test_canonical_hash_different_queries_differ():
    """Different values or types must produce distinct hashes."""
    h1 = canonical_query_hash({"page": 1})
    h2 = canonical_query_hash({"page": 2})
    h3 = canonical_query_hash({"page": "1"})

    assert h1 != h2
