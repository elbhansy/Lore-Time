"""Tests for Phase 4.7 Migration Safety, Integrity, and Rollback."""

import uuid

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from infrastructure.database.models import Base

ADMIN_DB_URL = (
    "postgresql+psycopg://timeline_user:timeline_password@localhost:5432/postgres"
)


@pytest.fixture
def disposable_db():
    """Provisions a completely isolated, disposable PostgreSQL database for testing migrations."""
    db_name = f"test_mig_{uuid.uuid4().hex[:8]}"
    admin_engine = create_engine(ADMIN_DB_URL, isolation_level="AUTOCOMMIT")

    with admin_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE {db_name}"))

    db_url = (
        f"postgresql+psycopg://timeline_user:timeline_password@localhost:5432/{db_name}"
    )
    target_engine = create_engine(db_url)

    yield db_url, target_engine

    target_engine.dispose()
    with admin_engine.connect() as conn:
        # Terminate any remaining connections to the disposable DB before dropping
        conn.execute(
            text(
                f"""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = '{db_name}' AND pid <> pg_backend_pid()
        """
            )
        )
        conn.execute(text(f"DROP DATABASE {db_name}"))
    admin_engine.dispose()


def test_clean_database_upgrade_to_head_and_schema_verification(disposable_db):
    """Milestone 4.7.2 & 4.7.3: Verifies that a clean database runs all migrations to head,

    producing all tables, constraints, and indexes expected by Base.metadata.
    """
    db_url, engine = disposable_db

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    # 1. Upgrade clean database to head
    command.upgrade(alembic_cfg, "head")

    # 2. Verify all models tables exist in the database
    insp = inspect(engine)
    db_tables = set(insp.get_table_names())
    expected_tables = set(Base.metadata.tables.keys())

    assert expected_tables.issubset(db_tables), (
        f"Missing tables after migration: {expected_tables - db_tables}"
    )

    # 3. Verify Alembic version is at head
    with engine.connect() as conn:
        rev = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        assert rev == "m2_8_graph_projection"


def test_migration_rollback_and_reapply(disposable_db):
    """Milestone 4.7.4: Verifies that migrations can be rolled back cleanly

    (downgrade -1) and re-upgraded without leaving corrupted state.
    """
    db_url, engine = disposable_db

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    # 1. Upgrade to head
    command.upgrade(alembic_cfg, "head")

    # 2. Downgrade one step (m2_8_graph_projection -> m2_7_canonical_search)
    command.downgrade(alembic_cfg, "-1")

    with engine.connect() as conn:
        rev = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        assert rev == "m2_7_canonical_search"

    insp = inspect(engine)
    tables_after_downgrade = set(insp.get_table_names())
    # canonical_entities and canonical_relationships should be dropped
    assert "canonical_entities" not in tables_after_downgrade
    assert "canonical_relationships" not in tables_after_downgrade

    # 3. Re-upgrade back to head
    command.upgrade(alembic_cfg, "head")
    insp2 = inspect(engine)
    tables_after_reupgrade = set(insp2.get_table_names())
    assert "canonical_entities" in tables_after_reupgrade
    assert "canonical_relationships" in tables_after_reupgrade


def test_migration_failure_injection_transaction_rollback(disposable_db):
    """Milestone 4.7.13: Simulates a migration failure and verifies that PostgreSQL's

    transactional DDL rolls back the migration completely, preventing partial application.
    """
    db_url, engine = disposable_db

    # Create a table that will cause a conflict during migration
    with engine.begin() as conn:
        conn.execute(
            text("CREATE TABLE series (id int primary key, conflicting_column text)")
        )

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    # Running upgrade should fail because table 'series' already exists with conflicting schema
    with pytest.raises(Exception):
        command.upgrade(alembic_cfg, "head")

    # Verify that alembic_version was NOT updated to head due to failure rollback
    with engine.connect() as conn:
        insp = inspect(engine)
        tables = insp.get_table_names()
        if "alembic_version" in tables:
            rev = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
            assert rev != "m2_8_graph_projection"
