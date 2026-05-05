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
