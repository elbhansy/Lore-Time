"""Tests for Phase 4.7 Restore + Application Verification (Milestone 4.7.14)."""

import os
import subprocess
import uuid

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from apps.api.app.main import app
from tests.integration.database.restore_helpers import restore_dump

ADMIN_DB_URL = (
    "postgresql+psycopg://timeline_user:timeline_password@localhost:5432/postgres"
)
PG_DUMP_PATH = r"C:\Users\elbhansy\AppData\Local\pgsql18\pgsql\bin\pg_dump.exe"
PG_RESTORE_PATH = r"C:\Users\elbhansy\AppData\Local\pgsql18\pgsql\bin\pg_restore.exe"


@pytest.fixture
def restored_application_db(tmp_path):
    """Provisions a populated source DB, backs it up, restores it into a restored DB,

    and configures the application to run against the restored DB.
    """
    src_db = f"app_src_{uuid.uuid4().hex[:8]}"
    res_db = f"app_res_{uuid.uuid4().hex[:8]}"
    admin_engine = create_engine(ADMIN_DB_URL, isolation_level="AUTOCOMMIT")

    with admin_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE {src_db}"))
        conn.execute(text(f"CREATE DATABASE {res_db}"))

    src_url = (
        f"postgresql+psycopg://timeline_user:timeline_password@localhost:5432/{src_db}"
    )
    res_url = (
        f"postgresql+psycopg://timeline_user:timeline_password@localhost:5432/{res_db}"
    )

    # 1. Migrate and seed source DB
    src_cfg = Config("alembic.ini")
    src_cfg.set_main_option("sqlalchemy.url", src_url)
    command.upgrade(src_cfg, "head")

    src_engine = create_engine(src_url)
    sid = uuid.uuid4()
    cid = uuid.uuid4()
    char_id = uuid.uuid4()

    with src_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO series (id, title, slug, total_chapters) VALUES (:id, :t, :s, :tc)"
            ),
            {"id": sid, "t": "Restored Series", "s": f"res-{sid.hex[:6]}", "tc": 10},
        )
        conn.execute(
            text(
                "INSERT INTO chapters (id, series_id, number, title) VALUES (:id, :sid, :num, :t)"
            ),
            {"id": cid, "sid": sid, "num": 1, "t": "Ch 1"},
        )
        conn.execute(
            text(
                "INSERT INTO characters (id, series_id, name, description) VALUES (:id, :sid, :n, :d)"
            ),
            {"id": char_id, "sid": sid, "n": "Restored Hero", "d": "Test"},
        )
        conn.execute(
            text(
                """
                INSERT INTO events (id, series_id, chapter_id, sequence, type, subject_type, subject_id, new_state, publication_fingerprint, metadata)
                VALUES (:id, :sid, :cid, 1, 'CHARACTER_INTRODUCED', 'CHARACTER', :subjid, '{"rank": "A"}', 'fp1', '{}')
            """
            ),
            {"id": uuid.uuid4(), "sid": sid, "cid": cid, "subjid": char_id},
        )
    src_engine.dispose()

    # 2. Dump source DB
    dump_file = tmp_path / "app_restore.dump"
    env = os.environ.copy()
    env["PGPASSWORD"] = "timeline_password"
    subprocess.run(
        [
            PG_DUMP_PATH,
            "-h",
            "localhost",
            "-p",
            "5432",
            "-U",
            "timeline_user",
            "-d",
            src_db,
            "-Fc",
            "-f",
            str(dump_file),
        ],
        env=env,
        check=True,
    )

    # 3. Restore to target DB
    restore_dump(PG_RESTORE_PATH, dump_file, res_db)

    yield res_url, sid

    with admin_engine.connect() as conn:
        for db in (src_db, res_db):
            conn.execute(
                text(
                    f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{db}' AND pid <> pg_backend_pid()
            """
                )
            )
            conn.execute(text(f"DROP DATABASE IF EXISTS {db}"))
    admin_engine.dispose()


def test_restored_database_serves_application_correctly(restored_application_db):
    """Milestone 4.7.14: Verifies that when the application connects to a restored database:

    1. /health returns 200.
    2. /ready returns 200.
    3. Series, WorldState, and Timeline queries return expected canonical records.
    """
    res_url, series_id = restored_application_db

    # Point application engine to the restored database
    from apps.api.app.dependencies import database

    original_engine = database.engine
    new_engine = create_engine(res_url)
    database.engine = new_engine
    database.SessionLocal.configure(bind=new_engine)

    try:
        client = TestClient(app)

        # 1. Health and Ready verification
        health_resp = client.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "ok"

        ready_resp = client.get("/ready")
        assert ready_resp.status_code == 200
        assert ready_resp.json()["status"] == "ready"

        # 2. Query world-state against restored database
        ws_resp = client.get(f"/api/v1/series/{series_id}/world-state?chapter=1")
        assert ws_resp.status_code == 200
        data = ws_resp.json()
        assert data["series_id"] == str(series_id)
        assert data["chapter"] == 1
        assert len(data["characters"]) >= 1

        # 3. Query timeline events against restored database
        tl_resp = client.get(
            f"/api/v1/series/{series_id}/timeline?reader_chapter=1&from=1&to=1"
        )
        assert tl_resp.status_code == 200
        assert len(tl_resp.json()) >= 1
        assert tl_resp.json()[0]["type"] == "CHARACTER_INTRODUCED"
    finally:
        database.engine = original_engine
        database.SessionLocal.configure(bind=original_engine)
        new_engine.dispose()


def test_health_and_ready_under_database_unavailable():
    """Milestone 4.7.14: Verifies that when the database is unavailable:

    1. /health still returns 200 (process liveness).
    2. /ready returns 503 (application readiness failure).
    """
    from apps.api.app.dependencies import database

    original_engine = database.engine
    # Point to a non-existent port where no PostgreSQL is listening (with fast timeout)
    bad_engine = create_engine(
        "postgresql+psycopg://timeline_user:timeline_password@localhost:5433/timeline_db",
        connect_args={"connect_timeout": 1},
    )
    database.engine = bad_engine

    try:
        client = TestClient(app)

        # Process is alive -> /health MUST be 200
        health_resp = client.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "ok"

        # Persistence is unavailable -> /ready MUST be 503
        ready_resp = client.get("/ready")
        assert ready_resp.status_code == 503
        assert ready_resp.json()["status"] == "not_ready"
    finally:
        database.engine = original_engine
        bad_engine.dispose()
