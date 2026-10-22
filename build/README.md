# Build files for the Weekend Pitch Planner

`refresh.py` rebuilds the page from the club's Google Sheets (fixtures, paddock & scrum machine bookings, weekly training). It reads the first tab of each sheet through the Google Drive API using a service account, so the sheets stay private.

## Run it

1. `pip install google-auth requests`
2. Provide the service account key in the environment: `GOOGLE_SERVICE_ACCOUNT_JSON` (the key's JSON), `GOOGLE_SERVICE_ACCOUNT_JSON_B64` (the same JSON base64-encoded, for settings boxes that only take one plain `KEY=value` line), or `GOOGLE_APPLICATION_CREDENTIALS` (path to the key file). To make the base64 form: `base64 -i key.json | tr -d '\n'` on Mac/Linux, or `[Convert]::ToBase64String([IO.File]::ReadAllBytes("key.json"))` in PowerShell.
3. `python3 refresh.py` validates the data and writes `build/index.html`.
4. Copy `build/index.html` to the repo root as `index.html` and commit it. Cloudflare and GitHub Pages publish from the root.

If the run fails, it exits non-zero and leaves the previous outputs untouched.

## One-off setup

- In Google Cloud, create a project, enable the **Google Drive API**, create a **service account** and download its JSON key. Keep the key out of the repo; store it as a secret in the routine's environment.
- Share each sheet with the service account's email address as **Viewer** (each owner does their own):
  - WBR Age Grade Fixtures 26/27 (`SHEET_IDS['latest']`)
  - WBR Paddock & Scrum Machine Bookings (`SHEET_IDS['bookings']`)
  - WBR Training Schedule (`SHEET_IDS['training']`)
- Allow outbound access to `www.googleapis.com` and `oauth2.googleapis.com` in the environment's network settings.

The sheet IDs are in `SHEET_IDS` at the top of `refresh.py`.

## Table-format sheet and the grid sync
`sync_tables.py` copies the old grid sheet into the new one-row-per-fixture sheet; `FIXTURES_FEED=table python3 refresh.py` builds the page from it. See `SHEET_TEMPLATE.md` for the sheet layout and the cutover steps. `gsheets.py` holds the sheet IDs and the Google access code shared by both scripts. Sync needs the service account to have write access (Editor) to the new sheet only.

## Manual fallback

With no service account configured, `refresh.py` reads `latest.b64`, `bookings.b64` and `training.b64` (base64 text of each sheet's first tab as CSV, e.g. from the Drive `download_file_content` tool). Retyping a long base64 string is error-prone, so use this only by hand, not for the scheduled run.

`latest.b64`, `bookings.b64`, `training.b64`, `latest.csv`, `index.html` and `artifact.html` in this folder are git-ignored.
