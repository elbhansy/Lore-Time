"""Authoritative Central Application Settings Contract for Timeline Power Visualizer.

Distinguishes:
  - development
  - test
  - production

Enforces strict Fail-Fast validation on production environments.
"""

import re
from enum import StrEnum

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Core Environment
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    SECRET_KEY: str = Field(
        default="dev-insecure-secret-key-change-in-production-32bytes!",
        description="Application secret key used for signing / security tokens",
    )

    # API Server Configuration
    API_TITLE: str = "Timeline Power Visualizer API"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # CORS Configuration
    CORS_ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True

    # Host & Proxy Security
    ALLOWED_HOSTS: list[str] = ["*"]
    MAX_REQUEST_BODY_BYTES: int = 1048576  # 1 MB request body limit

    # Database Configuration
    DATABASE_URL: str = "postgresql+psycopg://timeline_user:timeline_password@localhost:5432/timeline_db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT_SECONDS: int = 30
    DB_POOL_RECYCLE_SECONDS: int = 1800
    DB_POOL_PRE_PING: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"

    # Phase 4.8 Caching Configuration
    CACHE_ENABLED: bool = True
    CACHE_MAX_ENTRIES: int = 5000
    CACHE_MAX_ENTRY_BYTES: int = 524288  # 512 KB per entry ceiling
    CACHE_MAX_MEMORY_BYTES: int = 67108864  # 64 MB global cache memory ceiling
    CACHE_DEFAULT_TTL_SECONDS: int = 3600  # 1 hour default TTL
    CACHE_VERSION: str = "v1"  # Cache key schema version
    WORKER_COUNT: int = (
        1  # Process worker count (enforces in-process single-worker policy)
    )

    # Phase 4.9 Rate Limiting & Abuse Protection
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT_LIMIT: int = 120  # Standard read limit (req/min)
    RATE_LIMIT_DEFAULT_BURST: int = 30  # Standard read burst
    RATE_LIMIT_EXPENSIVE_LIMIT: int = 30  # Expensive read limit (req/min)
    RATE_LIMIT_EXPENSIVE_BURST: int = 10  # Expensive read burst
    RATE_LIMIT_MUTATING_LIMIT: int = 60  # Mutating limit (req/min)
    RATE_LIMIT_MUTATING_BURST: int = 15  # Mutating burst
    RATE_LIMIT_MAX_IDENTITIES: int = (
        10000  # Max unique client identities tracked in memory
    )
    RATE_LIMIT_MAX_HITS_PER_IDENTITY: int = 100  # Max hits stored in deque per identity
    RATE_LIMIT_WINDOW_SECONDS: int = 60  # Window size in seconds
    TRUSTED_PROXIES: list[str] = ["127.0.0.1", "::1"]

    @field_validator(
        "CORS_ALLOWED_ORIGINS", "ALLOWED_HOSTS", "TRUSTED_PROXIES", mode="before"
    )
    @classmethod
    def parse_string_lists(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @field_validator(
        "DB_POOL_SIZE",
        "DB_MAX_OVERFLOW",
        "DB_POOL_TIMEOUT_SECONDS",
        "DB_POOL_RECYCLE_SECONDS",
        "CACHE_MAX_ENTRIES",
        "CACHE_MAX_ENTRY_BYTES",
        "CACHE_MAX_MEMORY_BYTES",
        "CACHE_DEFAULT_TTL_SECONDS",
        "RATE_LIMIT_DEFAULT_LIMIT",
        "RATE_LIMIT_DEFAULT_BURST",
        "RATE_LIMIT_EXPENSIVE_LIMIT",
        "RATE_LIMIT_EXPENSIVE_BURST",
        "RATE_LIMIT_MUTATING_LIMIT",
        "RATE_LIMIT_MUTATING_BURST",
        "RATE_LIMIT_MAX_IDENTITIES",
        "RATE_LIMIT_MAX_HITS_PER_IDENTITY",
        "RATE_LIMIT_WINDOW_SECONDS",
        "WORKER_COUNT",
        "MAX_REQUEST_BODY_BYTES",
    )
    @classmethod
    def validate_positive_numbers(cls, v, info):
        if v < 0:
            raise ValueError(f"{info.field_name} must be non-negative")
        return v

    @model_validator(mode="after")
    def validate_cache_multi_worker_policy(self) -> "Settings":
        """Enforces multi-worker safety: in-process cache and rate limiter require single-worker deployment."""
        if self.WORKER_COUNT > 1:
            if self.CACHE_ENABLED:
                raise ValueError(
                    "Multi-Worker Cache Violation: In-process bounded cache is only supported for "
                    "single-worker deployments (WORKER_COUNT=1). For multi-worker deployments, "
                    "CACHE_ENABLED must be False."
                )
            if self.RATE_LIMIT_ENABLED:
                raise ValueError(
                    "Multi-Worker Rate Limit Violation: In-process bounded rate limiter is only "
                    "supported for single-worker deployments (WORKER_COUNT=1). For multi-worker deployments, "
                    "RATE_LIMIT_ENABLED must be False."
                )
        return self

    @model_validator(mode="after")
    def validate_production_hardening(self) -> "Settings":
        """Enforces critical security policies for production deployments."""
        if self.ENVIRONMENT == Environment.PRODUCTION:
            if self.DEBUG:
                raise ValueError(
                    "Security Violation: DEBUG cannot be True in production environment"
                )

            if (
                not self.SECRET_KEY
                or "dev-insecure" in self.SECRET_KEY
                or len(self.SECRET_KEY) < 32
            ):
                raise ValueError(
                    "Security Violation: Production requires a secure, non-default "
                    "SECRET_KEY of at least 32 characters"
                )

            if "*" in self.CORS_ALLOWED_ORIGINS:
                raise ValueError(
                    "Security Violation: Wildcard '*' CORS origin is strictly "
                    "prohibited in production environment"
                )

            if any(
                "localhost" in origin or "127.0.0.1" in origin
                for origin in self.CORS_ALLOWED_ORIGINS
            ):
                raise ValueError(
                    "Security Violation: Localhost origins are prohibited in "
                    "production CORS_ALLOWED_ORIGINS"
                )

            if "*" in self.ALLOWED_HOSTS:
                raise ValueError(
                    "Security Violation: Wildcard '*' ALLOWED_HOSTS is strictly "
                    "prohibited in production environment"
                )

            if not self.DATABASE_URL.startswith("postgresql"):
                raise ValueError("Production requires a valid PostgreSQL database URL")
            if "timeline_password" in self.DATABASE_URL:
                raise ValueError(
                    "Security Violation: Default sample database password detected "
                    "in production DATABASE_URL"
                )

        return self

    @property
    def sanitized_database_url(self) -> str:
        """Returns database URL with password masked for safe logging/diagnostics."""
        return re.sub(r":([^:@]+)@", ":****@", self.DATABASE_URL)


_settings_instance: Settings | None = None


def get_settings() -> Settings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def reset_settings_for_testing(new_settings: Settings | None = None) -> Settings | None:
    """Helper used strictly in test suite to reset or inject custom settings."""
    global _settings_instance
    _settings_instance = new_settings
    return _settings_instance
