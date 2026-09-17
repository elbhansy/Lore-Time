# Phase 4.7 — Backup & Restore Strategy

## 1. Executive Summary
This document establishes the production backup, restore, and disaster recovery strategy for the **Temporal Story Intelligence Web Application** on PostgreSQL 18. The strategy addresses logical backups, physical backups, Point-in-Time Recovery (PITR), restore verification, canonical data preservation, and recovery time/point objectives (RTO/RPO).

---

## 2. Operational Objectives (RTO & RPO)

| Metric | Target | Definition |
| :--- | :--- | :--- |
| **RPO (Recovery Point Objective)** | < 1 hour (Logical) / < 5 minutes (PITR) | Maximum acceptable data loss window |
| **RTO (Recovery Time Objective)** | < 15 minutes (Logical Restore) | Maximum allowable time to restore full application operations |

---

## 3. Backup Architecture

### 3.1 Logical Backup (`pg_dump`)
- **Tool**: PostgreSQL `pg_dump` utility.
- **Format**: Custom archive (`-Fc`) or plain SQL with directory format.
- **Scope**: Complete schema, data, triggers, sequences, and indexes.
- **Command Template**:
  ```bash
  pg_dump -h <host> -U timeline_user -d timeline_db -Fc -f /backups/timeline_db_<timestamp>.dump
  ```
- **Frequency**:
  - Full snapshot every 6 hours.
  - Pre-deployment snapshot immediately prior to applying any Alembic migration.

### 3.2 Backup Storage & Security
- **Encryption**: Encrypted at rest (AES-256) and in transit (TLS 1.3).
- **Isolation**: Backups stored in dedicated, immutable object storage separate from database compute instances.
- **Retention**:
  - Hourly/pre-deploy: 7 days.
  - Daily: 30 days.
  - Monthly: 1 year.

---

## 4. Restore & Recovery Procedure

### 4.1 Automated Restore Workflow
1. **Target Provisioning**: Target database created or existing database cleared.
2. **Restore Execution**:
   ```bash
   pg_restore -h <host> -U timeline_user -d timeline_db --clean --if-exists -v /backups/timeline_db_<timestamp>.dump
   ```
3. **Schema Verification**:
   - Verify `alembic_version` matches current deployment head.
   - Verify all 14 domain and infrastructure tables exist.
4. **Application Verification**:
   - Check `/health` returns `200 OK`.
   - Check `/ready` returns `200 OK` (verifies live database connectivity).
5. **Data Verification**:
   - Verify canonical entities, events, relationships, and review items are preserved.
   - Verify WorldState reconstruction matches pre-backup snapshots.

---

## 5. Point-in-Time Recovery (PITR) Assessment

### 5.1 Current Environment Assessment
- **PostgreSQL Version**: 18.6
- **Current Parameters**:
  - `wal_level`: `replica` (Sufficient for archiving and replication).
  - `archive_mode`: `off`
  - `archive_command`: `(disabled)`
- **Classification**: **PARTIALLY_SUPPORTED** (PostgreSQL binary and engine support PITR; operational archive storage is not yet activated on local test instance).

### 5.2 Production Activation Requirements
To fully enable PITR in production:
1. Set `archive_mode = on` in `postgresql.conf`.
2. Configure `archive_command = 'cp %p /var/lib/postgresql/wal_archive/%f'` (or cloud storage sync like `wal-g` / AWS S3).
3. Schedule base physical backups (`pg_basebackup`) weekly.

---

## 6. Verification Taxonomy

```text
1. Backup Created      → Dump file generated without error
2. Backup Verified     → Checksum and archive header validated
3. Backup Restored     → Target database restored without foreign key or constraint errors
4. App Verified        → /health == 200, /ready == 200, API endpoints serve traffic
5. DR Verified         → Canonical snapshots & temporal firewall verified identical
```
