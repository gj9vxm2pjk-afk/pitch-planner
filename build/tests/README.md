# Tests

- `uat_tests.py` is the list of user acceptance tests (four personas). `make_uat_sheet.py csv OUT` writes a CSV; `make_uat_sheet.py apply SHEET_ID` builds the "WBR Pitch Planner: UAT script" Google Sheet (tabs How to test, Tests, Summary, Test data; needs the service account as Editor of that sheet). Refresh the `TEST_DATA` text in `make_uat_sheet.py` before each test round.
- `smoke.cjs` is an automatic check of the page in headless Chromium (desktop, phone, dark, TV mode): `NODE_PATH=<playwright location> node build/tests/smoke.cjs [url]`.
- Sheet checks to run by hand before a round: `python3 build/validate_table.py` (dry run), `python3 build/sync_tables.py --dry-run` (must say Sync is OFF), `python3 build/opposition.py` (37 clubs).

Pre-checked by Claude on 2026-10-28: smoke.cjs 20/20 passed on the published page build; sync is OFF; validate_table and opposition dry runs OK.
