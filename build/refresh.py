#!/usr/bin/env python3
"""Rebuild the pitch planner from the club's Google Sheets.

Usage: python3 refresh.py
Reads  the first tab of each sheet through the Google Drive API, using a service account
       (key JSON in $GOOGLE_SERVICE_ACCOUNT_JSON, or a file path in $GOOGLE_APPLICATION_CREDENTIALS).
       Needs: pip install google-auth requests
Fallback when no service account is configured: latest.b64, bookings.b64 and training.b64
       (base64 text of each sheet's CSV export, saved by hand).
Writes latest.csv, index.html (standalone page) and artifact.html (for the Claude artifact).
Exits non-zero, leaving the previous outputs untouched, if the data fails validation.
"""
import base64, csv, io, json, os, re, sys, datetime, pathlib
here = pathlib.Path(__file__).parent
SHEET_IDS = {
    'latest':   '1Maux72-4AZUgkoHtkJZOQbU7rpPlA3d339fKg8Srffo',  # WBR Age Grade Fixtures 26/27
    'bookings': '1QAic2QwRDZUJHRQ7LHZVqVxrh-IdjqNMpTyos6FMKnE',  # WBR Paddock & Scrum Machine Bookings
    'training': '1J8sPyVbvGTNKMwhkA0R6S07qbQBXOm0LY5cvXeNRxrY',  # WBR Training Schedule
}
creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON', '').strip()
creds_file = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '').strip()
session = None
if creds_json or creds_file:
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import AuthorizedSession
        scopes = ['https://www.googleapis.com/auth/drive.readonly']
        creds = (service_account.Credentials.from_service_account_info(json.loads(creds_json), scopes=scopes)
                 if creds_json else service_account.Credentials.from_service_account_file(creds_file, scopes=scopes))
        session = AuthorizedSession(creds)
    except Exception as e:
        sys.exit(f'FAILED: could not set up the Google service account ({type(e).__name__}: {e})')

def fetch_csv(name):
    """CSV of the first tab of a sheet, via the Drive API export endpoint."""
    url = f'https://www.googleapis.com/drive/v3/files/{SHEET_IDS[name]}/export'
    try:
        r = session.get(url, params={'mimeType': 'text/csv'}, timeout=60)
    except Exception as e:
        sys.exit(f'FAILED: could not reach Google for the {name} sheet ({type(e).__name__}: {e})')
    if r.status_code != 200:
        sys.exit(f'FAILED: Google returned HTTP {r.status_code} for the {name} sheet (is it shared with the service account?)')
    return r.content.decode('utf-8-sig')

def read_b64(name, required=False):
    path = here/f'{name}.b64'
    raw = path.read_text().strip() if path.exists() else ''
    if not raw:
        if required:
            sys.exit(f'FAILED: no service account configured and {path.name} is missing')
        return ''
    try:
        return base64.b64decode(raw, validate=True).decode('utf-8-sig')
    except Exception as e:
        sys.exit(f'FAILED: could not decode {path.name} ({e})')

def load(name, required=False):
    return fetch_csv(name) if session else read_b64(name, required)

text = load('latest', required=True)
rows = list(csv.reader(io.StringIO(text)))
dates = [r for r in rows if r and re.fullmatch(r'\s*\d{1,2}/\d{1,2}\s*', r[0])]
teams = [c for c in rows[1] if c.strip()] if len(rows) > 1 else []
if len(dates) < 20 or len(teams) < 15 or max(len(r) for r in rows) < 50:
    sys.exit(f'FAILED: sheet looks wrong ({len(dates)} date rows, {len(teams)} teams, expected 20+ and 15+)')
if not any('U12' in t for t in teams) or not any(c.strip() in ('HG','HA','AW') for r in dates for c in r):
    sys.exit('FAILED: expected team headers or HG/HA/AW codes are missing')
# optional second input: the paddock & scrum machine bookings sheet (bookings.b64, same base64 CSV export)
bookings_text = load('bookings')
if bookings_text.strip():
    first = bookings_text.splitlines()[0].lower() if bookings_text.strip() else ''
    if not all(k in first for k in ('date','start','end','resource')):
        sys.exit('FAILED: bookings sheet header should include Date, Start, End and Resource')
# optional third input: the weekly training schedule sheet (training.b64)
training_text = load('training')
if training_text.strip():
    first = training_text.splitlines()[0].lower() if training_text.strip() else ''
    if not all(k in first for k in ('day','team','start','end','resource')):
        sys.exit('FAILED: training sheet header should include Day, Team, Start, End and Resource')
src = (here/'src.html').read_text()
stamp = datetime.datetime.now().strftime('%-d %b %H:%M')
crest = here/'crest.jpg'
crest_uri = 'data:image/jpeg;base64,' + base64.b64encode(crest.read_bytes()).decode() if crest.exists() else ''
full = src.replace('/*SAMPLE_CSV*/""', json.dumps(text)).replace('/*SNAPSHOT_DATE*/""', json.dumps(stamp)).replace('/*BOOKINGS_CSV*/""', json.dumps(bookings_text)).replace('/*TRAINING_CSV*/""', json.dumps(training_text)).replace('__CREST__', crest_uri)
(here/'latest.csv').write_text(text)
(here/'index.html').write_text(full)
head = '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
art = full.replace(head, '').replace('</head>\n<body>\n', '').replace('</body>\n</html>\n', '')
assert art != full and art.lstrip().startswith('<title>'), 'artifact wrapper strip failed'
(here/'artifact.html').write_text(art)
nb = max(0, len([l for l in bookings_text.splitlines() if l.strip()]) - 1)
print(f'OK: {len(dates)} fixture dates, {len(teams)} teams, {nb} booking rows, {max(0, len([l for l in training_text.splitlines() if l.strip()]) - 1)} training rows, copied {stamp}')
