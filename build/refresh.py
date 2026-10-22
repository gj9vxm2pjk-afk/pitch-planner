#!/usr/bin/env python3
"""Rebuild the pitch planner from the club's Google Sheets.

Usage: python3 refresh.py
Feed:  FIXTURES_FEED=table (default) reads the table sheet; FIXTURES_FEED=grid reads the old grid sheet.
Reads  the first tab of each sheet through the Google Drive API, using a service account
       (key JSON in $GOOGLE_SERVICE_ACCOUNT_JSON, or a file path in $GOOGLE_APPLICATION_CREDENTIALS).
       Needs: pip install google-auth requests
Fallback when no service account is configured: latest.b64, bookings.b64 and training.b64
       (base64 text of each sheet's CSV export, saved by hand).
Writes latest.csv, index.html (standalone page) and artifact.html (for the Claude artifact).
Exits non-zero, leaving the previous outputs untouched, if the data fails validation.
"""
import base64, csv, io, json, os, re, sys, datetime, pathlib
import gsheets
here = pathlib.Path(__file__).parent
SHEET_IDS = gsheets.SHEET_IDS
# FIXTURES_FEED=table (default) builds the page from the table sheet; FIXTURES_FEED=grid from the old grid sheet.
FEED = os.environ.get('FIXTURES_FEED', 'table').strip().lower()
if FEED not in ('grid', 'table'):
    sys.exit(f'FAILED: FIXTURES_FEED must be "grid" or "table", not "{FEED}"')
if FEED == 'table' and not SHEET_IDS['table']:
    sys.exit('FAILED: FIXTURES_FEED=table but SHEET_IDS["table"] is not set')
session = gsheets.session()

def fetch_csv(name):
    return gsheets.export_csv(session, SHEET_IDS[name], name)

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

if FEED == 'table':
    text = fetch_csv('table') if session else sys.exit('FAILED: FIXTURES_FEED=table needs a service account')
    rows = list(csv.reader(io.StringIO(text)))
    head = [h.strip().lower() for h in rows[0]] if rows else []
    if not all(k in head for k in ('date', 'team', 'type', 'venue')):
        sys.exit('FAILED: the first tab of the table sheet should have Date, Team, Type and Venue columns')
    dates = [r for r in rows[1:] if r and r[0].strip()]
    teams = sorted({r[head.index('team')].strip() for r in dates if len(r) > head.index('team') and r[head.index('team')].strip()})
    if len(dates) < 100 or len(teams) < 15:
        sys.exit(f'FAILED: table looks wrong ({len(dates)} rows, {len(teams)} teams, expected 100+ and 15+)')
else:
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
# optional fourth input: the Seniors tab of the table sheet (senior men's fixtures with kick-off times), read through the Sheets API
seniors_text = ''
if session and SHEET_IDS['table']:
    vals = gsheets.get_values_optional(session, SHEET_IDS['table'], 'Seniors!A:N', 'the Seniors tab')
    if vals and any(any(str(c).strip() for c in row) for row in vals[1:]):
        head = [str(h).strip().lower() for h in vals[0]]
        if not all(k in head for k in ('date', 'team', 'type', 'venue')):
            sys.exit('FAILED: the Seniors tab header should include Date, Team, Type and Venue (and Kick-off)')
        buf = io.StringIO(); csv.writer(buf).writerows(vals); seniors_text = buf.getvalue()
src = (here/'src.html').read_text()
stamp = datetime.datetime.now().strftime('%-d %b %H:%M')
crest = here/'crest.jpg'
crest_uri = 'data:image/jpeg;base64,' + base64.b64encode(crest.read_bytes()).decode() if crest.exists() else ''
full = src.replace('/*SAMPLE_CSV*/""', json.dumps(text)).replace('/*SNAPSHOT_DATE*/""', json.dumps(stamp)).replace('/*BOOKINGS_CSV*/""', json.dumps(bookings_text)).replace('/*SENIORS_CSV*/""', json.dumps(seniors_text)).replace('/*TRAINING_CSV*/""', json.dumps(training_text)).replace('__CREST__', crest_uri)
(here/('latest.csv' if FEED == 'grid' else 'fixtures_table.csv')).write_text(text)
(here/'index.html').write_text(full)
head = '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
art = full.replace(head, '').replace('</head>\n<body>\n', '').replace('</body>\n</html>\n', '')
assert art != full and art.lstrip().startswith('<title>'), 'artifact wrapper strip failed'
(here/'artifact.html').write_text(art)
nb = max(0, len([l for l in bookings_text.splitlines() if l.strip()]) - 1)
print(f'OK ({FEED} feed): {len(dates)} fixture rows, {len(teams)} teams, {nb} booking rows, {max(0, len([l for l in training_text.splitlines() if l.strip()]) - 1)} training rows, {max(0, len(list(csv.reader(io.StringIO(seniors_text)))) - 1) if seniors_text else 0} senior rows, copied {stamp}')
