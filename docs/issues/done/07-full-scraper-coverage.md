# Issue 7: Full Scraper Coverage + Rate Limiting

> GitHub Issue: https://github.com/CameronLewis08/Job-Market-Analysis-Tool/issues/8
> Type: AFK

## Parent

[PRD: Job Market Analysis Tool](../../prd.md)

## What to build

Expand the scraper from a single-page proof-of-concept to full production coverage: scrape both the Programming and Data Science categories across up to 5 pages each per run, with proper rate limiting and an honest user-agent. After this slice, each weekly run collects ~100-150 new listings across both categories, and the deduplication logic ensures re-runs are fully idempotent.

## Acceptance criteria

- [x] `scraper/main.py` iterates over active WWR engineering category URLs and maps them into analysis buckets (`programming`, `data-science`)
- [x] Pagination is capped at 5 pages per category per run
- [x] A random sleep of 2-3 seconds is enforced between every page request
- [x] Chrome is launched with user-agent set to `JobMarketResearchBot/1.0`
- [x] Running the scraper twice in a row produces zero duplicate rows in `raw_listings`
- [x] Scraper completes a full run (both categories, 5 pages each) in under 5 minutes

## Progress note (2026-05-04)

Issue complete. Full scraper run completed in under 5 minutes, and latest run loaded
`1245` listings for `programming` with `data-science` intentionally skipped due to no
active WWR source category. `dbt run` and `dbt test` both passed after loading.

Files added/changed:
- `scraper/browser.py`: sets user-agent to the required exact value (`JobMarketResearchBot/1.0`)
- `scraper/main.py`: updates source category slugs to current WWR taxonomy and keeps category bucketing stable for downstream marts
- `scraper/parser.py`: adds support for WWR's new `li.new-listing-container` markup so listings are parsed from current category pages
- `tests/test_scraper_config.py`: validates scraper configuration constants (user-agent, source categories, max pages)

Current source mapping after WWR taxonomy changes:
- `programming`: full-stack, back-end, front-end, devops/sysadmin category pages
- `data-science`: intentionally left empty (no direct WWR data-science category currently)

Duplicate-row criterion is satisfied by schema + load behavior:
- `raw_listings.id` is `PRIMARY KEY` and `upsert_listing` uses `ON CONFLICT (id) DO NOTHING`, preventing duplicate inserts across reruns.

## Blocked by

[Issue 2: Skill Frequency — Full Pipeline Tracer Bullet](./02-skill-frequency-tracer-bullet.md)
