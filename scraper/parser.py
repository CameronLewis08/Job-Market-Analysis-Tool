from __future__ import annotations

from typing import Optional
from bs4 import BeautifulSoup

WWR_BASE = "https://weworkremotely.com"


def parse_listings(html: str, category: str) -> list[dict]:
    """Parse a WWR category index page and return one dict per listing."""
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for article in soup.select("article.job"):
        listing = _parse_article(article, category)
        if listing:
            results.append(listing)

    return results


def _parse_article(article, category: str) -> Optional[dict]:
    title_tag = article.select_one("a.title")
    if not title_tag:
        return None

    href = title_tag.get("href", "")
    url = WWR_BASE + href
    listing_id = href.rstrip("/").rsplit("/", 1)[-1]
    title = title_tag.get_text(strip=True)

    company_tag = article.select_one("li.company span")
    company = company_tag.get_text(strip=True) if company_tag else None

    region_tag = article.select_one("li.region")
    location_restriction = region_tag.get_text(strip=True) if region_tag else None

    time_tag = article.select_one("time")
    date_posted = time_tag.get("datetime") if time_tag else None

    return {
        "id": listing_id,
        "title": title,
        "company": company,
        "category": category,
        "date_posted": date_posted,
        "url": url,
        "location_restriction": location_restriction,
        "salary_raw": None,
        "description_raw": None,
    }
