# Issue 7: Full Scraper Coverage + Rate Limiting

> GitHub Issue: https://github.com/CameronLewis08/Job-Market-Analysis-Tool/issues/8
> Type: AFK

## Parent

[PRD: Job Market Analysis Tool](../prd.md)

## What to build

Expand the scraper from a single-page proof-of-concept to full production coverage: scrape both the Programming and Data Science categories across up to 5 pages each per run, with proper rate limiting and an honest user-agent. After this slice, each weekly run collects ~100-150 new listings across both categories, and the deduplication logic ensures re-runs are fully idempotent.

## Acceptance criteria

- [ ] `scraper/main.py` iterates over both Programming and Data Science category URLs
- [ ] Pagination is capped at 5 pages per category per run
- [ ] A random sleep of 2-3 seconds is enforced between every page request
- [ ] Chrome is launched with user-agent set to `JobMarketResearchBot/1.0`
- [ ] Running the scraper twice in a row produces zero duplicate rows in `raw_listings`
- [ ] Scraper completes a full run (both categories, 5 pages each) in under 5 minutes

## Blocked by

[Issue 2: Skill Frequency — Full Pipeline Tracer Bullet](./02-skill-frequency-tracer-bullet.md)
