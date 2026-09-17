import logging

import pytest

from apps.api.app.config import Environment, Settings
from apps.api.app.core.logging import SensitiveDataFilter


def test_default_development_settings():
    s = Settings(ENVIRONMENT=Environment.DEVELOPMENT)
    assert s.ENVIRONMENT == Environment.DEVELOPMENT
    assert s.DEBUG is False
    assert len(s.CORS_ALLOWED_ORIGINS) > 0
    assert "timeline_user" in s.DATABASE_URL
    assert s.DB_POOL_SIZE == 10
    assert s.DB_POOL_PRE_PING is True


def test_test_environment_settings():
    s = Settings(
        ENVIRONMENT=Environment.TEST,
        DATABASE_URL="postgresql+psycopg://test_user:test_pass@localhost:5432/test_db",
        DEBUG=True,
    )
    assert s.ENVIRONMENT == Environment.TEST
    assert s.DEBUG is True
    assert s.DATABASE_URL == (
        "postgresql+psycopg://test_user:test_pass@localhost:5432/test_db"
    )


def test_cors_origins_parsing_from_string():
    s = Settings(
        CORS_ALLOWED_ORIGINS="https://app.example.com, https://admin.example.com"
    )
    assert s.CORS_ALLOWED_ORIGINS == [
        "https://app.example.com",
        "https://admin.example.com",
    ]


def test_sanitized_database_url_masks_password():
    s = Settings(
        DATABASE_URL="postgresql+psycopg://admin:SuperSecretPass123!@db.host.internal:5432/proddb"
    )
    sanitized = s.sanitized_database_url
    assert "SuperSecretPass123!" not in sanitized
    assert ":****@" in sanitized
    assert "db.host.internal:5432/proddb" in sanitized


def test_production_fails_if_debug_enabled():
    with pytest.raises(ValueError, match="DEBUG cannot be True in production"):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION,
            DEBUG=True,
            SECRET_KEY="A" * 32,
            DATABASE_URL="postgresql+psycopg://prod:real_secret@host:5432/db",
            CORS_ALLOWED_ORIGINS=["https://loretime.app"],
        )


def test_production_fails_if_secret_key_insecure_or_too_short():
    with pytest.raises(
        ValueError, match="Production requires a secure, non-default SECRET_KEY"
    ):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION,
            DEBUG=False,
            SECRET_KEY="short-key",
            DATABASE_URL="postgresql+psycopg://prod:real_secret@host:5432/db",
            CORS_ALLOWED_ORIGINS=["https://loretime.app"],
        )

    with pytest.raises(
        ValueError, match="Production requires a secure, non-default SECRET_KEY"
    ):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION,
            DEBUG=False,
            SECRET_KEY="dev-insecure-secret-key-change-in-production-32bytes!",
            DATABASE_URL="postgresql+psycopg://prod:real_secret@host:5432/db",
            CORS_ALLOWED_ORIGINS=["https://loretime.app"],
        )


def test_production_fails_if_wildcard_cors():
    with pytest.raises(
        ValueError,
        match=r"Wildcard '\*' CORS origin is strictly prohibited in production",
    ):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION,
            DEBUG=False,
            SECRET_KEY="A" * 32,
            DATABASE_URL="postgresql+psycopg://prod:real_secret@host:5432/db",
            CORS_ALLOWED_ORIGINS=["*"],
        )


def test_production_fails_if_sample_password_used():
    with pytest.raises(ValueError, match="Default sample database password detected"):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION,
            DEBUG=False,
            SECRET_KEY="A" * 32,
            DATABASE_URL="postgresql+psycopg://timeline_user:timeline_password@localhost:5432/timeline_db",
            CORS_ALLOWED_ORIGINS=["https://loretime.app"],
            ALLOWED_HOSTS=["loretime.app"],
        )


def test_production_valid_configuration():
    s = Settings(
        ENVIRONMENT=Environment.PRODUCTION,
        DEBUG=False,
        SECRET_KEY="VeryStrongProductionSecretKeyForSigningPurposes!",
        DATABASE_URL="postgresql+psycopg://real_user:StrongRandomPass987#@db.prod.internal:5432/canonical_timeline",
        CORS_ALLOWED_ORIGINS=["https://loretime.app", "https://app.loretime.com"],
        ALLOWED_HOSTS=["loretime.app", "app.loretime.com"],
    )
    assert s.ENVIRONMENT == Environment.PRODUCTION
    assert s.DEBUG is False
    assert len(s.SECRET_KEY) >= 32


def test_invalid_negative_pool_values_rejected():
    with pytest.raises(ValueError, match="DB_POOL_SIZE must be non-negative"):
        Settings(DB_POOL_SIZE=-1)


def test_sensitive_data_logging_filter():
    filt = SensitiveDataFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Connecting to postgresql://user:MySecretPassword@localhost:5432/db",
        args=(),
        exc_info=None,
    )
    filt.filter(record)
    assert "MySecretPassword" not in record.msg
    assert ":****@" in record.msg


def test_production_fails_if_localhost_in_cors():
    with pytest.raises(
        ValueError,
        match="Localhost origins are prohibited in production CORS_ALLOWED_ORIGINS",
    ):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION,
            DEBUG=False,
            SECRET_KEY="A" * 32,
            DATABASE_URL="postgresql+psycopg://prod:real_secret@host:5432/db",
            CORS_ALLOWED_ORIGINS=["https://loretime.app", "http://localhost:3000"],
            ALLOWED_HOSTS=["loretime.app"],
        )


def test_production_fails_if_wildcard_allowed_hosts():
    with pytest.raises(
        ValueError,
        match=r"Wildcard '\*' ALLOWED_HOSTS is strictly prohibited in production",
    ):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION,
            DEBUG=False,
            SECRET_KEY="A" * 32,
            DATABASE_URL="postgresql+psycopg://prod:real_secret@host:5432/db",
            CORS_ALLOWED_ORIGINS=["https://loretime.app"],
            ALLOWED_HOSTS=["*"],
        )
