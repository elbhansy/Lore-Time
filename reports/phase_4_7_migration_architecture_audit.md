# Phase 4.7 — Migration Architecture Audit

## 1. Executive Summary
This audit inspects the database schema, migration environment, Alembic configuration, and table/index/constraint structures for the **Temporal Story Intelligence Web Application** on PostgreSQL 18.

---

## 2. Migration Toolchain & Environment
- **Migration Framework**: Alembic 1.14.x (`alembic.ini`, `infrastructure/migrations/`).
- **Configuration**:
  - Script directory: `infrastructure/migrations/`
  - Version directory: `infrastructure/migrations/versions/`
  - Environment: `infrastructure/migrations/env.py` configured with `Base.metadata` from `infrastructure.database.models`.
  - Transactional DDL: Enabled (`with context.begin_transaction(): context.run_migrations()`). PostgreSQL natively supports transactional DDL.

---

## 3. Revision Chain & History Integrity

The migration chain is strictly linear with **exactly one head**:

```text
m0_1_core_schema (base)
       ↓
m0_9_power_systems (power systems, ranks, skills)
       ↓
m2_0_entity_aliases (entity aliases for ingestion)
       ↓
m2_1_provenance_sources (provenance sources)
       ↓
m2_3_review_layer (review items)
       ↓
m2_4_canonical_publishing (publication attempts & event publication_fingerprint)
       ↓
m2_7_canonical_search (search_vector TSVECTOR, GIN index, and tsvector trigger)
       ↓
m2_8_graph_projection (canonical_entities, canonical_relationships) [HEAD]
```

- **Branching**: None (0 branches).
- **Multiple Heads**: None (1 head: `m2_8_graph_projection`).
- **Determinism**: 100% deterministic ordered DAG.
- **Current Live DB Revision**: Synchronized to `m2_8_graph_projection (head)`.

---

## 4. Schema Elements, Constraints, and Indexes

| Table | Primary Key | Foreign Keys | Unique Constraints | Indexes | Triggers |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `series` | `id` (UUID) | None | `slug` | PK, Unique slug | None |
| `chapters` | `id` (UUID) | `series_id` → `series.id` | `(series_id, number)` | PK, Unique | None |
| `characters` | `id` (UUID) | `series_id` → `series.id` | None | PK | None |
| `factions` | `id` (UUID) | `series_id` → `series.id` | None | PK | None |
| `power_systems`| `id` (UUID) | `series_id` → `series.id` | `(series_id, slug)` | PK, Unique | None |
| `ranks` | `id` (UUID) | `power_system_id`, `parent_rank_id` | `(power_system_id, slug)` | PK, Unique | Check (`chapter >= 1`) |
| `skills` | `id` (UUID) | `power_system_id` → `power_systems.id` | None | PK | None |
| `events` | `id` (UUID) | `series_id`, `chapter_id` | `(series_id, chapter_id, sequence)`, `publication_fingerprint` | GIN (`search_vector`), B-tree (`series_id, chapter_id`), B-tree (`series_id, type`), B-tree (`series_id, subject_id`), B-tree (`series_id, target_id`) | `trg_events_search_vector_update` |
| `entity_aliases` | `id` (UUID) | `series_id` → `series.id` | `(series_id, entity_type, normalized_alias)` | B-tree (`series_id, normalized_alias`) | None |
| `sources` | `id` (UUID) | `series_id` → `series.id` | `(series_id, type, name, version)` | PK, Unique | None |
| `review_items` | `id` (UUID) | `series_id`, `chapter_id` | None | PK | None |
| `publication_attempts` | `id` (UUID) | `review_item_id`, `event_id` | None | PK | None |
| `canonical_entities` | `id` (String)| None | `(series_id, id)` | PK, Unique | None |
| `canonical_relationships` | `id` (UUID)| None | None | B-tree (`series_id, source`), B-tree (`series_id, target`), B-tree (`series_id, type`), B-tree (`event_id`) | None |

---

## 5. Critical Invariant Verification

1. **Canonical Uniqueness**:
   - `events.publication_fingerprint`: Enforces canonical event deduplication under concurrency.
   - `canonical_entities (series_id, id)`: Ensures deterministic entity uniqueness per series.
   - `events (series_id, chapter_id, sequence)`: Preserves deterministic temporal event sequencing.

2. **Temporal Integrity**:
   - `ranks.chk_rank_introduced_chapter_positive`: Asserts `introduced_chapter >= 1`.
   - `events.sequence`: Sequence number order is guaranteed per chapter.

3. **Reversibility / Downgrade Paths**:
   - All migrations provide matching `downgrade()` implementations that drop added tables, columns, indexes, and triggers in correct topological order.
