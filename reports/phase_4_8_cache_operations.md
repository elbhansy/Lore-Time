# Phase 4.8 — Cache Operations & Runbook

## 1. Enabling & Disabling Caching

Caching is controlled by environment variables in `.env` or application runtime settings:

```env
# Enable or disable caching entirely
CACHE_ENABLED=true

# Cache capacity limits
CACHE_MAX_ENTRIES=5000
CACHE_MAX_ENTRY_BYTES=524288       # 512 KB per entry ceiling
CACHE_MAX_MEMORY_BYTES=67108864     # 64 MB global cache memory ceiling
CACHE_DEFAULT_TTL_SECONDS=3600     # 1 hour default TTL
CACHE_VERSION=v1                   # Schema cache version

# Concurrency & worker deployment
WORKER_COUNT=1                     # Multi-worker safety enforcement
```

### First-Class Disabled Mode:
When `CACHE_ENABLED=false`:
- Zero cache reads or writes occur.
- Zero memory is allocated for cached payloads.
- Application logic executes directly against PostgreSQL.
- Output is 100% byte-for-byte identical to cache-enabled results.

---

## 2. Multi-Worker Deployment Policy

> [!CAUTION]
> **MULTI-PROCESS LIMITATION:**
> The cache implementation is an **in-process bounded LRU cache**. It resides entirely in application process RAM.
>
> If `WORKER_COUNT > 1` or multiple processes/containers are deployed behind a load balancer without sticky sessions:
> - Each worker maintains an independent, un-synchronized in-process cache.
> - An invalidation event occurring on Worker 1 will **not** invalidate the cache on Worker 2.
> - Therefore, `CACHE_ENABLED=true` is supported **ONLY for single-process deployments** (`WORKER_COUNT=1`).
>
> If `WORKER_COUNT > 1` is configured with `CACHE_ENABLED=true`, the application automatically flags an operational error and disables caching, reverting all workers to direct PostgreSQL queries.

---

## 3. Cache Flush & Version Bumping

### Instant Cache Invalidation across All Entries:
To invalidate the entire cache without restarting the process:
1. **Version Bump**: Increment `CACHE_VERSION` in the environment (e.g. from `v1` to `v2`). Because all cache keys are prefixed with `v{CACHE_VERSION}`, previous entries become unreachable and are automatically evicted by LRU.
2. **Runtime Programmatic Clear**: Call `cache_service.clear()`.

### Series-Scoped Flush:
To manually invalidate a specific series (e.g. following an administrative backfill):
```python
cache_service.invalidate_series(series_id)
```

---

## 4. Invalidation Failure & Dirty Bypass Recovery

If an exception occurs during cache invalidation:
1. The series namespace is added to the cache backend's `dirty_namespaces` registry.
2. Every subsequent lookup for `series_id` logs a warning and immediately bypasses the cache, querying PostgreSQL directly.
3. Once the administrator resolves the issue or runs `cache_service.clean_series(series_id)` / `clear()`, caching for that series safely resumes.

---

## 5. Observability & Monitoring

The cache emits structured JSON logs integrated with the Phase 4.6 observability pipeline:
- `cache.hit`: Successful retrieval from cache. Includes `duration_ms`, `series_id`, `reader_chapter`, `key`.
- `cache.miss`: Key not found; data fetched from DB and populated into cache.
- `cache.set`: Successful storage in cache. Includes payload byte size.
- `cache.rejected`: Payload exceeded `CACHE_MAX_ENTRY_BYTES`. Stored skipped; computed result returned safely.
- `cache.invalidate`: Series namespace invalidation executed.
- `cache.dirty`: Series namespace flagged dirty due to invalidation failure; bypassing cache.
- `cache.error`: Cache backend raised unexpected exception; degraded safely to PostgreSQL.

**Privacy Guarantee**: Under no circumstances are story payloads, secret keys, or future spoilers logged.
