import uuid

from sqlalchemy import create_engine, text

from infrastructure.database.models import Base


def run_seed():
    engine = create_engine(
        "postgresql+psycopg://timeline_user:timeline_password@localhost:5432/timeline_db"
    )
    Base.metadata.create_all(bind=engine)

    sid = str(uuid.uuid4())
    print(f"Seeding 1000 events for benchmark exploration with series {sid}...")
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO series (id, title, slug, total_chapters) VALUES (:id, :t, :s, 100)"
            ),
            {"id": sid, "t": "Bench Series", "s": f"bench-{sid[:8]}"},
        )
        cids = []
        for c in range(1, 21):
            cid = str(uuid.uuid4())
            cids.append((cid, c))
            conn.execute(
                text(
                    "INSERT INTO chapters (id, series_id, number, title) VALUES (:id, :sid, :num, :title)"
                ),
                {"id": cid, "sid": sid, "num": c, "title": f"Chapter {c}"},
            )

        char_ids = [str(uuid.uuid4()) for _ in range(50)]
        for i, ch_id in enumerate(char_ids):
            conn.execute(
                text(
                    "INSERT INTO characters (id, series_id, name, description) VALUES (:id, :sid, :n, :d)"
                ),
                {
                    "id": ch_id,
                    "sid": sid,
                    "n": f"Hero {i}",
                    "d": f"Description for hero {i}",
                },
            )
            conn.execute(
                text(
                    "INSERT INTO canonical_entities (id, series_id, type, name, metadata) VALUES (:id, :sid, :t, :n, :m)"
                ),
                {
                    "id": ch_id,
                    "sid": sid,
                    "t": "CHARACTER",
                    "n": f"Hero {i}",
                    "m": "{}",
                },
            )

        events_batch = []
        chapter_seq_counters = {cid: 0 for cid, _ in cids}
        for i in range(1000):
            cid, cnum = cids[i % 20]
            seq = chapter_seq_counters[cid]
            chapter_seq_counters[cid] += 1
            subj = char_ids[i % 50]
            tgt = char_ids[(i + 1) % 50]
            events_batch.append(
                {
                    "id": str(uuid.uuid4()),
                    "sid": sid,
                    "cid": cid,
                    "seq": seq,
                    "type": "POWER_RANK_CHANGED" if i % 2 == 0 else "DIALOGUE",
                    "subj": subj,
                    "tgt": tgt,
                    "meta": '{"payload": {"message": "hello"}}',
                    "new_state": '{"rank": "Aura Master"}',
                }
            )

        conn.execute(
            text("""
                INSERT INTO events (id, series_id, chapter_id, sequence, type, subject_type, subject_id, target_type, target_id, metadata, new_state)
                VALUES (:id, :sid, :cid, :seq, :type, 'CHARACTER', :subj, 'CHARACTER', :tgt, CAST(:meta AS jsonb), CAST(:new_state AS jsonb))
            """),
            events_batch,
        )

        # Seed relationships
        rels_batch = []
        for i in range(100):
            rels_batch.append(
                {
                    "id": str(uuid.uuid4()),
                    "sid": sid,
                    "src": char_ids[i % 50],
                    "tgt": char_ids[(i + 2) % 50],
                    "type": "ALLY" if i % 2 == 0 else "RIVAL",
                    "ev_id": events_batch[i]["id"],
                    "seq": i,
                }
            )
        conn.execute(
            text("""
                INSERT INTO canonical_relationships (id, series_id, source_entity_id, target_entity_id, type, event_id, sequence)
                VALUES (:id, :sid, :src, :tgt, :type, :ev_id, :seq)
            """),
            rels_batch,
        )

        # Seed review items
        revs_batch = []
        for i in range(50):
            cid, _ = cids[i % 20]
            revs_batch.append(
                {
                    "id": str(uuid.uuid4()),
                    "sid": sid,
                    "cid": cid,
                    "ft": "DIALOGUE",
                    "fp": '{"text": "Sample"}',
                    "prov": '{"chapter": 1}',
                    "st": "PENDING" if i % 2 == 0 else "APPROVED",
                }
            )
        conn.execute(
            text("""
                INSERT INTO review_items (id, series_id, chapter_id, fact_type, fact_payload, provenance_data, status)
                VALUES (:id, :sid, :cid, :ft, CAST(:fp AS jsonb), CAST(:prov AS jsonb), :st)
            """),
            revs_batch,
        )

    print("SUCCESS: 1000 events, 100 relationships, 50 characters, 50 reviews seeded.")
    return sid


if __name__ == "__main__":
    sid = run_seed()
    with open("bench_sid.txt", "w") as f:
        f.write(sid)
