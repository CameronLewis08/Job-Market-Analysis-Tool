# Playwright Migration — Design Spec

**Date:** 2026-05-06
**Branch:** phase-1
**Scope:** Replace `scraper/browser.py` (undetected-chromedriver) with Playwright persistent context

---

## Overview

`weworkremotely.com` uses Cloudflare bot protection that is consistently defeating the current `undetected-chromedriver` implementation. This spec replaces `scraper/browser.py` with Playwright's `launch_persistent_context` API, which persists the `cf_clearance` Cloudflare cookie across runs. First run is headed (browser window visible) to let Cloudflare issue clearance; subsequent runs are headless and reuse the stored profile.

---

## Architecture

Replace `scraper/browser.py` entirely. All other pipeline modules (`main.py`, `backfill_details.py`, `parser.py`, `loader.py`) are untouched except a two-line `driver` → `context` rename in `main.py` and `backfill_details.py`.

A `browser_profile/` directory at the project root stores the persistent Chromium profile (cookies, localStorage, TLS session state). It is gitignored and created automatically on first run. Once Cloudflare issues `cf_clearance` into the profile during a headed run, every subsequent headless run reuses it.

**New dependencies:** `playwright`, `playwright-stealth`
**Removed dependencies:** `undetected-chromedriver`, `setuptools` (distutils shim — no longer needed)

**One-time setup (not in requirements.txt):** After `pip install playwright`, run `playwright install chromium` to download the Playwright browser binary. Since we use `channel="chrome"` (system Chrome), this is a fallback binary — but the CLI step is required to install Playwright's browser infrastructure.

---

## Components

### `scraper/browser.py` (full rewrite)

Two public functions:

**`create_context() -> BrowserContext`**
- Starts a Playwright sync instance
- Launches `chromium.launch_persistent_context(user_data_dir="browser_profile/", headless=<SCRAPER_HEADLESS>, channel="chrome")`
- `channel="chrome"` uses the real installed Chrome binary for a genuine fingerprint
- Returns the context

**`fetch_page(context: BrowserContext, url: str) -> str`**
- Opens a new page from the context
- Applies `stealth_sync(page)` from `playwright-stealth`
- Navigates to `url` with `wait_until="domcontentloaded"`
- Waits for page to settle
- Extracts `page.content()` (full rendered HTML post-JS)
- Closes the page in a `finally` block (page leak guard)
- Returns HTML string
- Bot-challenge detection and retry logic identical to current implementation

**Env var:** `SCRAPER_HEADLESS` — defaults to `"false"`. Set to `"true"` once the persistent profile has Cloudflare clearance confirmed.

**Constants retained:** `BOT_CHALLENGE_RETRIES = 3`, `_looks_like_bot_challenge()` unchanged.

### `browser_profile/`

Gitignored directory at project root. Auto-created by Playwright on first run. Stores cookies (including `cf_clearance`), localStorage, and TLS session state.

### `scraper/main.py` and `scraper/backfill_details.py`

Two-line rename only:
- `create_driver` → `create_context`
- `driver` → `context`
- `driver.quit()` → `context.stop()`

### Playwright MCP (VS Code)

Used after initial setup to navigate WWR live and confirm CSS selectors for the parser. Not part of the production code path.

---

## Error Handling

- **Page leak guard:** `fetch_page` wraps page usage in `try/finally` — page is closed even if navigation throws
- **Context lifecycle:** `context.stop()` in the existing `finally` block in `main.py` and `backfill_details.py` shuts down both the context and Playwright instance cleanly
- **Bot challenge retry:** unchanged — same markers, same 3-attempt loop, same backoff

---

## Testing

`tests/test_scraper_config.py` currently asserts `USER_AGENT` from `browser.py`. With Playwright, user-agent is set on the context (not a module constant) so this assertion is removed. The test is updated to assert:
- `SCRAPER_HEADLESS` env var defaults to `"false"`
- `BOT_CHALLENGE_RETRIES == 3`

No browser-integration tests. Parser and loader tests are unaffected.

---

## File Map

| File | Change |
|---|---|
| `scraper/browser.py` | Full rewrite — Playwright persistent context |
| `scraper/main.py` | `create_driver` → `create_context`, `driver` → `context`, `driver.quit()` → `context.stop()` |
| `scraper/backfill_details.py` | Same rename |
| `tests/test_scraper_config.py` | Update USER_AGENT assertion → SCRAPER_HEADLESS + BOT_CHALLENGE_RETRIES |
| `browser_profile/` | New gitignored directory (auto-created by Playwright) |
| `.gitignore` | Add `browser_profile/` |
| `requirements.txt` | Add `playwright`, `playwright-stealth`; remove `undetected-chromedriver`, `setuptools` |

---

## Out of Scope

- CI/GitHub Actions headed browser setup — deprioritized until local scraper is confirmed working
- Async Playwright API — sync API is sufficient for single-threaded scraper
- CAPTCHA solving — persistent context + headed first run handles `cf_clearance`; interactive CAPTCHAs are out of scope
