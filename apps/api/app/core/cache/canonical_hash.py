"""Canonical Query Serializer and Deterministic Hasher."""

import hashlib
import json
import unicodedata
from typing import Any


def canonicalize_value(val: Any) -> Any:
    """Recursively normalizes values for deterministic serialization."""
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val
    if isinstance(val, str):
        # Unicode NFKC normalization ensures equivalent character sequences produce identical strings
        return unicodedata.normalize("NFKC", val)
    if isinstance(val, (list, tuple, set)):
        # Normalize items; for sets or unordered lists where order should not matter,
        # sort primitive types if possible. Otherwise preserve normalized list.
        normalized = [canonicalize_value(item) for item in val]
        try:
            return sorted(normalized)
        except TypeError:
            return normalized
    if isinstance(val, dict):
        # Sort keys deterministically
        return {
            str(k): canonicalize_value(v)
            for k, v in sorted(val.items(), key=lambda item: str(item[0]))
        }
    # Fallback to string representation with NFKC
    return unicodedata.normalize("NFKC", str(val))


def canonical_query_hash(query_params: dict[str, Any] | None) -> str:
    """Computes a deterministic SHA-256 hash from query parameters.

    Guarantees:
    - Parameter order does not change hash: {'a': 1, 'b': 2} == {'b': 2, 'a': 1}
    - Unicode NFKC normalization
    - Empty or None query params return 'empty'
    """
    if not query_params:
        return "empty"

    normalized = canonicalize_value(query_params)
    serialized = json.dumps(
        normalized,
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]
