from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Optional

from bs4 import BeautifulSoup

WWR_BASE = "https://weworkremotely.com"
MAX_LISTING_AGE_DAYS = 14
COMPENSATION_LINE_PATTERN = re.compile(
    r"(salary|compensation|pay\s*range|base\s*pay|base\s*salary|ote|on[-\s]*target)",
    flags=re.IGNORECASE,
)
MONEY_PATTERN = re.compile(
    r"(?:\$|USD\s*)[\d,]+(?:\.\d+)?(?:\s*[kK])?(?:\s*-\s*(?:\$|USD\s*)?[\d,]+(?:\.\d+)?(?:\s*[kK])?)?",
    flags=re.IGNORECASE,
)


def parse_listings(html: str, category: str) -> list[dict]:
    """Parse a WWR category index page and return one dict per listing."""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    legacy_articles = soup.select("article.job")
    if legacy_articles:
        for article in legacy_articles:
            listing = _parse_article(article, category)
            if listing:
                results.append(listing)
        return results

    for container in soup.select("li.new-listing-container"):
        listing = _parse_new_listing(container, category)
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


def _parse_new_listing(container, category: str) -> Optional[dict]:
    link_tag = container.select_one("a.listing-link--unlocked[href*='/remote-jobs/']")
    if not link_tag:
        return None

    href = link_tag.get("href", "")
    if not href or "/remote-jobs/" not in href:
        return None

    url = WWR_BASE + href
    listing_id = href.rstrip("/").rsplit("/", 1)[-1]

    title_tag = container.select_one(".new-listing__header__title__text")
    title = title_tag.get_text(strip=True) if title_tag else None
    if not title:
        fallback_title = container.select_one("h3.new-listing__header__title")
        title = fallback_title.get_text(" ", strip=True) if fallback_title else None
    if not title:
        return None

    company_tag = container.select_one(".new-listing__company-name")
    company = company_tag.get_text(" ", strip=True) if company_tag else None

    region_tag = container.select_one(".new-listing__company-headquarters")
    location_restriction = region_tag.get_text(" ", strip=True) if region_tag else None

    salary_raw = None
    for category_tag in container.select(".new-listing__categories__category"):
        category_text = category_tag.get_text(" ", strip=True)
        if "$" in category_text or "USD" in category_text:
            salary_raw = category_text
            break

    relative_date_tag = container.select_one(".new-listing__header__icons__date")
    relative_date = relative_date_tag.get_text(" ", strip=True) if relative_date_tag else None
    age_days = _parse_relative_age_days(relative_date)
    if age_days is None or age_days > MAX_LISTING_AGE_DAYS:
        return None
    date_posted = _parse_relative_date(relative_date)

    return {
        "id": listing_id,
        "title": title,
        "company": company,
        "category": category,
        "date_posted": date_posted,
        "url": url,
        "location_restriction": location_restriction,
        "salary_raw": salary_raw,
        "description_raw": None,
    }


def parse_job_detail(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    description_container = soup.select_one(".lis-container__job__content__description")
    description_raw = None
    if description_container:
        text_parts = list(description_container.stripped_strings)
        description_raw = "\n".join(text_parts) if text_parts else None

    salary_raw = _extract_salary_text(description_raw)

    date_posted = None
    time_tag = soup.select_one("time[datetime]")
    if time_tag:
        date_posted = time_tag.get("datetime")

    return {
        "date_posted": date_posted,
        "salary_raw": salary_raw,
        "description_raw": description_raw,
    }


def _parse_relative_date(label: Optional[str]) -> Optional[str]:
    if not label:
        return None

    value = label.strip().lower()
    if value.endswith("d"):
        days = value[:-1]
        if days.isdigit():
            return (date.today() - timedelta(days=int(days))).isoformat()
    if value.endswith("h") and value[:-1].isdigit():
        return date.today().isoformat()
    if value in {"today", "just now"}:
        return date.today().isoformat()
    return None


def _parse_relative_age_days(label: Optional[str]) -> Optional[int]:
    if not label:
        return None

    value = label.strip().lower()
    if value.endswith("d"):
        days = value[:-1]
        if days.isdigit():
            return int(days)
        return None
    if value.endswith("h") and value[:-1].isdigit():
        return 0
    if value in {"today", "just now"}:
        return 0
    return None


def _extract_salary_text(description_raw: Optional[str]) -> Optional[str]:
    if not description_raw:
        return None

    lines = [line.strip() for line in description_raw.splitlines() if line.strip()]

    for line in lines:
        if COMPENSATION_LINE_PATTERN.search(line):
            money_match = MONEY_PATTERN.search(line)
            if money_match:
                return line

    money_match = MONEY_PATTERN.search(description_raw)
    if money_match:
        return money_match.group(0).strip()

    return None
