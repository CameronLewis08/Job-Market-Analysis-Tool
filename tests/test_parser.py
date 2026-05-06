import os
from datetime import date, timedelta

import pytest
from scraper.parser import _parse_relative_age_days, _parse_relative_date, parse_job_detail, parse_listings

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


def test_parse_new_listing_markup_returns_expected_fields():
    html = """
    <ul>
      <li class="new-listing-container feature">
        <a class="listing-link--unlocked" href="/remote-jobs/acme-senior-data-engineer">
          <div class="new-listing">
            <div class="new-listing__header">
              <h3 class="new-listing__header__title">
                <span class="new-listing__header__title__text">Senior Data Engineer</span>
              </h3>
              <p class="new-listing__header__icons__date">1d</p>
            </div>
            <p class="new-listing__company-name">Acme Corp</p>
            <p class="new-listing__company-headquarters">Anywhere in the World</p>
            <div class="new-listing__categories">
              <p class="new-listing__categories__category">Full-Time</p>
              <p class="new-listing__categories__category">$100,000 or more USD</p>
            </div>
          </div>
        </a>
      </li>
    </ul>
    """

    listings = parse_listings(html, category="programming")

    assert len(listings) == 1
    listing = listings[0]
    assert listing["id"] == "acme-senior-data-engineer"
    assert listing["title"] == "Senior Data Engineer"
    assert listing["company"] == "Acme Corp"
    assert listing["category"] == "programming"
    assert listing["date_posted"] == (date.today() - timedelta(days=1)).isoformat()
    assert listing["url"] == "https://weworkremotely.com/remote-jobs/acme-senior-data-engineer"
    assert listing["location_restriction"] == "Anywhere in the World"
    assert listing["salary_raw"] == "$100,000 or more USD"


def test_parse_new_listing_skips_jobs_older_than_1_day():
    html = """
    <ul>
      <li class="new-listing-container">
        <a class="listing-link--unlocked" href="/remote-jobs/acme-legacy-role">
          <div class="new-listing">
            <div class="new-listing__header">
              <h3 class="new-listing__header__title">
                <span class="new-listing__header__title__text">Legacy Role</span>
              </h3>
              <p class="new-listing__header__icons__date">15d</p>
            </div>
          </div>
        </a>
      </li>
    </ul>
    """

    listings = parse_listings(html, category="programming")

    assert listings == []


def test_parse_job_detail_extracts_description_and_salary():
    html = """
    <div class="lis-container__job__content__description">
      <p><strong>Compensation and benefits</strong></p>
      <p>Salary: $145K</p>
      <p>Great role details here.</p>
    </div>
    """

    detail = parse_job_detail(html)

    assert detail["description_raw"] is not None
    assert "Compensation and benefits" in detail["description_raw"]
    assert detail["salary_raw"] == "Salary: $145K"


def test_parse_job_detail_extracts_compensation_range_line():
    html = """
    <div class="lis-container__job__content__description">
      <p>Benefits include equity and annual retreat.</p>
      <p>Compensation: USD 120,000 - 150,000 plus bonus.</p>
      <p>Role details here.</p>
    </div>
    """

    detail = parse_job_detail(html)

    assert detail["salary_raw"] == "Compensation: USD 120,000 - 150,000 plus bonus."


def test_parse_job_detail_keeps_full_description_and_extracts_cad_salary_line():
    html = """
    <div class="lis-container__job__content__description">
      <p>We are hiring a full-time Customer Support Representative.</p>
      <p><strong>Compensation:</strong></p>
      <ul><li>Salary: $50,000 CAD</li><li>Vacation: 15 days</li></ul>
    </div>
    """

    detail = parse_job_detail(html)

    assert "We are hiring a full-time Customer Support Representative." in detail["description_raw"]
    assert "Compensation:" in detail["description_raw"]
    assert "Salary: $50,000 CAD" in detail["description_raw"]
    assert detail["salary_raw"] == "Salary: $50,000 CAD"


def test_parse_relative_date_parses_day_and_hour_labels():
    assert _parse_relative_date("4d") is not None
    assert _parse_relative_date("3h") is not None
    assert _parse_relative_date("today") is not None


def test_parse_relative_age_days_parses_recency_labels():
    assert _parse_relative_age_days("12d") == 12
    assert _parse_relative_age_days("3h") == 0
    assert _parse_relative_age_days("today") == 0
    assert _parse_relative_age_days("unknown") is None
