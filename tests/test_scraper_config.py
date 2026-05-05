from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _literal_from_assignment(file_path: Path, variable_name: str):
    module = ast.parse(file_path.read_text(encoding="utf-8"))
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == variable_name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"{variable_name} not found in {file_path}")


def test_scraper_user_agent_matches_issue_requirement():
    user_agent = _literal_from_assignment(ROOT / "scraper" / "browser.py", "USER_AGENT")
    assert user_agent == "JobMarketResearchBot/1.0"


def test_scraper_targets_programming_and_data_science():
    category_sources = _literal_from_assignment(ROOT / "scraper" / "main.py", "CATEGORY_SOURCES")
    assert category_sources == {
        "programming": [
            "/categories/remote-full-stack-programming-jobs",
            "/categories/remote-back-end-programming-jobs",
            "/categories/remote-front-end-programming-jobs",
            "/categories/remote-devops-sysadmin-jobs",
        ],
        "data-science": [],
    }


def test_scraper_max_pages_capped_at_five():
    max_pages = _literal_from_assignment(ROOT / "scraper" / "main.py", "MAX_PAGES")
    assert max_pages == 5
