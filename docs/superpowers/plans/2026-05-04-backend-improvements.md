# Backend Pipeline Improvements — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add structured logging, env-var validation, batched DB commits, word-boundary skill matching, and automated backfill to the scraper pipeline.

**Architecture:** A new `scraper/log.py` module centralises logging config and `validate_env()`; all other changes are surgical edits to existing files. Each improvement is independently reversible.

**Tech Stack:** Python 3.11, psycopg2, Python `logging`, dbt-postgres, GitHub Actions

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `scraper/log.py` | Logging config + `validate_env()` |
| Create | `tests/test_log.py` | Tests for `log.py` |
| Create | `tests/test_loader.py` | Tests for batched loader |
| Modify | `scraper/loader.py` | Add `_batch`, `flush()`, make `upsert_listing` append-only |
| Modify | `scraper/main.py` | Wire logging, `validate_env()`, `flush()` |
| Modify | `scraper/backfill_details.py` | Wire logging, `validate_env()`, `flush()` |
| Modify | `scraper/browser.py` | Wire logging |
| Modify | `dbt/models/intermediate/int_listing_skills.sql` | Word-boundary regex |
| Modify | `.github/workflows/pipeline.yml` | Add backfill step |

---

## Task 1: Create `scraper/log.py`

**Files:**
- Create: `scraper/log.py`
- Create: `tests/test_log.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_log.py`:

```python
from __future__ import annotations

import logging

import pytest

from scraper.log import configure_logging, get_logger, validate_env


def test_get_logger_returns_logger_with_correct_name():
    configure_logging()
    logger = get_logger("scraper.test")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "scraper.test"


def test_validate_env_returns_url_when_set(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host/db")
    url = validate_env()
    assert url == "postgresql://user:pass@host/db"


def test_validate_env_exits_when_missing(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        validate_env()
    assert exc_info.value.code == 1
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/test_log.py -v
```

Expected: `ImportError` — `scraper.log` does not exist yet.

- [ ] **Step 3: Create `scraper/log.py`**

```python
from __future__ import annotations

import logging
import os
import sys


def configure_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def validate_env() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        logging.critical("DATABASE_URL is not set — aborting")
        sys.exit(1)
    return url
```

- [ ] **Step 4: Run tests to confirm they pass**

```
pytest tests/test_log.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scraper/log.py tests/test_log.py
git commit -m "feat(scraper): add shared log.py with configure_logging and validate_env"
```

---

## Task 2: Batch loader — `scraper/loader.py`

**Files:**
- Modify: `scraper/loader.py`
- Create: `tests/test_loader.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_loader.py`:

```python
from __future__ import annotations

from unittest.mock import MagicMock

import scraper.loader as loader_module
from scraper.loader import flush, upsert_listing

SAMPLE_LISTING = {
    "id": "acme-senior-engineer-001",
    "title": "Senior Engineer",
    "company": "Acme",
    "category": "programming",
    "date_posted": None,
    "url": "https://weworkremotely.com/remote-jobs/acme-senior-engineer-001",
    "location_restriction": None,
    "salary_raw": None,
    "description_raw": None,
}


def _make_conn() -> MagicMock:
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = MagicMock()
    return conn


def setup_function():
    loader_module._batch.clear()


def test_upsert_listing_appends_to_batch_without_committing():
    conn = _make_conn()
    upsert_listing(conn, SAMPLE_LISTING)
    assert len(loader_module._batch) == 1
    conn.commit.assert_not_called()


def test_flush_executes_batch_and_commits():
    conn = _make_conn()
    mock_cur = conn.cursor.return_value.__enter__.return_value
    loader_module._batch.append(SAMPLE_LISTING)

    count = flush(conn)

    assert count == 1
    mock_cur.executemany.assert_called_once()
    conn.commit.assert_called_once()
    assert loader_module._batch == []


def test_flush_does_nothing_when_batch_is_empty():
    conn = _make_conn()
    count = flush(conn)
    assert count == 0
    conn.commit.assert_not_called()


def test_multiple_listings_flushed_together():
    conn = _make_conn()
    mock_cur = conn.cursor.return_value.__enter__.return_value
    upsert_listing(conn, SAMPLE_LISTING)
    upsert_listing(conn, {**SAMPLE_LISTING, "id": "acme-senior-engineer-002"})

    count = flush(conn)

    assert count == 2
    args = mock_cur.executemany.call_args
    assert len(args[0][1]) == 2
    conn.commit.assert_called_once()
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/test_loader.py -v
```

Expected: `AttributeError` — `flush` does not exist yet.

- [ ] **Step 3: Rewrite `scraper/loader.py`**

Replace the entire file:

```python
from __future__ import annotations

import psycopg2

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_listings (
    id                   VARCHAR PRIMARY KEY,
    title                VARCHAR NOT NULL,
    company              VARCHAR,
    category             VARCHAR,
    date_posted          DATE,
    url                  VARCHAR,
    location_restriction VARCHAR,
    salary_raw           VARCHAR,
    description_raw      TEXT,
    scraped_at           TIMESTAMP DEFAULT NOW()
);
"""

UPSERT_SQL = """
INSERT INTO raw_listings
    (id, title, company, category, date_posted, url, location_restriction, salary_raw, description_raw)
VALUES
    (%(id)s, %(title)s, %(company)s, %(category)s, %(date_posted)s, %(url)s, %(location_restriction)s, %(salary_raw)s, %(description_raw)s)
ON CONFLICT (id) DO UPDATE SET
    title = COALESCE(EXCLUDED.title, raw_listings.title),
    company = COALESCE(EXCLUDED.company, raw_listings.company),
    category = COALESCE(EXCLUDED.category, raw_listings.category),
    date_posted = COALESCE(EXCLUDED.date_posted, raw_listings.date_posted),
    url = COALESCE(EXCLUDED.url, raw_listings.url),
    location_restriction = COALESCE(EXCLUDED.location_restriction, raw_listings.location_restriction),
    salary_raw = COALESCE(EXCLUDED.salary_raw, raw_listings.salary_raw),
    description_raw = COALESCE(EXCLUDED.description_raw, raw_listings.description_raw),
    scraped_at = NOW();
"""

# Module-level batch. Single-threaded only — do not use with concurrent scrapers.
_batch: list[dict] = []


def ensure_table(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cur:
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()


def upsert_listing(conn: psycopg2.extensions.connection, listing: dict) -> None:
    _batch.append(listing)


def flush(conn: psycopg2.extensions.connection) -> int:
    if not _batch:
        return 0
    with conn.cursor() as cur:
        cur.executemany(UPSERT_SQL, _batch)
    conn.commit()
    count = len(_batch)
    _batch.clear()
    return count
```

- [ ] **Step 4: Run tests to confirm they pass**

```
pytest tests/test_loader.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Run full test suite to check for regressions**

```
pytest tests/ -v
```

Expected: all existing tests still PASS.

- [ ] **Step 6: Commit**

```bash
git add scraper/loader.py tests/test_loader.py
git commit -m "feat(scraper): batch loader upserts with flush() — reduces DB round-trips from ~100 to ~5 per run"
```

---

## Task 3: Wire logging + validate_env + flush into `scraper/main.py`

**Files:**
- Modify: `scraper/main.py`

No new tests — `main.py` is orchestration. The logging and validate_env behaviour is already tested in `test_log.py`; flush is tested in `test_loader.py`.

- [ ] **Step 1: Replace `scraper/main.py` with the updated version**

```python
from __future__ import annotations

import os

import psycopg2
from dotenv import load_dotenv

from scraper.browser import create_driver, fetch_page
from scraper.loader import ensure_table, flush, upsert_listing
from scraper.log import configure_logging, get_logger, validate_env
from scraper.parser import parse_job_detail, parse_listings

load_dotenv()
configure_logging()
logger = get_logger(__name__)

WWR_BASE = "https://weworkremotely.com"
CATEGORY_SOURCES = {
    "programming": [
        "/categories/remote-full-stack-programming-jobs",
        "/categories/remote-back-end-programming-jobs",
        "/categories/remote-front-end-programming-jobs",
        "/categories/remote-devops-sysadmin-jobs",
    ],
    "data-science": [],
}
MAX_PAGES = 5
ENRICH_DETAIL_FIELDS = os.getenv("SCRAPER_ENRICH_DETAILS", "false").lower() == "true"


def get_connection() -> psycopg2.extensions.connection:
    return psycopg2.connect(validate_env())


def scrape_category(driver, conn, category: str, slug: str) -> int:
    loaded = 0
    for page in range(1, MAX_PAGES + 1):
        url = f"{WWR_BASE}{slug}?page={page}"
        logger.info("Fetching %s (page %d)", slug, page)
        html = fetch_page(driver, url)
        listings = parse_listings(html, category=category)
        if not listings:
            logger.info("No listings on page %d for %s — stopping", page, slug)
            break
        for listing in listings:
            if ENRICH_DETAIL_FIELDS:
                detail_html = fetch_page(driver, listing["url"])
                detail_fields = parse_job_detail(detail_html)
                listing["date_posted"] = listing["date_posted"] or detail_fields["date_posted"]
                listing["salary_raw"] = listing["salary_raw"] or detail_fields["salary_raw"]
                listing["description_raw"] = detail_fields["description_raw"] or listing["description_raw"]
            upsert_listing(conn, listing)
            loaded += 1
        flush(conn)
        logger.debug("Flushed page %d (%d listings so far for %s)", page, loaded, slug)
    return loaded


def main() -> None:
    conn = get_connection()
    ensure_table(conn)
    driver = create_driver()
    try:
        for category, slugs in CATEGORY_SOURCES.items():
            if not slugs:
                logger.warning("%s: skipped (no active source categories)", category)
                continue
            count = 0
            for slug in slugs:
                count += scrape_category(driver, conn, category, slug)
            logger.info("%s: loaded %d listings", category, count)
    finally:
        driver.quit()
        conn.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run full test suite**

```
pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add scraper/main.py
git commit -m "feat(scraper): wire logging, validate_env, and flush into main.py"
```

---

## Task 4: Wire logging + validate_env + flush into `scraper/backfill_details.py`

**Files:**
- Modify: `scraper/backfill_details.py`

- [ ] **Step 1: Replace `scraper/backfill_details.py` with the updated version**

```python
from __future__ import annotations

import os

import psycopg2
from dotenv import load_dotenv

from scraper.browser import create_driver, fetch_page
from scraper.loader import flush, upsert_listing
from scraper.log import configure_logging, get_logger, validate_env
from scraper.parser import parse_job_detail

load_dotenv()
configure_logging()
logger = get_logger(__name__)

DEFAULT_BATCH_SIZE = 100


def get_connection() -> psycopg2.extensions.connection:
    return psycopg2.connect(validate_env())


def backfill_missing_details(batch_size: int) -> int:
    conn = get_connection()
    driver = create_driver()
    updated = 0

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                select id, title, company, category, date_posted, url, location_restriction, salary_raw, description_raw
                from raw_listings
                where url is not null
                  and (date_posted is null or salary_raw is null or description_raw is null)
                order by scraped_at desc
                limit %s
                """,
                (batch_size,),
            )
            rows = cur.fetchall()

        logger.info("Found %d listings to backfill", len(rows))

        for row in rows:
            listing = {
                "id": row[0],
                "title": row[1],
                "company": row[2],
                "category": row[3],
                "date_posted": row[4],
                "url": row[5],
                "location_restriction": row[6],
                "salary_raw": row[7],
                "description_raw": row[8],
            }

            if not listing["url"]:
                logger.debug("Skipping listing %s — no URL", listing["id"])
                continue

            html = fetch_page(driver, listing["url"])
            detail_fields = parse_job_detail(html)
            listing["date_posted"] = listing["date_posted"] or detail_fields["date_posted"]
            listing["salary_raw"] = listing["salary_raw"] or detail_fields["salary_raw"]
            listing["description_raw"] = listing["description_raw"] or detail_fields["description_raw"]

            upsert_listing(conn, listing)
            updated += 1

        flush(conn)
        logger.info("Backfilled %d listings", updated)
        return updated
    finally:
        driver.quit()
        conn.close()


def main() -> None:
    batch_size = int(os.getenv("SCRAPER_DETAIL_BACKFILL_LIMIT", str(DEFAULT_BATCH_SIZE)))
    backfill_missing_details(batch_size)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run full test suite**

```
pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add scraper/backfill_details.py
git commit -m "feat(scraper): wire logging, validate_env, and flush into backfill_details.py"
```

---

## Task 5: Wire logging into `scraper/browser.py`

**Files:**
- Modify: `scraper/browser.py`

- [ ] **Step 1: Replace `scraper/browser.py` with the updated version**

```python
from __future__ import annotations

import os
import random
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from scraper.log import get_logger

logger = get_logger(__name__)

USER_AGENT = "JobMarketResearchBot/1.0"
BOT_CHALLENGE_RETRIES = 3


def create_driver() -> webdriver.Chrome:
    options = Options()
    if os.getenv("SCRAPER_HEADLESS", "true").lower() == "true":
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--user-agent={USER_AGENT}")
    logger.debug("Creating Chrome driver")
    return webdriver.Chrome(options=options)


def fetch_page(driver: webdriver.Chrome, url: str) -> str:
    last_source = ""
    for attempt in range(BOT_CHALLENGE_RETRIES):
        driver.get(url)
        _polite_delay()
        page_source = driver.page_source
        last_source = page_source
        if not _looks_like_bot_challenge(page_source):
            return page_source
        logger.warning(
            "Bot challenge detected on %s (attempt %d/%d)",
            url, attempt + 1, BOT_CHALLENGE_RETRIES,
        )
        if attempt < BOT_CHALLENGE_RETRIES - 1:
            time.sleep(4)
    logger.error("All %d attempts failed for %s — returning last page source", BOT_CHALLENGE_RETRIES, url)
    return last_source


def _polite_delay() -> None:
    time.sleep(random.uniform(2.0, 3.0))


def _looks_like_bot_challenge(html: str) -> bool:
    lower = html.lower()
    return "just a moment..." in lower and "security verification" in lower
```

- [ ] **Step 2: Run full test suite**

```
pytest tests/ -v
```

Expected: all tests PASS. (The scraper config test validates `USER_AGENT` — confirm it still passes.)

- [ ] **Step 3: Commit**

```bash
git add scraper/browser.py
git commit -m "feat(scraper): add logging to browser.py — logs retries and bot-challenge failures"
```

---

## Task 6: Fix word-boundary skill matching in dbt

**Files:**
- Modify: `dbt/models/intermediate/int_listing_skills.sql`

- [ ] **Step 1: Replace line 18 in `dbt/models/intermediate/int_listing_skills.sql`**

Full file after change:

```sql
with listings as (
    select * from {{ ref('stg_listings') }}
    where description_raw is not null
),

skills as (
    select * from {{ ref('skills') }}
)

select
    l.id         as listing_id,
    l.date_posted,
    l.category   as listing_category,
    s.skill,
    s.category   as skill_category
from listings l
cross join skills s
where l.description_raw ~* ('\m' || s.skill || '\m')
```

The only change is line 18: `ilike '%' || s.skill || '%'` → `~* ('\m' || s.skill || '\m')`.

`\m` is a PostgreSQL POSIX word-boundary anchor. `~*` is case-insensitive regex match. This prevents "python" from matching "cpython" or "jython".

- [ ] **Step 2: Run dbt to verify the model compiles and passes schema tests**

From the `dbt/` directory:

```
dbt run --select int_listing_skills
dbt test --select int_listing_skills
```

Expected: model runs and all `not_null` tests pass. If you have a live `DATABASE_URL` set locally, check the row count — it should be slightly lower than before (false positives removed).

- [ ] **Step 3: Commit**

```bash
git add dbt/models/intermediate/int_listing_skills.sql
git commit -m "fix(dbt): use word-boundary regex for skill matching — eliminates false positives like cpython matching python"
```

---

## Task 7: Add backfill step to CI pipeline

**Files:**
- Modify: `.github/workflows/pipeline.yml`

- [ ] **Step 1: Add the backfill step between "Run scraper" and "Run dbt"**

Full updated `pipeline.yml`:

```yaml
name: Weekly ETL Pipeline

on:
  schedule:
    - cron: '0 6 * * 1'  # Monday 6am UTC
  workflow_dispatch:

jobs:
  run-pipeline:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Set up ChromeDriver
        uses: browser-actions/setup-chrome@v1

      - name: Run scraper
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          NEON_HOST: ${{ secrets.NEON_HOST }}
          NEON_DB: ${{ secrets.NEON_DB }}
          NEON_USER: ${{ secrets.NEON_USER }}
          NEON_PASSWORD: ${{ secrets.NEON_PASSWORD }}
        run: python -m scraper.main

      - name: Backfill missing details
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: python -m scraper.backfill_details

      - name: Run dbt
        env:
          NEON_HOST: ${{ secrets.NEON_HOST }}
          NEON_DB: ${{ secrets.NEON_DB }}
          NEON_USER: ${{ secrets.NEON_USER }}
          NEON_PASSWORD: ${{ secrets.NEON_PASSWORD }}
        working-directory: dbt
        run: |
          dbt deps
          dbt seed
          dbt run
          dbt test
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/pipeline.yml
git commit -m "ci: add backfill step between scrape and dbt — ensures description_raw populated before skill matching"
```

---

## Completion Checklist

- [ ] `pytest tests/ -v` — all tests green
- [ ] `scraper/log.py` exists with `configure_logging`, `get_logger`, `validate_env`
- [ ] `scraper/loader.py` has `_batch`, `upsert_listing` (append-only), `flush`
- [ ] `scraper/main.py` calls `configure_logging()`, `validate_env()`, `flush()` per page, uses `logger` not `print`
- [ ] `scraper/backfill_details.py` calls `configure_logging()`, `validate_env()`, `flush()` after loop, uses `logger` not `print`
- [ ] `scraper/browser.py` logs bot-challenge warnings and retry failures
- [ ] `int_listing_skills.sql` uses `~*` with `\m` word-boundary anchors
- [ ] `pipeline.yml` has backfill step between scraper and dbt
