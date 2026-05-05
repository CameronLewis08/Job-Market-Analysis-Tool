from __future__ import annotations

import logging

import pytest

from scraper.log import configure_logging, get_logger, validate_env


def test_get_logger_returns_logger_with_correct_name():
    configure_logging()
    logger = get_logger("scraper.test")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "scraper.test"


def test_validate_env_returns_url_when_set(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host/db")
    url = validate_env()
    assert url == "postgresql://user:pass@host/db"


def test_validate_env_exits_when_missing(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        validate_env()
    assert exc_info.value.code == 1
