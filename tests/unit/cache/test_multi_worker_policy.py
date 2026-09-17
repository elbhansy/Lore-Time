"""Unit tests for Multi-Worker safety policy enforcement in Settings."""

import pytest

from apps.api.app.config import Environment, Settings


def test_single_worker_cache_enabled_allowed():
    settings = Settings(
        ENVIRONMENT=Environment.DEVELOPMENT,
        WORKER_COUNT=1,
        CACHE_ENABLED=True,
    )
    assert settings.WORKER_COUNT == 1
    assert settings.CACHE_ENABLED is True


def test_multi_worker_cache_disabled_allowed():
    settings = Settings(
        ENVIRONMENT=Environment.DEVELOPMENT,
        WORKER_COUNT=4,
        CACHE_ENABLED=False,
        RATE_LIMIT_ENABLED=False,
    )
    assert settings.WORKER_COUNT == 4
    assert settings.CACHE_ENABLED is False
    assert settings.RATE_LIMIT_ENABLED is False


def test_multi_worker_cache_enabled_rejected():
    """Configuring multi-worker deployment with in-process cache must raise validation error."""
    with pytest.raises(ValueError, match="Multi-Worker Cache Violation"):
        Settings(
            ENVIRONMENT=Environment.DEVELOPMENT,
            WORKER_COUNT=2,
            CACHE_ENABLED=True,
        )
