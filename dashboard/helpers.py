from __future__ import annotations

import pandas as pd


def filter_weekly_trends(df: pd.DataFrame, skills: list[str]) -> pd.DataFrame:
    if not skills:
        return df
    return df[df["skill"].isin(skills)].reset_index(drop=True)


def top_skills(df: pd.DataFrame, n: int) -> list[str]:
    totals = df.groupby("skill")["listing_count"].sum().nlargest(n)
    return list(totals.index)


def filter_cooccurrence(df: pd.DataFrame, min_count: int) -> pd.DataFrame:
    return df[df["cooccurrence_count"] >= min_count].reset_index(drop=True)


def build_cooccurrence_matrix(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    pair_values = {}
    skills = sorted(set(df["skill_a"]).union(df["skill_b"]))

    for row in df.itertuples(index=False):
        pair_values[(row.skill_a, row.skill_b)] = row.cooccurrence_count
        pair_values[(row.skill_b, row.skill_a)] = row.cooccurrence_count

    matrix = pd.DataFrame(0, index=skills, columns=skills, dtype=int)

    for (skill_left, skill_right), value in pair_values.items():
        matrix.loc[skill_left, skill_right] = value

    return matrix
