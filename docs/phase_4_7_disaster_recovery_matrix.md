# Phase 4.7 — Disaster Recovery Matrix

## 1. Overview
This matrix assesses failure modes across migrations, database operations, infrastructure disruptions, and recovery mechanisms for the **Temporal Story Intelligence Web Application**.

---

## 2. Comprehensive Disaster Recovery Matrix

| Failure Mode | Detection Mechanism | Recovery Procedure | Data Loss | Target RTO | Target RPO | Test Verification Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **Migration DDL Failure** | Alembic exception during `upgrade` | Transactional rollback in PostgreSQL; revision remains at previous state | None | < 1 min | 0 sec | **VERIFIED** (4.7.13) |
| **Interrupted / Broken Migration** | Alembic lock or mismatch | Rollback transaction, run `alembic downgrade` or restore pre-migration backup | None | < 5 min | 0 sec | **VERIFIED** (4.7.4) |
| **Constraint Creation Failure** | PostgreSQL `IntegrityError` during migration | Transaction auto-rollback; schema uncorrupted | None | < 1 min | 0 sec | **VERIFIED** (4.7.13) |
| **Accidental Table / Row Deletion** | Application error, alert, or 404 anomaly | Restore from point-in-time recovery WAL or latest pre-incident backup | < RPO window | < 15 min | < 1 hour | **VERIFIED** (4.7.10) |
| **Database Corruption / Storage Loss** | PostgreSQL panic / connection refusal | Provision replacement instance; restore from latest verified backup | < RPO window | < 15 min | < 1 hour | **VERIFIED** (4.7.11) |
| **Backup Corruption / Truncation** | Automated backup restore integrity test failure | Trigger immediate re-backup from active replica / primary | None | < 5 min | 0 sec | **VERIFIED** (4.7.11) |
| **Restore Execution Failure** | `pg_restore` non-zero exit code | Abort switchover; retry with alternative snapshot archive | None | < 10 min | < 1 hour | **VERIFIED** (4.7.10) |
| **PostgreSQL Outage / Network Cut** | `/ready` probe returns 503; API logs `database.connection.failure` | Auto-failover / restart PostgreSQL; `/health` remains 200 | None | < 2 min | 0 sec | **VERIFIED** (4.7.14) |
| **Schema / Code Mismatch** | App startup failure or `OperationalError` | Enforce CI/CD pipeline gate running `alembic upgrade head` before container startup | None | < 5 min | 0 sec | **VERIFIED** (4.7.2) |
| **Canonical Data Drift Post-Restore** | Checksum mismatch between pre-backup and restored data | Forensic comparison of canonical tables; re-apply immutable events | None | < 15 min | 0 sec | **VERIFIED** (4.7.7) |
