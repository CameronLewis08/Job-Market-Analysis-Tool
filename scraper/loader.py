from __future__ import annotations

import psycopg2

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_listings (
    id                   VARCHAR PRIMARY KEY,
    title                VARCHAR NOT NULL,
    company              VARCHAR,
    category             VARCHAR,
    date_posted          DATE,
    url                  VARCHAR,
    location_restriction VARCHAR,
    salary_raw           VARCHAR,
    description_raw      TEXT,
    scraped_at           TIMESTAMP DEFAULT NOW()
);
"""

UPSERT_SQL = """
INSERT INTO raw_listings
    (id, title, company, category, date_posted, url, location_restriction, salary_raw, description_raw)
VALUES
    (%(id)s, %(title)s, %(company)s, %(category)s, %(date_posted)s, %(url)s, %(location_restriction)s, %(salary_raw)s, %(description_raw)s)
ON CONFLICT (id) DO UPDATE SET
    title = COALESCE(EXCLUDED.title, raw_listings.title),
    company = COALESCE(EXCLUDED.company, raw_listings.company),
    category = COALESCE(EXCLUDED.category, raw_listings.category),
    date_posted = COALESCE(EXCLUDED.date_posted, raw_listings.date_posted),
    url = COALESCE(EXCLUDED.url, raw_listings.url),
    location_restriction = COALESCE(EXCLUDED.location_restriction, raw_listings.location_restriction),
    salary_raw = COALESCE(EXCLUDED.salary_raw, raw_listings.salary_raw),
    description_raw = COALESCE(EXCLUDED.description_raw, raw_listings.description_raw),
    scraped_at = NOW();
"""

# Module-level batch. Single-threaded only — do not use with concurrent scrapers.
_batch: list[dict] = []


def ensure_table(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cur:
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()


def upsert_listing(conn: psycopg2.extensions.connection, listing: dict) -> None:
    _batch.append(listing)


def flush(conn: psycopg2.extensions.connection) -> int:
    if not _batch:
        return 0
    batch_copy = _batch[:]
    count = len(batch_copy)
    with conn.cursor() as cur:
        cur.executemany(UPSERT_SQL, batch_copy)
    conn.commit()
    _batch.clear()
    return count
