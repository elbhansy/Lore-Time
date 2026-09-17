"""Deterministic Endpoint Tier Classification based on route pattern and HTTP method."""

import re
from enum import StrEnum


class EndpointTier(StrEnum):
    EXEMPT = "EXEMPT"
    EXPENSIVE_READ = "EXPENSIVE_READ"
    MUTATING = "MUTATING"
    STANDARD_READ = "STANDARD_READ"


# Pre-compiled concrete route patterns for exact matching
_EXEMPT_ROUTES = {
    "/health",
    "/ready",
}

_EXPENSIVE_ROUTES = [
    re.compile(r"^/api/v1/series/[^/]+/world-state$"),
    re.compile(r"^/api/v1/series/[^/]+/analytics(/.*)?$"),
    re.compile(r"^/api/v1/series/[^/]+/search$"),
    re.compile(r"^/api/v1/series/[^/]+/characters/[^/]+/relationship-graph$"),
    re.compile(r"^/api/v1/series/[^/]+/relationships/graph$"),
    re.compile(r"^/api/v1/series/[^/]+/comparison$"),
    re.compile(r"^/api/v1/series/[^/]+/impact$"),
    re.compile(r"^/api/v1/series/[^/]+/intelligence(/.*)?$"),
]

_MUTATING_ROUTES = [
    re.compile(r"^/api/v1/review(/.*)?$"),
]


def classify_endpoint(path: str, method: str) -> EndpointTier:
    """Classifies an incoming request path & method into a deterministic rate limit tier."""
    norm_path = path.rstrip("/") or "/"

    # 1. Operational & Infrastructure Exemption
    if norm_path in _EXEMPT_ROUTES:
        return EndpointTier.EXEMPT

    # 2. Mutating Endpoints
    if method.upper() in ("POST", "PUT", "PATCH", "DELETE"):
        for pattern in _MUTATING_ROUTES:
            if pattern.match(norm_path):
                return EndpointTier.MUTATING

    # 3. Expensive Reads
    if method.upper() == "GET":
        for pattern in _EXPENSIVE_ROUTES:
            if pattern.match(norm_path):
                return EndpointTier.EXPENSIVE_READ

    # 4. Standard Reads
    return EndpointTier.STANDARD_READ
