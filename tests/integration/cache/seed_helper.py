"""Seed helper for integration test suites."""

import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session


def seed_test_series(
    session: Session, num_chapters: int = 5, events_per_chapter: int = 4
) -> str:
    """Seeds a series with chapters, characters, and events into PostgreSQL."""
    sid = uuid.uuid4()
    cids = [uuid.uuid4() for _ in range(num_chapters)]
    char_ids = [uuid.uuid4() for _ in range(3)]

    # 1. Insert series
    session.execute(
        text(
            "INSERT INTO series (id, title, slug, total_chapters) VALUES (:id, :t, :s, :tc)"
        ),
        {
            "id": sid,
            "t": f"Test Series {str(sid)[:6]}",
            "s": f"s-{str(sid)[:6]}",
            "tc": num_chapters,
        },
    )

    # 2. Insert chapters
    for i, cid in enumerate(cids):
        session.execute(
            text(
                "INSERT INTO chapters (id, series_id, number, title) VALUES (:id, :sid, :num, :t)"
            ),
            {"id": cid, "sid": sid, "num": i + 1, "t": f"Chapter {i + 1}"},
        )

    # 3. Insert characters
    for i, ch_id in enumerate(char_ids):
        session.execute(
            text(
                "INSERT INTO characters (id, series_id, name, description) VALUES (:id, :sid, :n, :d)"
            ),
            {
                "id": ch_id,
                "sid": sid,
                "n": f"Hero_{i}_{str(ch_id)[:4]}",
                "d": f"Hero description {i}",
            },
        )
        session.execute(
            text(
                "INSERT INTO canonical_entities (id, series_id, type, name, metadata) VALUES (:id, :sid, 'CHARACTER', :n, '{}')"
            ),
            {"id": ch_id, "sid": sid, "n": f"Hero_{i}_{str(ch_id)[:4]}"},
        )

    # 4. Insert events
    seq = 0
    for c_idx, cid in enumerate(cids):
        for e_idx in range(events_per_chapter):
            ev_id = uuid.uuid4()
            ch_sub = char_ids[e_idx % len(char_ids)]
            fp = f"fp_{ev_id}"
            ev_type = (
                "CHARACTER_INTRODUCED"
                if (c_idx == 0 and e_idx < len(char_ids))
                else "POWER_RANK_CHANGED"
            )
            new_state = (
                f'{{"name": "Hero_{e_idx}"}}'
                if ev_type == "CHARACTER_INTRODUCED"
                else f'{{"rank": "Rank_{c_idx}_{e_idx}"}}'
            )

            session.execute(
                text("""
                    INSERT INTO events (id, series_id, chapter_id, sequence, type, subject_type, subject_id, publication_fingerprint, metadata, new_state)
                    VALUES (:id, :sid, :cid, :seq, :type, 'CHARACTER', :subj, :fp, '{}', CAST(:new_state AS jsonb))
                """),
                {
                    "id": ev_id,
                    "sid": sid,
                    "cid": cid,
                    "seq": seq,
                    "type": ev_type,
                    "subj": ch_sub,
                    "fp": fp,
                    "new_state": new_state,
                },
            )
            seq += 1

    session.commit()
    return str(sid)
