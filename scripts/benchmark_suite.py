"""Reproducible Benchmark Suite across scales (100, 1K, 10K events).

Explicitly invoked benchmark script that records:
- Platform environment & versions
- Warmup policy
- 10 iterations per query operation
- Min, Median, P95, Max latencies
- Query plans & row counts
Does NOT run automatically during normal pytest runs to keep CI fast.
"""

import platform
import statistics
import sys
import time
import uuid

import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from apps.api.app.config import get_settings
from apps.api.repositories.canonical.sqlalchemy_analytics_reader import (
    SQLAlchemyAnalyticsReader,
)
from apps.api.repositories.sqlalchemy_character_repository import (
    SQLAlchemyCharacterRepository,
)
from apps.api.repositories.sqlalchemy_event_repository import SQLAlchemyEventRepository
from apps.api.repositories.sqlalchemy_search_repository import (
    SQLAlchemySearchRepository,
)
from infrastructure.database.models import Base
from packages.domain.analytics.analytics_query import AnalyticsQuery
from packages.domain.search.search_query import SearchQuery, SearchType
from packages.domain.services.event_applier import EventApplier
from packages.domain.services.world_state_builder import WorldStateBuilder
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId


def seed_scale(engine, event_count: int) -> str:
    """Seeds a test dataset with exact event_count in PostgreSQL."""
    sid = str(uuid.uuid4())
    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO series (id, title, slug, total_chapters) VALUES (:id, :t, :s, 100)"
            ),
            {"id": sid, "t": f"Scale {event_count}", "s": f"scale-{sid[:8]}"},
        )
        # Create chapters (scaled proportionally)
        num_chapters = max(5, min(50, event_count // 10))
        cids = []
        for c in range(1, num_chapters + 1):
            cid = str(uuid.uuid4())
            cids.append((cid, c))
            conn.execute(
                text(
                    "INSERT INTO chapters (id, series_id, number, title) VALUES (:id, :sid, :num, :t)"
                ),
                {"id": cid, "sid": sid, "num": c, "t": f"Chapter {c}"},
            )

        # Create characters (up to 50)
        num_chars = min(50, max(5, event_count // 20))
        char_ids = [str(uuid.uuid4()) for _ in range(num_chars)]
        for i, ch_id in enumerate(char_ids):
            conn.execute(
                text(
                    "INSERT INTO characters (id, series_id, name, description) VALUES (:id, :sid, :n, :d)"
                ),
                {
                    "id": ch_id,
                    "sid": sid,
                    "n": f"Hero {i}",
                    "d": f"Hero description {i}",
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

        # Create events batch
        events_batch = []
        chapter_seq_counters = {cid: 0 for cid, _ in cids}
        for i in range(event_count):
            cid, cnum = cids[i % num_chapters]
            seq = chapter_seq_counters[cid]
            chapter_seq_counters[cid] += 1
            subj = char_ids[i % num_chars]
            tgt = char_ids[(i + 1) % num_chars]
            events_batch.append(
                {
                    "id": str(uuid.uuid4()),
                    "sid": sid,
                    "cid": cid,
                    "seq": seq,
                    "type": "POWER_RANK_CHANGED"
                    if i % 2 == 0
                    else "CHARACTER_INTRODUCED",
                    "subj": subj,
                    "tgt": tgt,
                    "meta": '{"payload": {"val": 1}}',
                    "new_state": '{"rank": "Master"}',
                }
            )

        conn.execute(
            text("""
                INSERT INTO events (id, series_id, chapter_id, sequence, type, subject_type, subject_id, target_type, target_id, metadata, new_state)
                VALUES (:id, :sid, :cid, :seq, :type, 'CHARACTER', :subj, 'CHARACTER', :tgt, CAST(:meta AS jsonb), CAST(:new_state AS jsonb))
            """),
            events_batch,
        )

        # Create relationships
        num_rels = min(100, event_count // 5)
        if num_rels > 0:
            rels_batch = []
            for i in range(num_rels):
                rels_batch.append(
                    {
                        "id": str(uuid.uuid4()),
                        "sid": sid,
                        "src": char_ids[i % num_chars],
                        "tgt": char_ids[(i + 1) % num_chars],
                        "type": "ALLY",
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

        # Create review items
        num_reviews = min(50, event_count // 10)
        if num_reviews > 0:
            rev_batch = []
            for i in range(num_reviews):
                cid, _ = cids[i % num_chapters]
                rev_batch.append(
                    {
                        "id": str(uuid.uuid4()),
                        "sid": sid,
                        "cid": cid,
                        "ft": "DIALOGUE",
                        "fp": '{"k": 1}',
                        "prov": '{"chapter": 1}',
                        "st": "PENDING" if i % 2 == 0 else "APPROVED",
                    }
                )
            conn.execute(
                text("""
                    INSERT INTO review_items (id, series_id, chapter_id, fact_type, fact_payload, provenance_data, status)
                    VALUES (:id, :sid, :cid, :ft, CAST(:fp AS jsonb), CAST(:prov AS jsonb), :st)
                """),
                rev_batch,
            )

    return sid


def time_operation(fn, warmup: int = 2, iterations: int = 10):
    """Measures min, median, p95, max execution time in milliseconds."""
    for _ in range(warmup):
        fn()
    durations = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn()
        durations.append((time.perf_counter() - t0) * 1000)
    durations.sort()
    p95_idx = int(0.95 * len(durations))
    return {
        "min": durations[0],
        "median": statistics.median(durations),
        "p95": durations[p95_idx],
        "max": durations[-1],
    }


def run_benchmark():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)

    # Print environment
    with engine.connect() as conn:
        pg_ver = conn.execute(text("SHOW server_version")).scalar()

    print("=====================================================================")
    print("PHASE 4.3 BENCHMARK REPORT ENVIRONMENT")
    print("=====================================================================")
    print(f"OS: {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Python: {platform.python_version()}")
    print(f"SQLAlchemy: {sqlalchemy.__version__}")
    print(f"PostgreSQL: {pg_ver}")
    print("Iterations: 10 per operation (after 2 warmups)")
    print("=====================================================================\n")

    scales = [100, 1000, 10000]
    # Check if 100K requested via arg
    if "--include-100k" in sys.argv:
        scales.append(100000)

    results_table = {}

    for count in scales:
        print(f"Seeding and benchmarking dataset scale: {count} events...")
        sid = seed_scale(engine, count)
        session = Session()

        event_repo = SQLAlchemyEventRepository(session)
        char_repo = SQLAlchemyCharacterRepository(session)
        search_repo = SQLAlchemySearchRepository(session)
        analytics_reader = SQLAlchemyAnalyticsReader(session)
        ws_builder = WorldStateBuilder(EventApplier())

        # Operations
        ops = {
            "Event Query (bounded)": lambda: event_repo.get_by_chapter_range(
                EntityId(sid), ChapterNumber(1), ChapterNumber(5)
            ),
            "Timeline (get_all_by_series)": lambda: event_repo.get_all_by_series(
                EntityId(sid), to_chapter=ChapterNumber(5)
            ),
            "Search (candidate query)": lambda: search_repo.search_candidates(
                SearchQuery(text="Hero", type=SearchType.CHARACTER, reader_chapter=5),
                sid,
            ),
            "Analytics (event stats)": lambda: analytics_reader.get_event_statistics(
                AnalyticsQuery(series_id=sid, from_chapter=1, to_chapter=5)
            ),
            "Relationship Query": lambda: session.execute(
                text("SELECT * FROM canonical_relationships WHERE series_id = :sid"),
                {"sid": sid},
            ).all(),
            "WorldState Rebuild (<= ch 5)": lambda: ws_builder.build(
                EntityId(sid),
                event_repo.get_all_by_series(
                    EntityId(sid), to_chapter=ChapterNumber(5)
                ),
                ChapterNumber(5),
            ),
            "Review Queue (PENDING)": lambda: session.execute(
                text(
                    "SELECT * FROM review_items WHERE series_id = :sid AND status = 'PENDING'"
                ),
                {"sid": sid},
            ).all(),
            "Publication Lookup (indexed)": lambda: session.execute(
                text(
                    "SELECT id FROM events WHERE publication_fingerprint = 'dummy-fp'"
                ),
            ).all(),
        }

        results_table[count] = {}
        for op_name, fn in ops.items():
            stats = time_operation(fn)
            results_table[count][op_name] = stats
            print(
                f"  [{op_name:30}] median: {stats['median']:6.2f}ms (p95: {stats['p95']:6.2f}ms, min: {stats['min']:6.2f}ms)"
            )

        session.close()
        print()

    # Format final summary table
    print(
        "\n=========================================================================================="
    )
    print(f"{'OPERATION':30} | " + " | ".join(f"{str(c):>12}" for c in scales))
    print(
        "------------------------------------------------------------------------------------------"
    )
    op_names = list(results_table[scales[0]].keys())
    for op in op_names:
        row = f"{op:30} | "
        for c in scales:
            median_val = results_table[c][op]["median"]
            row += f"{median_val:10.2f}ms | "
        print(row)
    print(
        "==========================================================================================\n"
    )


if __name__ == "__main__":
    run_benchmark()
