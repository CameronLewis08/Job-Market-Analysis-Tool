from __future__ import annotations

import os

import psycopg2
from dotenv import load_dotenv

from scraper.browser import create_driver, fetch_page
from scraper.loader import ensure_table, upsert_listing
from scraper.parser import parse_listings

load_dotenv()

WWR_BASE = "https://weworkremotely.com"
CATEGORIES = {
    "programming": "/remote-jobs/categories/2-programming",
    "data-science": "/remote-jobs/categories/19-data-science",
}
MAX_PAGES = 5


def get_connection() -> psycopg2.extensions.connection:
    return psycopg2.connect(os.environ["DATABASE_URL"])


def scrape_category(driver, conn, category: str, slug: str) -> int:
    loaded = 0
    for page in range(1, MAX_PAGES + 1):
        url = f"{WWR_BASE}{slug}?page={page}"
        html = fetch_page(driver, url)
        listings = parse_listings(html, category=category)
        if not listings:
            break
        for listing in listings:
            upsert_listing(conn, listing)
            loaded += 1
    return loaded


def main() -> None:
    conn = get_connection()
    ensure_table(conn)
    driver = create_driver()
    try:
        for category, slug in CATEGORIES.items():
            count = scrape_category(driver, conn, category, slug)
            print(f"{category}: loaded {count} listings")
    finally:
        driver.quit()
        conn.close()


if __name__ == "__main__":
    main()
