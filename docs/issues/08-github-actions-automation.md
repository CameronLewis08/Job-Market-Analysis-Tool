# Issue 8: GitHub Actions Automation

> GitHub Issue: https://github.com/CameronLewis08/Job-Market-Analysis-Tool/issues/9
> Type: HITL (requires GitHub Secrets setup)

## Parent

[PRD: Job Market Analysis Tool](../prd.md)

## What to build

Automate the pipeline with GitHub Actions: a workflow that runs on a weekly cron schedule (and can be triggered manually) that sets up headless Chrome, runs the scraper, then runs dbt seed, dbt run, and dbt test in sequence. After this slice, the pipeline runs without any manual intervention and data quality failures surface as failed workflow runs.

## Acceptance criteria

- [ ] `.github/workflows/pipeline.yml` exists with a `schedule: cron` trigger set to Monday 6am UTC
- [ ] Workflow includes a `workflow_dispatch` trigger for manual runs
- [ ] Workflow runs on `ubuntu-latest`
- [ ] ChromeDriver is installed via `nanasess/setup-chromedriver@v2` action
- [ ] `DATABASE_URL`, `NEON_HOST`, `NEON_DB`, `NEON_USER`, `NEON_PASSWORD` are read from GitHub Secrets
- [ ] Workflow steps run in order: install dependencies -> run scraper -> dbt seed -> dbt run -> dbt test
- [ ] A manual `workflow_dispatch` run completes successfully end-to-end
- [ ] GitHub Secrets are configured in the repository settings (HITL step)

## Blocked by

- [Issue 2: Skill Frequency — Full Pipeline Tracer Bullet](./02-skill-frequency-tracer-bullet.md)
- [Issue 3: Week-over-Week Skill Trends](./03-week-over-week-trends.md)
- [Issue 4: Skill Co-occurrence](./04-skill-cooccurrence.md)
- [Issue 5: Salary Intelligence](./05-salary-intelligence.md)
- [Issue 6: Hiring by Category](./06-hiring-by-category.md)
- [Issue 7: Full Scraper Coverage + Rate Limiting](./07-full-scraper-coverage.md)
