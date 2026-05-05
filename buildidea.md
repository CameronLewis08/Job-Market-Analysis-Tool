### Project #9 — Job Market Analysis Tool

**What you build:** A scheduled ETL pipeline that scrapes data engineering job listings from a public job board, cleans and normalizes the records, loads them into PostgreSQL, and models the data with dbt to produce analytical views that answer specific questions: which tools appear most in job descriptions, how salary ranges vary by required skill set, which industries are hiring most, and how demand has shifted week over week. A lightweight Streamlit dashboard surfaces the findings.

**Key skills practiced:**
- Python web scraping with Selenium for JavaScript-rendered pages and BeautifulSoup for parsing
- Text normalization — extracting structured fields (skills, salary, location, seniority) from unstructured job description text
- Scheduled pipeline execution and incremental loading (only scrape new listings, not the full board every run)
- dbt models: staging layer to clean raw listings, intermediate layer to extract and normalize skills, mart layer to answer the analytical questions
- Dashboard development with Streamlit or Plotly to make the findings demo-able
- Ethical and legal scraping: respect robots.txt, avoid ToS violations, do not scrape sites that explicitly prohibit it

**Why it stands out in 2026:** You can scrape the data engineering job market itself and surface which tools employers actually want. This is one of the most compelling interview talking points possible — you did the research, built the tool, have the data, and can show it live. The dbt modeling layer elevates it from a data dump to an analytical product.

**Important:** LinkedIn prohibits scraping in its ToS and actively blocks automated access. Target public job boards that permit scraping (check robots.txt first). Indeed, Glassdoor, and similar sites have varying policies — verify before building.

**Suggested tools:** Python, Selenium, BeautifulSoup, PostgreSQL, dbt Core, Streamlit

---