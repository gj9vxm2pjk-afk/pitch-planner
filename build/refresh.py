#!/usr/bin/env python3
"""Rebuild the pitch planner from a Google Drive CSV export.

Usage: python3 refresh.py
Reads  latest.b64  (the base64 text returned by the Drive download_file_content tool, exportMimeType text/csv)
Writes latest.csv, index.html (standalone page) and artifact.html (for the Claude artifact).
Exits non-zero, leaving the previous outputs untouched, if the data fails validation.
"""
import base64, csv, io, json, re, sys, datetime, pathlib
here = pathlib.Path(__file__).parent
raw = (here/'latest.b64').read_text().strip()
try:
    text = base64.b64decode(raw, validate=True).decode('utf-8-sig')
except Exception as e:
    sys.exit(f'FAILED: could not decode latest.b64 ({e})')
rows = list(csv.reader(io.StringIO(text)))
dates = [r for r in rows if r and re.fullmatch(r'\s*\d{1,2}/\d{1,2}\s*', r[0])]
teams = [c for c in rows[1] if c.strip()] if len(rows) > 1 else []
if len(dates) < 20 or len(teams) < 15 or max(len(r) for r in rows) < 50:
    sys.exit(f'FAILED: sheet looks wrong ({len(dates)} date rows, {len(teams)} teams, expected 20+ and 15+)')
if not any('U12' in t for t in teams) or not any(c.strip() in ('HG','HA','AW') for r in dates for c in r):
    sys.exit('FAILED: expected team headers or HG/HA/AW codes are missing')
# optional second input: the paddock & scrum machine bookings sheet (bookings.b64, same base64 CSV export)
bookings_text = ''
bp = here/'bookings.b64'
if bp.exists() and bp.read_text().strip():
    try:
        bookings_text = base64.b64decode(bp.read_text().strip(), validate=True).decode('utf-8-sig')
    except Exception as e:
        sys.exit(f'FAILED: could not decode bookings.b64 ({e})')
    first = bookings_text.splitlines()[0].lower() if bookings_text.strip() else ''
    if not all(k in first for k in ('date','start','end','resource')):
        sys.exit('FAILED: bookings sheet header should include Date, Start, End and Resource')
# optional third input: the weekly training schedule sheet (training.b64)
training_text = ''
tp = here/'training.b64'
if tp.exists() and tp.read_text().strip():
    try:
        training_text = base64.b64decode(tp.read_text().strip(), validate=True).decode('utf-8-sig')
    except Exception as e:
        sys.exit(f'FAILED: could not decode training.b64 ({e})')
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
