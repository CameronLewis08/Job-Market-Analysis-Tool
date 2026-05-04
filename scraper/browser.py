from __future__ import annotations

import random
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

USER_AGENT = "JobMarketResearchBot/1.0 (educational project; contact: camdam827@gmail.com)"


def create_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--user-agent={USER_AGENT}")
    return webdriver.Chrome(options=options)


def fetch_page(driver: webdriver.Chrome, url: str) -> str:
    driver.get(url)
    _polite_delay()
    return driver.page_source


def _polite_delay() -> None:
    time.sleep(random.uniform(2.0, 3.0))
