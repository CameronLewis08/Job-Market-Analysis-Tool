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
    try:
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
    finally:
        conn.close()


if __name__ == "__main__":
    main()
