"""Deterministic Cache Key Builder enforcing series isolation and temporal boundaries."""

import uuid
from typing import Any

from .canonical_hash import canonical_query_hash


def build_cache_key(
    version: str,
    series_id: str | uuid.UUID,
    resource: str,
    reader_chapter: int | None = None,
    query_params: dict[str, Any] | None = None,
) -> str:
    """Builds a deterministic, collision-proof cache key.

    Structure:
    v{version}:{series_id}:{resource}:{reader_chapter}:{query_hash}
    """
    sid_str = str(series_id)
    chap_str = f"ch{reader_chapter}" if reader_chapter is not None else "global"
    q_hash = canonical_query_hash(query_params)

    return f"{version}:{sid_str}:{resource}:{chap_str}:{q_hash}"


def build_series_prefix(version: str, series_id: str | uuid.UUID) -> str:
    """Returns the key prefix for all cached entries of a given series."""
    return f"{version}:{str(series_id)}:"
