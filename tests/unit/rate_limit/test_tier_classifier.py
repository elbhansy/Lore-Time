"""Unit tests for Endpoint Tier Classification."""

from apps.api.app.core.rate_limit.tier_classifier import EndpointTier, classify_endpoint


def test_exempt_endpoints():
    assert classify_endpoint("/health", "GET") == EndpointTier.EXEMPT
    assert classify_endpoint("/ready", "GET") == EndpointTier.EXEMPT
    assert classify_endpoint("/health/", "GET") == EndpointTier.EXEMPT
    assert classify_endpoint("/ready/", "GET") == EndpointTier.EXEMPT


def test_expensive_read_endpoints():
    assert (
        classify_endpoint("/api/v1/series/123/world-state", "GET")
        == EndpointTier.EXPENSIVE_READ
    )
    assert (
        classify_endpoint("/api/v1/series/123/analytics/overview", "GET")
        == EndpointTier.EXPENSIVE_READ
    )
    assert (
        classify_endpoint("/api/v1/series/123/analytics/events", "GET")
        == EndpointTier.EXPENSIVE_READ
    )
    assert (
        classify_endpoint("/api/v1/series/123/search", "GET")
        == EndpointTier.EXPENSIVE_READ
    )
    assert (
        classify_endpoint("/api/v1/series/123/characters/456/relationship-graph", "GET")
        == EndpointTier.EXPENSIVE_READ
    )
    assert (
        classify_endpoint("/api/v1/series/123/relationships/graph", "GET")
        == EndpointTier.EXPENSIVE_READ
    )
    assert (
        classify_endpoint("/api/v1/series/123/comparison", "GET")
        == EndpointTier.EXPENSIVE_READ
    )
    assert (
        classify_endpoint("/api/v1/series/123/impact", "GET")
        == EndpointTier.EXPENSIVE_READ
    )


def test_mutating_endpoints():
    assert (
        classify_endpoint("/api/v1/review/item/publish", "POST")
        == EndpointTier.MUTATING
    )
    assert classify_endpoint("/api/v1/review/123", "PUT") == EndpointTier.MUTATING
    assert classify_endpoint("/api/v1/review/queue", "POST") == EndpointTier.MUTATING


def test_standard_read_endpoints():
    assert classify_endpoint("/api/v1/series/123", "GET") == EndpointTier.STANDARD_READ
    assert (
        classify_endpoint("/api/v1/series/123/timeline", "GET")
        == EndpointTier.STANDARD_READ
    )
    assert (
        classify_endpoint("/api/v1/series/123/characters", "GET")
        == EndpointTier.STANDARD_READ
    )
    assert (
        classify_endpoint("/api/v1/series/123/power-systems", "GET")
        == EndpointTier.STANDARD_READ
    )
    assert (
        classify_endpoint("/api/v1/series/123/factions", "GET")
        == EndpointTier.STANDARD_READ
    )
    assert (
        classify_endpoint("/api/v1/series/123/skills", "GET")
        == EndpointTier.STANDARD_READ
    )
