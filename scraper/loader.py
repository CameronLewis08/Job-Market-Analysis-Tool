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
ON CONFLICT (id) DO NOTHING;
"""


def ensure_table(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cur:
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()


def upsert_listing(conn: psycopg2.extensions.connection, listing: dict) -> None:
    with conn.cursor() as cur:
        cur.execute(UPSERT_SQL, listing)
    conn.commit()
