from __future__ import annotations

import pandas as pd

from dashboard.helpers import build_cooccurrence_matrix, filter_cooccurrence


def test_filter_cooccurrence_applies_minimum_threshold():
    df = pd.DataFrame(
        {
            "skill_a": ["Python", "Python", "SQL"],
            "skill_b": ["SQL", "dbt", "dbt"],
            "cooccurrence_count": [5, 1, 3],
        }
    )

    result = filter_cooccurrence(df, min_count=2)

    assert len(result) == 2
    assert set(result["cooccurrence_count"]) == {3, 5}


def test_build_cooccurrence_matrix_creates_symmetric_heatmap_values():
    df = pd.DataFrame(
        {
            "skill_a": ["Python", "Python", "SQL"],
            "skill_b": ["SQL", "dbt", "dbt"],
            "cooccurrence_count": [5, 2, 3],
        }
    )

    matrix = build_cooccurrence_matrix(df)

    assert list(matrix.index) == ["Python", "SQL", "dbt"]
    assert list(matrix.columns) == ["Python", "SQL", "dbt"]
    assert matrix.loc["Python", "SQL"] == 5
    assert matrix.loc["SQL", "Python"] == 5
    assert matrix.loc["Python", "dbt"] == 2
    assert matrix.loc["dbt", "Python"] == 2
    assert matrix.loc["SQL", "dbt"] == 3
    assert matrix.loc["dbt", "SQL"] == 3
