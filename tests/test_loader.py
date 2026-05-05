from __future__ import annotations

from unittest.mock import MagicMock

import scraper.loader as loader_module
from scraper.loader import flush, upsert_listing

SAMPLE_LISTING = {
    "id": "acme-senior-engineer-001",
    "title": "Senior Engineer",
    "company": "Acme",
    "category": "programming",
    "date_posted": None,
    "url": "https://weworkremotely.com/remote-jobs/acme-senior-engineer-001",
    "location_restriction": None,
    "salary_raw": None,
    "description_raw": None,
}


def _make_conn() -> MagicMock:
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = MagicMock()
    return conn


def setup_function():
    loader_module._batch.clear()


def test_upsert_listing_appends_to_batch_without_committing():
    conn = _make_conn()
    upsert_listing(conn, SAMPLE_LISTING)
    assert len(loader_module._batch) == 1
    conn.commit.assert_not_called()


def test_flush_executes_batch_and_commits():
    conn = _make_conn()
    mock_cur = conn.cursor.return_value.__enter__.return_value
    loader_module._batch.append(SAMPLE_LISTING)

    count = flush(conn)

    assert count == 1
    mock_cur.executemany.assert_called_once()
    conn.commit.assert_called_once()
    assert loader_module._batch == []


def test_flush_does_nothing_when_batch_is_empty():
    conn = _make_conn()
    count = flush(conn)
    assert count == 0
    conn.commit.assert_not_called()


def test_multiple_listings_flushed_together():
    conn = _make_conn()
    mock_cur = conn.cursor.return_value.__enter__.return_value
    upsert_listing(conn, SAMPLE_LISTING)
    upsert_listing(conn, {**SAMPLE_LISTING, "id": "acme-senior-engineer-002"})

    count = flush(conn)

    assert count == 2
    args = mock_cur.executemany.call_args
    assert len(args[0][1]) == 2
    conn.commit.assert_called_once()
