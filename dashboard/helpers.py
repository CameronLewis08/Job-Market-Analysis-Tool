from __future__ import annotations

import pandas as pd


def filter_weekly_trends(df: pd.DataFrame, skills: list[str]) -> pd.DataFrame:
    if not skills:
        return df
    return df[df["skill"].isin(skills)].reset_index(drop=True)


def top_skills(df: pd.DataFrame, n: int) -> list[str]:
    totals = df.groupby("skill")["listing_count"].sum().nlargest(n)
    return list(totals.index)
