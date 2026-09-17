# Production Operational Runbook

**Service:** Timeline Power Visualizer API  
**Target Environment:** Production  
**Runtime:** Python 3.13 / FastAPI / Uvicorn (Single Worker) / PostgreSQL 18  

---

## 1. Production Configuration & Bootstrap

### 1.1 Mandatory Environment Variables
Configure the application environment using the following variables (e.g. via Kubernetes Secret, AWS Parameter Store, or Vault):

```bash
# Core Environment
export ENVIRONMENT=production
export DEBUG=false
export SECRET_KEY="<generate-random-64-character-hex-string>"

# Server & Security
export API_TITLE="Timeline Power Visualizer API"
export API_HOST=0.0.0.0
export API_PORT=8000
export CORS_ALLOWED_ORIGINS="https://loretime.app,https://api.loretime.app"
export ALLOWED_HOSTS="api.loretime.app"
export TRUSTED_PROXIES="10.0.0.1,10.0.0.2"
export MAX_REQUEST_BODY_BYTES=1048576

# Database Connection (PostgreSQL 18)
export DATABASE_URL="postgresql+psycopg://timeline_prod_user:<secure_db_pass>@prod-db.internal:5432/timeline_prod"
export DB_POOL_SIZE=10
export DB_MAX_OVERFLOW=20
export DB_POOL_TIMEOUT_SECONDS=30
export DB_POOL_RECYCLE_SECONDS=1800
export DB_POOL_PRE_PING=true

# Logging & Monitoring
export LOG_LEVEL=INFO

# Caching & Rate Limiting (Single Worker Constraint)
export CACHE_ENABLED=true
export RATE_LIMIT_ENABLED=true
export WORKER_COUNT=1
```

### 1.2 Starting the Application
```bash
python -m uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000 --workers 1
```
*Note: `workers` MUST equal `1` to satisfy the in-process cache and rate limiter safety constraint.*

---

## 2. Health & Readiness Verification

- **Liveness Probe**:
  ```bash
  curl -f http://127.0.0.1:8000/health
  # Expected: HTTP 200 {"status": "ok", "service": "timeline-api"}
  ```
- **Readiness Probe**:
  ```bash
  curl -f http://127.0.0.1:8000/ready
  # Expected: HTTP 200 {"status": "ready", "database": "connected"}
  ```

---

## 3. Database Migrations Procedure

**MANDATORY RULE**: Migrations must be executed out-of-band BEFORE launching the updated application process.

1. Connect to production deployment runner or bastion host.
2. Verify connectivity:
   ```bash
   alembic current
   ```
3. Execute migration upgrade:
   ```bash
   alembic upgrade head
   ```
4. Verify migration state matches expected head revision.

---

## 4. Backup & Restore Procedures

### 4.1 Daily Logical Backup
```bash
pg_dump -h prod-db.internal -U timeline_prod_user -d timeline_prod --format=custom -f /backups/timeline_prod_$(date +%Y%m%d_%H%M%S).dump
```

### 4.2 Restoring from Backup
1. Stop application instances to prevent writes.
2. Drop and recreate database:
   ```bash
   dropdb -h prod-db.internal -U postgres timeline_prod
   createdb -h prod-db.internal -U postgres -O timeline_prod_user timeline_prod
   ```
3. Restore schema and data:
   ```bash
   pg_restore -h prod-db.internal -U timeline_prod_user -d timeline_prod -v /backups/timeline_prod_<timestamp>.dump
   ```
4. Run application readiness check (`/ready`).

---

## 5. Diagnostic & Incident Response Playbooks

### Scenario 1: Readiness Check Fails (HTTP 503 on `/ready`)
- **Symptoms**: Load balancer removes instance; error `database.connection.failure` logged.
- **Diagnostics**:
  1. Inspect PostgreSQL service status and connectivity from the container host.
  2. Verify credentials in `DATABASE_URL`.
  3. Check PostgreSQL connection counts (`SELECT count(*) FROM pg_stat_activity;`).
- **Resolution**: Restore PostgreSQL connectivity. The application connection pool with `DB_POOL_PRE_PING=True` will recover automatically once PostgreSQL resumes accepting connections.

### Scenario 2: High Rate of HTTP 429 (`RATE_LIMIT_EXCEEDED`)
- **Symptoms**: Clients report HTTP 429; log contains `rate_limit.rejected`.
- **Diagnostics**:
  1. Inspect `client_ip` and `tier` in structured logs.
  2. If legitimate traffic is throttled due to a proxy misconfiguration, ensure edge proxy IPs are included in `TRUSTED_PROXIES`.
  3. If traffic is an abusive query flood, the rate limiter is functioning as designed; verify edge DDoS filters.

### Scenario 3: Cache Inconsistency or Corruption
- **Symptoms**: Outdated world-state or stale timeline queries.
- **Resolution**:
  1. In-process cache automatically bypasses to PostgreSQL if marked dirty.
  2. To force a hard reset of in-process cache, restart the API process (`systemctl restart timeline-api` or container reboot). Cache starts completely cold and safely repopulates from PostgreSQL.
