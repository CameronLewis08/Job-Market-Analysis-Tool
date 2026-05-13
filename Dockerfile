# Python 3.12 slim base matches the version requirements.txt was frozen against.
FROM python:3.12-slim-bookworm

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium, its OS-level dependencies, and xvfb (virtual display for headed mode)
RUN playwright install-deps chromium && playwright install chromium \
    && apt-get install -y --no-install-recommends xvfb xauth \
    && rm -rf /var/lib/apt/lists/*

COPY scraper/ scraper/
COPY dbt/ dbt/
COPY dashboard/ dashboard/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV SCRAPER_HEADLESS=false
ENV DISPLAY=:99
ENV STREAMLIT_SERVER_HEADLESS=true

# Start Xvfb as a background process, wait for it to be ready, then run the scraper
CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp & sleep 2 && python -m scraper.main"]
