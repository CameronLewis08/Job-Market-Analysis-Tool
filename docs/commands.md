# Common Commands

## Python Environment

**Activate the virtual environment**
```bash
.venv-dbt\Scripts\activate       # Windows
source .venv-dbt/bin/activate    # Linux / macOS
```

**Freeze dependencies after installing a new package**
```bash
pip freeze > requirements.txt
```

**Run the test suite**
```bash
pytest tests/ -v
```

---

## Scraper (local)

**Run the scraper locally**
```bash
python -m scraper.main
```

Requires a `.env` file with `DATABASE_URL` set (see `.env.example`).

---

## dbt

All dbt commands must be run from the `dbt/` directory.

```bash
cd dbt
```

**Install dbt package dependencies**
```bash
dbt deps
```

**Load seed files (skills dictionary)**
```bash
dbt seed
```

**Run all models**
```bash
dbt run
```

**Run a specific model**
```bash
dbt run --select mart_skill_frequency
```

**Run schema tests**
```bash
dbt test
```

**Full pipeline (seed → run → test)**
```bash
dbt seed && dbt run && dbt test
```

**Switch to prod target**
```bash
dbt run --target prod
```

---

## Dashboard (local)

**Run the Streamlit dashboard**
```bash
streamlit run dashboard/app.py
```

Opens at `http://localhost:8501`.

---

## Docker

**Build the image**
```bash
docker build -t job-market-scraper .
```

**Run the scraper**
```bash
docker run --env-file .env job-market-scraper
```

**Run the dashboard**
```bash
docker run --env-file .env -p 8501:8501 job-market-scraper \
  streamlit run dashboard/app.py --server.address=0.0.0.0
```

Opens at `http://localhost:8501`.

**Run dbt inside the container**
```bash
docker run --env-file .env -w /app/dbt job-market-scraper \
  sh -c "dbt seed && dbt run && dbt test"
```

**Tail container logs**
```bash
docker logs -f $(docker ps -lq)
```

**Stop the most recent container**
```bash
docker stop $(docker ps -lq)
```

**Remove all stopped containers**
```bash
docker container prune
```
