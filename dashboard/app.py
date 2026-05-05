from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import psycopg2
import streamlit as st
from dotenv import load_dotenv

from dashboard.helpers import (
    build_cooccurrence_matrix,
    filter_cooccurrence,
    filter_weekly_trends,
    top_skills,
)

load_dotenv()

st.set_page_config(page_title="Job Market Intelligence", layout="wide")


@st.cache_resource
def get_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def query(sql: str, params=None) -> pd.DataFrame:
    conn = get_connection()
    return pd.read_sql(sql, conn, params=params)


# Sidebar — global date range filter
st.sidebar.title("Filters")
date_from = st.sidebar.date_input("From", value=pd.Timestamp.now() - pd.Timedelta(days=90))
date_to = st.sidebar.date_input("To", value=pd.Timestamp.now())

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Skill Rankings",
    "Salary by Skill",
    "Hiring by Category",
    "Week-over-Week Trends",
    "Skill Co-occurrence",
])

# ── Tab 1: Skill Rankings ──────────────────────────────────────────────────────
with tab1:
    st.header("Top Skills by Listing Count")
    df = query(
        """
        select skill, skill_category, listing_count
        from mart_skill_frequency
        where last_seen between %(from)s and %(to)s
        order by listing_count desc
        limit 30
        """,
        {"from": date_from, "to": date_to},
    )
    if df.empty:
        st.info("No data in selected date range.")
    else:
        fig = px.bar(
            df,
            x="listing_count",
            y="skill",
            color="skill_category",
            orientation="h",
            labels={"listing_count": "# Listings", "skill": "Skill", "skill_category": "Category"},
            height=700,
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

# ── Tab 2: Salary by Skill ────────────────────────────────────────────────────
with tab2:
    st.header("Salary Ranges by Skill")
    st.info("Salary data is sparse — many listings omit salary. Chart shows only listings with parseable salary.")
    st.caption("Salary values are parsed from raw salary text and aggregated by skill.")
    df_salary = query(
        """
        select skill, skill_category, min_salary, avg_salary, max_salary, coverage_pct
        from mart_skill_salary
        where last_seen between %(from)s and %(to)s
        order by avg_salary desc
        limit 30
        """,
        {"from": date_from, "to": date_to},
    )
    if df_salary.empty:
        st.info("No salary data in selected date range.")
    else:
        coverage = float(df_salary["coverage_pct"].iloc[0])
        st.metric("Data coverage", f"{coverage:.2f}% of listings include salary")
        fig = px.bar(
            df_salary,
            x="avg_salary",
            y="skill",
            color="skill_category",
            orientation="h",
            labels={
                "avg_salary": "Average Salary (USD)",
                "skill": "Skill",
                "skill_category": "Category",
            },
            custom_data=["min_salary", "max_salary"],
            height=700,
        )
        fig.update_traces(
            hovertemplate=(
                "Skill=%{y}<br>"
                "Avg Salary=$%{x:,.0f}<br>"
                "Min Salary=$%{customdata[0]:,.0f}<br>"
                "Max Salary=$%{customdata[1]:,.0f}<extra></extra>"
            )
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

# ── Tab 3: Hiring by Category ──────────────────────────────────────────────────
with tab3:
    st.header("Hiring Volume by Category")
    st.caption("Aggregated weekly category volume across the selected date range.")
    df_hiring = query(
        """
        select category, sum(listing_count) as listing_count
        from mart_industry_hiring
        where week_start between %(from)s and %(to)s
        group by category
        order by listing_count desc
        """,
        {"from": date_from, "to": date_to},
    )
    if df_hiring.empty:
        st.info("No data in selected date range.")
    else:
        fig = px.bar(
            df_hiring,
            x="category",
            y="listing_count",
            labels={"category": "Category", "listing_count": "# Listings"},
            height=500,
        )
        st.plotly_chart(fig, use_container_width=True)

# ── Tab 4: Week-over-Week Trends ──────────────────────────────────────────────
with tab4:
    st.header("Week-over-Week Skill Demand")
    df_trends = query(
        """
        select week_start, skill, skill_category, listing_count
        from mart_weekly_trends
        where week_start between %(from)s and %(to)s
        order by week_start
        """,
        {"from": date_from, "to": date_to},
    )
    if df_trends.empty:
        st.info("No data in selected date range.")
    else:
        default_skills = top_skills(df_trends, n=5)
        selected_skills = st.multiselect(
            "Skills to compare",
            options=sorted(df_trends["skill"].unique()),
            default=default_skills,
        )
        df_chart = filter_weekly_trends(df_trends, selected_skills)
        if df_chart.empty:
            st.info("Select at least one skill above.")
        else:
            fig = px.line(
                df_chart,
                x="week_start",
                y="listing_count",
                color="skill",
                labels={
                    "week_start": "Week",
                    "listing_count": "# Listings",
                    "skill": "Skill",
                },
                height=500,
            )
            fig.update_layout(xaxis_title="Week (Monday)", yaxis_title="Listing Count")
            st.plotly_chart(fig, use_container_width=True)

# ── Tab 5: Skill Co-occurrence ─────────────────────────────────────────────────
with tab5:
    st.header("Skill Co-occurrence Heatmap")
    df_cooccurrence = query(
        """
        select skill_a, skill_b, cooccurrence_count
        from mart_skill_cooccurrence
        order by cooccurrence_count desc, skill_a, skill_b
        """
    )
    if df_cooccurrence.empty:
        st.info("No co-occurrence data available.")
    else:
        min_available = int(df_cooccurrence["cooccurrence_count"].min())
        max_available = int(df_cooccurrence["cooccurrence_count"].max())
        min_threshold = st.slider(
            "Minimum co-occurrence count",
            min_value=min_available,
            max_value=max_available,
            value=max(min_available, 2),
            step=1,
        )
        df_filtered = filter_cooccurrence(df_cooccurrence, min_threshold)
        if df_filtered.empty:
            st.info("No skill pairs match the selected threshold.")
        else:
            matrix = build_cooccurrence_matrix(df_filtered)
            fig = px.imshow(
                matrix,
                labels={"x": "Skill", "y": "Skill", "color": "Co-occurrence Count"},
                color_continuous_scale="Blues",
                aspect="auto",
            )
            fig.update_layout(xaxis_title="Skill", yaxis_title="Skill", height=700)
            st.plotly_chart(fig, use_container_width=True)
