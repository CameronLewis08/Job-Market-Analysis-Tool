# Backend Pipeline Improvements — Design Spec

**Date:** 2026-05-04  
**Branch:** phase-1  
**Scope:** Scraper reliability, data quality, CI pipeline wiring

---

## Overview

Five targeted improvements to the backend pipeline. No new external dependencies. Each change is surgical and independently reversible.

---

## 1. Shared Logging Module (`scraper/log.py`)

**What:** A new ~10-line module that configures Python's built-in `logging` once with a consistent format.

**Format:**
```
2026-05-04 12:00:00 [INFO] scraper.main: Starting scrape for category=programming-python
```

**Details:**
- Level defaults to `INFO`; set `LOG_LEVEL=DEBUG` env var to enable debug output
- Every scraper module gets `logger = logging.getLogger(__name__)` and replaces bare `print()` calls
- `browser.py` logs each retry attempt and bot-challenge detection
- `main.py` logs per-category start/finish and listing counts
- `backfill_details.py` logs batch progress and skipped listings

**Files changed:** `scraper/log.py` (new), `scraper/main.py`, `scraper/browser.py`, `scraper/backfill_details.py`

---

## 2. Env Var Validation

**What:** A `validate_env()` function at the top of each entry point that checks required vars before any driver or DB connection opens.

**Required vars:** `DATABASE_URL`  
**Optional with defaults:** `LOG_LEVEL` (default `INFO`), `MAX_PAGES` (default `5`)

**Behaviour on failure:** Logs a `CRITICAL` message and exits with code 1 — no stack trace, no silent hang.

```python
def validate_env() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        logging.critical("DATABASE_URL is not set — aborting")
        sys.exit(1)
    return url
```

**Called as:** first line of `main()` in both `scraper/main.py` and `scraper/backfill_details.py`.

**Files changed:** `scraper/main.py`, `scraper/backfill_details.py`

---

## 3. Loader Batching (`scraper/loader.py`)

**What:** Replace single-row commits with batch inserts using `executemany()`.

**Public API change:** `upsert_listing()` stays the same signature. A new `flush(conn)` function drains the accumulated batch and commits once.

```python
_batch: list[tuple] = []

def upsert_listing(conn, listing: dict) -> None:
    _batch.append((...))  # no commit

def flush(conn) -> None:
    if _batch:
        cur.executemany(UPSERT_SQL, _batch)
        conn.commit()
        _batch.clear()
```

**Commit cadence:**
- `main.py`: calls `flush()` after each page (~20 listings), not after each listing
- `backfill_details.py`: calls `flush()` after each batch of 100

**Performance impact:** Reduces DB round-trips from ~100 to ~5 per full scrape run.

**Note:** `_batch` is module-level state. This is safe because the scraper is single-threaded; do not use this pattern if concurrency is added later.

**Files changed:** `scraper/loader.py`, `scraper/main.py`, `scraper/backfill_details.py`

---

## 4. Skill Matching Fix (`dbt/models/intermediate/int_listing_skills.sql`)

**What:** Replace `ILIKE '%skill%'` with PostgreSQL word-boundary regex to eliminate false positives.

```sql
-- before
WHERE s.description_raw ILIKE '%' || sk.skill || '%'

-- after
WHERE s.description_raw ~* ('\m' || sk.skill || '\m')
```

**Details:**
- `\m` / `\M` are POSIX word-boundary anchors in PostgreSQL
- `~*` is case-insensitive regex match (equivalent to `ILIKE` in strictness level, stricter in boundary matching)
- Eliminates false positives: "python" no longer matches "cpython" or "jython"
- No new dependencies; same query plan complexity

**Files changed:** `dbt/models/intermediate/int_listing_skills.sql`

---

## 5. Backfill in CI (`.github/workflows/pipeline.yml`)

**What:** Add `backfill_details.py` as a sequential step between scrape and dbt run.

```yaml
steps:
  - name: Scrape listings
    run: python scraper/main.py

  - name: Backfill missing details
    run: python scraper/backfill_details.py

  - name: Run dbt
    run: dbt seed && dbt run && dbt test
```

**Details:**
- Uses the existing `DATABASE_URL` secret — no new secrets required
- If backfill fails, workflow halts before dbt runs (correct: dbt skill matching depends on `description_raw` being populated)
- No new jobs or schedule changes

**Files changed:** `.github/workflows/pipeline.yml`

---

## Implementation Order

1. `scraper/log.py` — foundation; other modules depend on it
2. `scraper/loader.py` — batching; touch `main.py` and `backfill_details.py` together
3. `scraper/main.py` + `scraper/backfill_details.py` — env validation + logging wired in
4. `scraper/browser.py` — logging wired in
5. `dbt/models/intermediate/int_listing_skills.sql` — regex fix
6. `.github/workflows/pipeline.yml` — backfill step added

---

## Out of Scope (Next Cycle)

- Dashboard freshness indicator (separate spec)
- Type hints across all modules
- Data retention policy
- Dashboard CSV export
