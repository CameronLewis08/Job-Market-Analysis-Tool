from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import psycopg2
import streamlit as st
from dotenv import load_dotenv

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

# ── Tab 2: Salary by Skill (placeholder) ──────────────────────────────────────
with tab2:
    st.header("Salary Ranges by Skill")
    st.info("Salary data is sparse — many listings omit salary. Chart shows only listings with parseable salary.")
    # mart_skill_salary not yet built; placeholder message
    st.caption("Coming in a future release once mart_skill_salary is implemented.")

# ── Tab 3: Hiring by Category ──────────────────────────────────────────────────
with tab3:
    st.header("Hiring Volume by Category")
    st.caption("Coming once mart_industry_hiring is implemented.")

# ── Tab 4: Week-over-Week Trends ──────────────────────────────────────────────
with tab4:
    st.header("Week-over-Week Skill Demand")
    st.caption("Coming once mart_weekly_trends is implemented.")

# ── Tab 5: Skill Co-occurrence ─────────────────────────────────────────────────
with tab5:
    st.header("Skill Co-occurrence Heatmap")
    st.caption("Coming once mart_skill_cooccurrence is implemented.")
