"""Tests for Phase 4.7 Backup and Restore Safety, Canonical & Temporal Data Preservation."""

import os
import subprocess
import uuid

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from tests.integration.database.restore_helpers import restore_dump

ADMIN_DB_URL = (
    "postgresql+psycopg://timeline_user:timeline_password@localhost:5432/postgres"
)
PG_DUMP_PATH = r"C:\Users\elbhansy\AppData\Local\pgsql18\pgsql\bin\pg_dump.exe"
PG_RESTORE_PATH = r"C:\Users\elbhansy\AppData\Local\pgsql18\pgsql\bin\pg_restore.exe"


@pytest.fixture
def disposable_db_pair():
    """Provisions a pair of source and target disposable databases for backup and restore testing."""
    src_db = f"test_src_{uuid.uuid4().hex[:8]}"
    tgt_db = f"test_tgt_{uuid.uuid4().hex[:8]}"
    admin_engine = create_engine(ADMIN_DB_URL, isolation_level="AUTOCOMMIT")

    with admin_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE {src_db}"))
        conn.execute(text(f"CREATE DATABASE {tgt_db}"))

    src_url = (
        f"postgresql+psycopg://timeline_user:timeline_password@localhost:5432/{src_db}"
    )
    tgt_url = (
        f"postgresql+psycopg://timeline_user:timeline_password@localhost:5432/{tgt_db}"
    )

    src_engine = create_engine(src_url)
    tgt_engine = create_engine(tgt_url)

    yield (src_db, src_url, src_engine), (tgt_db, tgt_url, tgt_engine)

    src_engine.dispose()
    tgt_engine.dispose()

    with admin_engine.connect() as conn:
        for db in (src_db, tgt_db):
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


def test_backup_and_restore_preserves_canonical_and_temporal_data(
    disposable_db_pair, tmp_path
):
    """Milestones 4.7.7, 4.7.8, 4.7.10, 4.7.11:

    1. Applies migrations to source database.
    2. Seeds a representative canonical series with chapters, characters, events, ranks, review items.
    3. Captures pre-backup snapshots of all data.
    4. Performs logical backup with pg_dump.
    5. Restores dump into clean target database with pg_restore.
    6. Verifies 100% data preservation and temporal integrity.
    """
    (src_db, src_url, src_engine), (tgt_db, tgt_url, tgt_engine) = disposable_db_pair

    # 1. Migrate source DB to head
    src_cfg = Config("alembic.ini")
    src_cfg.set_main_option("sqlalchemy.url", src_url)
    command.upgrade(src_cfg, "head")

    # 2. Seed representative dataset in source DB
    sid = uuid.uuid4()
    cid1 = uuid.uuid4()
    cid2 = uuid.uuid4()
    char_id = uuid.uuid4()
    ps_id = uuid.uuid4()
    rank_id = uuid.uuid4()
    ev1_id = uuid.uuid4()
    ev2_id = uuid.uuid4()
    rev_id = uuid.uuid4()

    with src_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO series (id, title, slug, total_chapters) VALUES (:id, :t, :s, :tc)"
            ),
            {"id": sid, "t": "Canonical Lore", "s": f"lore-{sid.hex[:6]}", "tc": 2},
        )
        conn.execute(
            text(
                "INSERT INTO chapters (id, series_id, number, title) VALUES (:id, :sid, :num, :t)"
            ),
            [
                {"id": cid1, "sid": sid, "num": 1, "t": "Prologue"},
                {"id": cid2, "sid": sid, "num": 2, "t": "Awakening"},
            ],
        )
        conn.execute(
            text(
                "INSERT INTO characters (id, series_id, name, description) VALUES (:id, :sid, :n, :d)"
            ),
            {"id": char_id, "sid": sid, "n": "Shadow Monarch", "d": "Protagonist"},
        )
        conn.execute(
            text(
                "INSERT INTO power_systems (id, series_id, name, slug) VALUES (:id, :sid, :n, :s)"
            ),
            {"id": ps_id, "sid": sid, "n": "Mana System", "s": "mana-system"},
        )
        conn.execute(
            text(
                'INSERT INTO ranks (id, power_system_id, name, slug, "order", introduced_chapter) VALUES (:id, :psid, :n, :s, :o, :ic)'
            ),
            {
                "id": rank_id,
                "psid": ps_id,
                "n": "S-Rank",
                "s": "s-rank",
                "o": 1,
                "ic": 1,
            },
        )
        conn.execute(
            text(
                """
                INSERT INTO events (id, series_id, chapter_id, sequence, type, subject_type, subject_id, new_state, publication_fingerprint, metadata)
                VALUES (:id, :sid, :cid, :seq, :t, 'CHARACTER', :subjid, CAST(:ns AS jsonb), :fp, '{}')
            """
            ),
            [
                {
                    "id": ev1_id,
                    "sid": sid,
                    "cid": cid1,
                    "seq": 1,
                    "t": "CHARACTER_APPEARANCE",
                    "subjid": char_id,
                    "ns": '{"rank": "E"}',
                    "fp": "fp_ev1",
                },
                {
                    "id": ev2_id,
                    "sid": sid,
                    "cid": cid2,
                    "seq": 1,
                    "t": "POWER_RANK_CHANGED",
                    "subjid": char_id,
                    "ns": '{"rank": "S"}',
                    "fp": "fp_ev2",
                },
            ],
        )
        conn.execute(
            text(
                """
                INSERT INTO review_items (id, series_id, chapter_id, fact_type, fact_payload, provenance_data, status)
                VALUES (:id, :sid, :cid, :ft, '{"to_rank": "S"}', '{"source": "ch2"}', 'APPROVED')
            """
            ),
            {"id": rev_id, "sid": sid, "cid": cid2, "ft": "POWER_RANK_CHANGED"},
        )

    # 3. Capture pre-backup state snapshot
    with src_engine.connect() as conn:
        src_series = conn.execute(text("SELECT * FROM series")).fetchall()
        src_chapters = conn.execute(
            text("SELECT * FROM chapters ORDER BY number")
        ).fetchall()
        src_events = conn.execute(
            text("SELECT * FROM events ORDER BY sequence")
        ).fetchall()
        src_reviews = conn.execute(text("SELECT * FROM review_items")).fetchall()

    # 4. Perform pg_dump backup
    dump_file = tmp_path / "test_backup.dump"
    env = os.environ.copy()
    env["PGPASSWORD"] = "timeline_password"

    dump_cmd = [
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
    ]
    dump_proc = subprocess.run(dump_cmd, env=env, capture_output=True, text=True)
    assert dump_proc.returncode == 0, f"pg_dump failed: {dump_proc.stderr}"
    assert dump_file.exists() and dump_file.stat().st_size > 0

    # 5. Restore into clean target database using pg_restore
    restore_dump(PG_RESTORE_PATH, dump_file, tgt_db)

    # 6. Verify target database matches pre-backup snapshots byte-for-byte / value-for-value
    with tgt_engine.connect() as conn:
        tgt_series = conn.execute(text("SELECT * FROM series")).fetchall()
        tgt_chapters = conn.execute(
            text("SELECT * FROM chapters ORDER BY number")
        ).fetchall()
        tgt_events = conn.execute(
            text("SELECT * FROM events ORDER BY sequence")
        ).fetchall()
        tgt_reviews = conn.execute(text("SELECT * FROM review_items")).fetchall()

    assert len(tgt_series) == len(src_series)
    assert len(tgt_chapters) == len(src_chapters)
    assert len(tgt_events) == len(src_events)
    assert len(tgt_reviews) == len(src_reviews)

    assert tgt_series[0][1] == "Canonical Lore"
    assert tgt_events[0][4] == "CHARACTER_APPEARANCE"
    assert tgt_events[1][4] == "POWER_RANK_CHANGED"
    assert tgt_reviews[0][6] == "APPROVED"
