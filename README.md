# Job Market Analysis Tool

A weekly ETL pipeline that scrapes data engineering job listings from We Work Remotely, transforms them with dbt, and surfaces the results in a Streamlit dashboard. Answers questions like: which tools are employers actually asking for, how has demand shifted week over week, and which skills cluster together in job descriptions.

## What it does

- **Scrapes** the Programming and Data Science categories on We Work Remotely every Monday at 6am UTC
- **Loads** raw listings into PostgreSQL on Neon (idempotent — duplicates are skipped)
- **Transforms** with dbt into 5 analytical mart tables
- **Visualizes** in a Streamlit dashboard with 5 tabs: Skill Rankings, Salary by Skill, Hiring by Category, Week-over-Week Trends, and Skill Co-occurrence

## Stack

| Layer | Technology |
|---|---|
| Scraper | Python, Playwright, BeautifulSoup |
| Database | PostgreSQL (Neon) |
| Transformation | dbt |
| Dashboard | Streamlit |
| CI/CD | GitHub Actions |

## Project structure

```
scraper/        # Playwright browser, HTML parser, Postgres loader, orchestration
dbt/            # Staging, intermediate, and mart models + skills seed
dashboard/      # Streamlit app
tests/          # pytest tests for scraper modules
.github/
  workflows/
    pipeline.yml  # Weekly cron + manual dispatch
```

## Local setup

**Prerequisites:** Python 3.11+, a Neon account

1. Clone the repo and create a virtual environment:
   ```
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   source .venv/bin/activate   # Mac/Linux
   pip install -r requirements.txt
   playwright install chromium
   ```

2. Copy `.env.example` to `.env` and fill in your Neon credentials:
   ```
   DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
   NEON_HOST=your-project.us-east-2.aws.neon.tech
   NEON_DB=neondb
   NEON_USER=neondb_owner
   NEON_PASSWORD=your_password_here
   SCRAPER_HEADLESS=false
   ```

3. Run the scraper:
   ```
   python -m scraper.main
   ```

4. Run dbt transforms:
   ```
   cd dbt
   dbt deps
   dbt seed
   dbt run
   dbt test
   ```

5. Launch the dashboard:
   ```
   streamlit run dashboard/app.py
   ```

## Running tests

```
pytest tests/ -v
```

## CI/CD

The GitHub Actions workflow (`.github/workflows/pipeline.yml`) runs automatically every Monday at 6am UTC and can also be triggered manually from the Actions tab.

**Required GitHub Secrets (Repository secrets, not Environment secrets):**
- `DATABASE_URL`
- `NEON_HOST`
- `NEON_DB`
- `NEON_USER`
- `NEON_PASSWORD`

The workflow installs Playwright, runs tests, then runs the scraper under `xvfb-run` (virtual display to avoid headless bot detection), followed by dbt seed, run, and test.

## Extending the skills list

Add rows to `dbt/seeds/skills.csv` with a `skill` name and a `category` (language, orchestration, warehouse, cloud, infrastructure, transformation, storage, visualization, library). Run `dbt seed` to reload. No code changes needed.

## Configuration

| Environment variable | Default | Description |
|---|---|---|
| `SCRAPER_HEADLESS` | `false` | Run browser in headless mode |
| `BOT_CHALLENGE_RETRIES` | `3` | Retry attempts per page on bot challenge |
| `SCRAPER_MIN_DELAY` | `1.5` | Min seconds between page requests |
| `SCRAPER_MAX_DELAY` | `3.0` | Max seconds between page requests |
