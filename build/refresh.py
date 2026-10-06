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
src = (here/'src.html').read_text()
stamp = datetime.datetime.now().strftime('%-d %b %H:%M')
crest = here/'crest.jpg'
crest_uri = 'data:image/jpeg;base64,' + base64.b64encode(crest.read_bytes()).decode() if crest.exists() else ''
full = src.replace('/*SAMPLE_CSV*/""', json.dumps(text)).replace('/*SNAPSHOT_DATE*/""', json.dumps(stamp)).replace('__CREST__', crest_uri)
(here/'latest.csv').write_text(text)
(here/'index.html').write_text(full)
head = '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
art = full.replace(head, '').replace('</head>\n<body>\n', '').replace('</body>\n</html>\n', '')
assert art != full and art.lstrip().startswith('<title>'), 'artifact wrapper strip failed'
(here/'artifact.html').write_text(art)
print(f'OK: {len(dates)} fixture dates, {len(teams)} teams, copied {stamp}')
