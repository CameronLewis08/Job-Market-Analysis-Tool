# Follow-Up Tasks

Items surfaced during the backend improvements PR (phase-1) that were out of scope or pre-existing.

---

## High Priority

### Fix `requirements.txt` encoding and missing packages
- File has a UTF-16 BOM — `pip install -r requirements.txt` will fail on CI runners
- Missing packages: `selenium`, `python-dotenv`, `pytest`, `streamlit`
- File appears to have been exported from the dbt venv, not the scraper venv
- **Fix:** Re-export from the correct scraper venv and save as UTF-8

### Add `pytest` step to CI pipeline (`.github/workflows/pipeline.yml`)
- Tests exist but never run in CI — regressions in scraper layer only surface at runtime
- **Fix:** Add a step before "Run scraper":
  ```yaml
  - name: Run tests
    run: pytest tests/ -v
  ```

---

## Medium Priority

### Call `validate_env()` at startup, not at connect time
- Currently called inside `get_connection()` in both `main.py` and `backfill_details.py`
- If `DATABASE_URL` is unset the driver loads and may fetch pages before aborting
- **Fix:** Call `validate_env()` as the first line of `main()` in both entry points, before `create_driver()`

### Escape skill regex metacharacters in `int_listing_skills.sql`
- Skills like `C++`, `C#`, `.NET` contain regex metacharacters that will error or silently mismatch
- **Fix:** Wrap skill with `regexp_replace(s.skill, '([.+*?^${}()|[\]\\])', '\\\1', 'g')` or audit the seed CSV to confirm no metacharacters

---

## Low Priority

### Broaden bot-challenge detection in `browser.py`
- `_looks_like_bot_challenge` requires both `"just a moment..."` AND `"security verification"` simultaneously
- Real challenge pages may show only one phrase depending on challenge type
- **Fix:** Change `and` to `or`

---

## Next Planned Cycle

### Dashboard freshness indicator
- Spec: brainstormed and approved, not yet written
- Add a "Last updated" metric to the Streamlit dashboard so users know if data is stale
