from sqlalchemy import create_engine, text


def run_explain():
    engine = create_engine(
        "postgresql+psycopg://timeline_user:timeline_password@localhost:5432/timeline_db"
    )
    with open("bench_sid.txt") as f:
        sid = f.read().strip()

    queries = {
        "1. Event timeline query (get_all_by_series with chapter join)": f"""
            EXPLAIN ANALYZE
            SELECT events.id, events.series_id, events.chapter_id, events.sequence, events.type,
                   chapters.number as chapter_number
            FROM events
            JOIN chapters ON events.chapter_id = chapters.id
            WHERE events.series_id = '{sid}'
            ORDER BY chapters.number ASC, events.sequence ASC, events.id ASC;
        """,
        "2. Event chapter filtering (bounded chapter range 5 to 10)": f"""
            EXPLAIN ANALYZE
            SELECT events.id, events.series_id, events.chapter_id, events.sequence, events.type,
                   chapters.number as chapter_number
            FROM events
            JOIN chapters ON events.chapter_id = chapters.id
            WHERE events.series_id = '{sid}'
              AND chapters.number BETWEEN 5 AND 10
            ORDER BY chapters.number ASC, events.sequence ASC, events.id ASC;
        """,
        "3. Character retrieval by series": f"""
            EXPLAIN ANALYZE
            SELECT characters.id, characters.series_id, characters.name, characters.description
            FROM characters
            WHERE characters.series_id = '{sid}';
        """,
        "4. Relationship retrieval (by series + source)": f"""
            EXPLAIN ANALYZE
            SELECT canonical_relationships.id, canonical_relationships.series_id, canonical_relationships.source_entity_id,
                   canonical_relationships.target_entity_id, canonical_relationships.type
            FROM canonical_relationships
            WHERE canonical_relationships.series_id = '{sid}';
        """,
        "5. Global search (characters by name ILIKE)": f"""
            EXPLAIN ANALYZE
            SELECT characters.id, characters.name, characters.description
            FROM characters
            WHERE characters.series_id = '{sid}'
              AND (characters.name ILIKE '%Hero 1%' OR characters.description ILIKE '%Hero 1%')
            LIMIT 1000;
        """,
        "6. Analytics aggregation (events by type)": f"""
            EXPLAIN ANALYZE
            SELECT events.type, COUNT(*)
            FROM events
            JOIN chapters ON events.chapter_id = chapters.id
            WHERE events.series_id = '{sid}'
              AND chapters.number <= 10
            GROUP BY events.type;
        """,
        "7. Review queue (status PENDING bounded by chapter)": f"""
            EXPLAIN ANALYZE
            SELECT review_items.id, review_items.series_id, review_items.status, chapters.number
            FROM review_items
            JOIN chapters ON review_items.chapter_id = chapters.id
            WHERE review_items.series_id = '{sid}'
              AND review_items.status = 'PENDING'
              AND chapters.number <= 10;
        """,
        "8. Publication lookup (by fingerprint)": """
            EXPLAIN ANALYZE
            SELECT events.id, events.publication_fingerprint
            FROM events
            WHERE events.publication_fingerprint = 'fp-test-dummy';
        """,
        "9. WorldState event loading (all events for series vs <= reader_chapter)": f"""
            EXPLAIN ANALYZE
            SELECT events.id, events.series_id, events.chapter_id, events.sequence, events.type,
                   chapters.number as chapter_number
            FROM events
            JOIN chapters ON events.chapter_id = chapters.id
            WHERE events.series_id = '{sid}'
              AND chapters.number <= 10;
        """,
        "10. Temporal filtering (canonical search plainto_tsquery)": f"""
            EXPLAIN ANALYZE
            SELECT events.id, chapters.number
            FROM events
            JOIN chapters ON events.chapter_id = chapters.id
            WHERE events.series_id = '{sid}'
            ORDER BY chapters.number ASC, events.sequence ASC, events.id ASC
            LIMIT 50 OFFSET 0;
        """,
    }

    with engine.connect() as conn:
        for name, q in queries.items():
            print("==================================================")
            print(f"{name}")
            print("==================================================")
            result = conn.execute(text(q))
            for row in result:
                print(row[0])
            print()


if __name__ == "__main__":
    run_explain()
