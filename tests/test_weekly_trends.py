from __future__ import annotations

import pandas as pd
import pytest

from dashboard.helpers import filter_weekly_trends, top_skills


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "week_start": pd.to_datetime(
                ["2024-01-01", "2024-01-01", "2024-01-08", "2024-01-08", "2024-01-08"]
            ),
            "skill": ["Python", "SQL", "Python", "dbt", "SQL"],
            "skill_category": ["languages", "databases", "languages", "transformation", "databases"],
            "listing_count": [10, 5, 12, 3, 7],
        }
    )


def test_filter_weekly_trends_returns_selected_skills(sample_df):
    result = filter_weekly_trends(sample_df, ["Python", "SQL"])
    assert set(result["skill"].unique()) == {"Python", "SQL"}


def test_filter_weekly_trends_preserves_all_rows_for_matching_skills(sample_df):
    result = filter_weekly_trends(sample_df, ["Python"])
    assert len(result) == 2
    assert list(result["listing_count"]) == [10, 12]


def test_filter_weekly_trends_empty_selection_returns_all(sample_df):
    result = filter_weekly_trends(sample_df, [])
    assert len(result) == len(sample_df)


def test_top_skills_returns_n_skills_by_total_count(sample_df):
    result = top_skills(sample_df, n=2)
    assert result == ["Python", "SQL"]


def test_top_skills_ranks_by_sum_of_listing_count(sample_df):
    result = top_skills(sample_df, n=1)
    assert result == ["Python"]


def test_top_skills_returns_all_when_n_exceeds_available(sample_df):
    result = top_skills(sample_df, n=100)
    assert len(result) == 3
