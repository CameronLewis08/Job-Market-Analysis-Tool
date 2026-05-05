from __future__ import annotations

import random
import time

import setuptools  # noqa: F401 — keeps distutils importable on Python 3.12
import undetected_chromedriver as uc

from scraper.log import get_logger

logger = get_logger(__name__)

USER_AGENT = "JobMarketResearchBot/1.0"
BOT_CHALLENGE_RETRIES = 3


def create_driver() -> uc.Chrome:
    options = uc.ChromeOptions()
    options.add_argument(f"--user-agent={USER_AGENT}")
    logger.debug("Creating undetected Chrome driver")
    return uc.Chrome(options=options)


def fetch_page(driver: uc.Chrome, url: str) -> str:
    last_source = ""
    for attempt in range(BOT_CHALLENGE_RETRIES):
        driver.get(url)
        _polite_delay()
        page_source = driver.page_source
        last_source = page_source
        if not _looks_like_bot_challenge(page_source):
            return page_source
        logger.warning(
            "Bot challenge detected on %s (attempt %d/%d)",
            url, attempt + 1, BOT_CHALLENGE_RETRIES,
        )
        if attempt < BOT_CHALLENGE_RETRIES - 1:
            time.sleep(4)
    logger.error("All %d attempts failed for %s — returning last page source", BOT_CHALLENGE_RETRIES, url)
    return last_source


def _polite_delay() -> None:
    time.sleep(random.uniform(2.0, 3.0))


def _looks_like_bot_challenge(html: str) -> bool:
    lower = html.lower()
    return "just a moment..." in lower or "security verification" in lower
