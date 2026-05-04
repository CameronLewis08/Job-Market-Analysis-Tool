import os
import pytest
from scraper.parser import parse_listings

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "..", "scraper", "fixtures", "wwr_programming_page1.html")


@pytest.fixture
def fixture_html():
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return f.read()


def test_parse_returns_correct_count(fixture_html):
    listings = parse_listings(fixture_html, category="programming")
    assert len(listings) == 3


def test_parse_first_listing_fields(fixture_html):
    listings = parse_listings(fixture_html, category="programming")
    first = listings[0]

    assert first["id"] == "acme-corp-senior-data-engineer-12345"
    assert first["title"] == "Senior Data Engineer"
    assert first["company"] == "Acme Corp"
    assert first["category"] == "programming"
    assert first["date_posted"] == "2024-03-15"
    assert first["url"] == "https://weworkremotely.com/remote-jobs/programming/acme-corp-senior-data-engineer-12345"
    assert first["location_restriction"] == "USA Only"


def test_parse_listing_has_required_keys(fixture_html):
    listings = parse_listings(fixture_html, category="programming")
    required_keys = {"id", "title", "company", "category", "date_posted", "url", "location_restriction", "salary_raw", "description_raw"}
    for listing in listings:
        assert required_keys == set(listing.keys())


def test_parse_html_entities_decoded(fixture_html):
    listings = parse_listings(fixture_html, category="programming")
    second = listings[1]
    assert "&amp;" not in second["title"]
    assert second["title"] == "Data Engineer - Airflow & Spark"


def test_parse_salary_raw_is_none_when_absent(fixture_html):
    listings = parse_listings(fixture_html, category="programming")
    for listing in listings:
        assert listing["salary_raw"] is None


def test_parse_description_raw_is_none_from_index_page(fixture_html):
    listings = parse_listings(fixture_html, category="programming")
    for listing in listings:
        assert listing["description_raw"] is None
