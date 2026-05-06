# Playwright Migration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `scraper/browser.py` (undetected-chromedriver) with Playwright persistent context + playwright-stealth to reliably bypass Cloudflare on weworkremotely.com.

**Architecture:** `browser.py` is rewritten around `launch_persistent_context` which stores the `cf_clearance` Cloudflare cookie in `browser_profile/` between runs. First run is headed (visible browser) to earn clearance; subsequent runs are headless. `main.py` needs only a `driver` → `context` rename.

**Tech Stack:** Python 3.12, playwright (sync API), playwright-stealth, BeautifulSoup, psycopg2

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `requirements.txt` | Add `playwright`, `playwright-stealth`; remove `undetected-chromedriver` |
| Modify | `.gitignore` | Add `browser_profile/` |
| Rewrite | `scraper/browser.py` | Playwright persistent context, stealth, fetch logic |
| Modify | `tests/test_scraper_config.py` | Replace `USER_AGENT` assertion with `BOT_CHALLENGE_RETRIES` assertion |
| Modify | `scraper/main.py` | Rename `create_driver` → `create_context`, `driver` → `context`, `driver.quit()` → `context.stop()` |

> **Note:** `scraper/backfill_details.py` does not exist yet. When it is implemented, apply the same `driver` → `context` rename pattern from Task 4.

---

## Task 1: Install dependencies and update project config

**Files:**
- Modify: `requirements.txt`
- Modify: `.gitignore`

- [ ] **Step 1: Install playwright and playwright-stealth into the project venv**

Run these in your terminal (activate your project venv first,`.venv-dbt`):

```
pip install playwright playwright-stealth
```

- [ ] **Step 2: Download Playwright's Chromium browser binary**

```
playwright install chromium
```

Expected: output like `Downloading Chromium 130.x.x...` followed by `✓ Chromium 130.x.x (playwright build) downloaded`.

- [ ] **Step 3: Update `requirements.txt`**

Replace the `undetected-chromedriver==3.5.5` line with the two new packages. Run this to capture exact pinned versions:

```
pip freeze | findstr /I "playwright"
```

Expected output (versions may differ slightly):
```
playwright==1.x.x
playwright-stealth==1.x.x
```

Open `requirements.txt` and make these two edits:
- Remove the line: `undetected-chromedriver==3.5.5`
- Add the two playwright lines with the exact versions from pip freeze

- [ ] **Step 4: Add `browser_profile/` to `.gitignore`**

Open `.gitignore` and add this line in the `# Environments` section (after `.venv`):

```
browser_profile/
```

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .gitignore
git commit -m "deps: add playwright + playwright-stealth, remove undetected-chromedriver"
```

---

## Task 2: Rewrite `scraper/browser.py`

**Files:**
- Rewrite: `scraper/browser.py`

- [ ] **Step 1: Replace the entire contents of `scraper/browser.py`**

```python
from __future__ import annotations

import os
import random
import time

from playwright.sync_api import BrowserContext, sync_playwright
from playwright_stealth import stealth_sync

from scraper.log import get_logger

logger = get_logger(__name__)

BOT_CHALLENGE_RETRIES = 3
_PROFILE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "browser_profile")


def create_context() -> BrowserContext:
    headless = os.getenv("SCRAPER_HEADLESS", "false").lower() == "true"
    pw = sync_playwright().start()
    context = pw.chromium.launch_persistent_context(
        user_data_dir=_PROFILE_DIR,
        headless=headless,
        channel="chrome",
        args=["--disable-blink-features=AutomationControlled"],
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
    )

    def _stop() -> None:
        context.close()
        pw.stop()

    context.stop = _stop  # patch stop() so callers use context.stop() for full cleanup
    logger.debug("Created persistent browser context (headless=%s, profile=%s)", headless, _PROFILE_DIR)
    return context


def fetch_page(context: BrowserContext, url: str) -> str:
    last_source = ""
    for attempt in range(BOT_CHALLENGE_RETRIES):
        page = context.new_page()
        try:
            stealth_sync(page)
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            _polite_delay()
            _human_scroll(page)
            page_source = page.content()
            last_source = page_source
            if not _looks_like_bot_challenge(page_source):
                return page_source
        finally:
            page.close()
        logger.warning(
            "Bot challenge detected on %s (attempt %d/%d)",
            url, attempt + 1, BOT_CHALLENGE_RETRIES,
        )
        if attempt < BOT_CHALLENGE_RETRIES - 1:
            time.sleep(random.uniform(6.0, 12.0))
    logger.error("All %d attempts failed for %s — returning last page source", BOT_CHALLENGE_RETRIES, url)
    return last_source


def _polite_delay() -> None:
    time.sleep(random.uniform(3.0, 6.0))


def _human_scroll(page) -> None:
    try:
        page.evaluate("window.scrollTo(0, 400)")
        time.sleep(random.uniform(0.2, 0.4))
        page.evaluate("window.scrollTo(0, 800)")
        time.sleep(random.uniform(0.2, 0.4))
        page.evaluate("window.scrollTo(0, 0)")
    except Exception:
        pass


def _looks_like_bot_challenge(html: str) -> bool:
    lower = html.lower()
    markers = [
        "just a moment",
        "security verification",
        "checking your browser",
        "enable javascript",
        "cf-browser-verification",
        "challenge-platform",
        "ray id",
    ]
    return any(m in lower for m in markers)
```

- [ ] **Step 2: Run the existing test suite to confirm nothing is broken**

```
pytest tests/ -v
```

Expected: the `test_scraper_user_agent_matches_issue_requirement` test will **FAIL** (it looks for `USER_AGENT` which no longer exists). All other tests should PASS. This failure is expected and is fixed in Task 3.

- [ ] **Step 3: Commit**

```bash
git add scraper/browser.py
git commit -m "feat(scraper): replace undetected-chromedriver with Playwright persistent context"
```

---

## Task 3: Update `tests/test_scraper_config.py`

**Files:**
- Modify: `tests/test_scraper_config.py`

- [ ] **Step 1: Replace the `test_scraper_user_agent_matches_issue_requirement` test**

Open `tests/test_scraper_config.py`. Replace this function:

```python
def test_scraper_user_agent_matches_issue_requirement():
    user_agent = _literal_from_assignment(ROOT / "scraper" / "browser.py", "USER_AGENT")
    assert "Mozilla" in user_agent
```

With this:

```python
def test_bot_challenge_retries_is_three():
    retries = _literal_from_assignment(ROOT / "scraper" / "browser.py", "BOT_CHALLENGE_RETRIES")
    assert retries == 3
```

- [ ] **Step 2: Run the test to confirm it passes**

```
pytest tests/test_scraper_config.py -v
```

Expected: 3 tests PASS.
```
PASSED tests/test_scraper_config.py::test_bot_challenge_retries_is_three
PASSED tests/test_scraper_config.py::test_scraper_targets_programming_categories
PASSED tests/test_scraper_config.py::test_scraper_max_pages_capped_at_five
```

- [ ] **Step 3: Run the full test suite**

```
pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/test_scraper_config.py
git commit -m "test(scraper): replace USER_AGENT assertion with BOT_CHALLENGE_RETRIES for Playwright migration"
```

---

## Task 4: Update `scraper/main.py`

**Files:**
- Modify: `scraper/main.py`

- [ ] **Step 1: Replace the entire contents of `scraper/main.py`**

```python
from __future__ import annotations

import psycopg2
from dotenv import load_dotenv

from scraper.browser import create_context, fetch_page
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
}
MAX_PAGES = 5


def get_connection(db_url: str) -> psycopg2.extensions.connection:
    return psycopg2.connect(db_url)


def scrape_category(context, conn, category: str, slug: str) -> int:
    loaded = 0
    for page in range(1, MAX_PAGES + 1):
        url = f"{WWR_BASE}{slug}?page={page}"
        logger.info("Fetching %s (page %d)", slug, page)
        html = fetch_page(context, url)
        listings = parse_listings(html, category=category)
        logger.info("  -> parsed %d listings from page %d", len(listings), page)
        if not listings:
            logger.info("No listings on page %d for %s — stopping", page, slug)
            break
        for listing in listings:
            logger.debug("  -> detail: %s", listing["url"])
            detail_html = fetch_page(context, listing["url"])
            detail_fields = parse_job_detail(detail_html)
            listing["date_posted"] = listing["date_posted"] or detail_fields["date_posted"]
            listing["salary_raw"] = listing["salary_raw"] or detail_fields["salary_raw"]
            listing["description_raw"] = detail_fields["description_raw"]
            logger.debug(
                "     title=%r  desc=%s  salary=%r",
                listing["title"],
                f"{len(listing['description_raw'])} chars" if listing["description_raw"] else "None",
                listing["salary_raw"],
            )
            upsert_listing(conn, listing)
            loaded += 1
        flush(conn)
        logger.info("Flushed page %d (%d listings so far for %s)", page, loaded, slug)
    return loaded


def main() -> None:
    db_url = validate_env()
    conn = get_connection(db_url)
    ensure_table(conn)
    context = create_context()
    try:
        for category, slugs in CATEGORY_SOURCES.items():
            if not slugs:
                logger.warning("%s: skipped (no active source categories)", category)
                continue
            count = 0
            for slug in slugs:
                count += scrape_category(context, conn, category, slug)
            logger.info("%s: loaded %d listings", category, count)
    finally:
        context.stop()
        conn.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the full test suite**

```
pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add scraper/main.py
git commit -m "feat(scraper): wire Playwright context into main.py — driver -> context rename"
```

---

## Task 5: Verify headed run bypasses Cloudflare

This task has no code changes. It confirms the migration works end-to-end.

- [ ] **Step 1: Run the scraper headed (default) to earn Cloudflare clearance**

Make sure `SCRAPER_HEADLESS` is not set (or explicitly set to `false`). Run:

```
python -m scraper.main
```

A Chrome window will open. Watch it navigate to weworkremotely.com. If Cloudflare shows a challenge page, wait — with `playwright-stealth` + a real Chrome profile it should auto-pass within a few seconds. If it hangs on a challenge, you may need to briefly interact with the browser (check a box, wait for the spinner).

Expected outcome: scraper logs show listings being parsed and flushed, no `Bot challenge detected` warnings, and `browser_profile/` directory is created at the project root containing cookie/session files.

- [ ] **Step 2: Confirm `browser_profile/` was created**

```
ls browser_profile/
```

Expected: directory exists and contains files (Cookies, Local State, etc.).

- [ ] **Step 3: Run headless to confirm persistent clearance works**

```bash
$env:SCRAPER_HEADLESS="true"
python -m scraper.main
```

Expected: scraper runs without a visible browser window, no bot challenge warnings, listings load successfully. If Cloudflare re-challenges, set `SCRAPER_HEADLESS=false` and re-run once to refresh the `cf_clearance` cookie.

---

## Completion Checklist

- [ ] `pytest tests/ -v` — all tests green
- [ ] `scraper/browser.py` uses `create_context()`, `fetch_page(context, url)`, `BOT_CHALLENGE_RETRIES = 3`
- [ ] `browser_profile/` exists in `.gitignore`
- [ ] `requirements.txt` has `playwright` and `playwright-stealth`, no `undetected-chromedriver`
- [ ] `scraper/main.py` uses `create_context`, `context`, `context.stop()`
- [ ] Headed run reaches weworkremotely.com without bot challenge
- [ ] Headless run reuses `cf_clearance` from profile successfully
