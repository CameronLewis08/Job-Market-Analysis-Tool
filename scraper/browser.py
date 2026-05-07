from __future__ import annotations

import os
import random
import time

from playwright.sync_api import BrowserContext, sync_playwright
from playwright_stealth import Stealth

from scraper.log import get_logger

logger = get_logger(__name__)

BOT_CHALLENGE_RETRIES = int(os.getenv("BOT_CHALLENGE_RETRIES", "3"))
_PROFILE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "browser_profile")
os.makedirs(_PROFILE_DIR, exist_ok=True)


def create_context() -> BrowserContext:
    headless = os.getenv("SCRAPER_HEADLESS", "false").lower() == "true"
    pw = sync_playwright().start()
    try:
        context = pw.chromium.launch_persistent_context(
            user_data_dir=_PROFILE_DIR,
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
        )
    except Exception:
        pw.stop()
        raise

    def _stop() -> None:
        context.close()
        pw.stop()

    context.stop = _stop  # patch stop() so callers use context.stop() for full cleanup
    logger.debug("Created persistent browser context (headless=%s, profile=%s)", headless, _PROFILE_DIR)
    return context


def fetch_page(context: BrowserContext, url: str) -> str:
    last_source = ""
    for attempt in range(BOT_CHALLENGE_RETRIES):
        page = context.new_page()
        try:
            Stealth().apply_stealth_sync(page)
            page.goto(url, wait_until="load", timeout=30000)
            _polite_delay()
            _human_scroll(page)
            page_source = page.content()
            last_source = page_source
            if not _looks_like_bot_challenge(page_source):
                return page_source
        finally:
            page.close()
        logger.warning(
            "Bot challenge detected on %s (attempt %d/%d)",
            url, attempt + 1, BOT_CHALLENGE_RETRIES,
        )
        if attempt < BOT_CHALLENGE_RETRIES - 1:
            time.sleep(random.uniform(6.0, 12.0))
    logger.error("All %d attempts failed for %s — returning last page source", BOT_CHALLENGE_RETRIES, url)
    return last_source


def _polite_delay() -> None:
    time.sleep(random.uniform(1.5, 3.0))


def _human_scroll(page) -> None:
    try:
        page.evaluate("window.scrollTo(0, 400)")
        time.sleep(random.uniform(0.1, 0.2))
        page.evaluate("window.scrollTo(0, 800)")
        time.sleep(random.uniform(0.1, 0.2))
        page.evaluate("window.scrollTo(0, 0)")
    except Exception:
        pass


def _looks_like_bot_challenge(html: str) -> bool:
    lower = html.lower()
    markers = [
        "just a moment",
        "security verification",
        "checking your browser",
        "enable javascript",
        "cf-browser-verification",
        "challenge-platform",
        "ray id",
    ]
    return any(m in lower for m in markers)
