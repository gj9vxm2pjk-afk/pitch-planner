#!/usr/bin/env python3
"""Convert the current grid-style fixtures sheet into the tidy table format (one row per fixture or session).

Usage: python3 migrate_grid.py [grid.csv] [outdir]
  grid.csv  CSV of the first tab of the grid sheet (default: latest.csv, which refresh.py writes)
  outdir    where to write fixtures.csv and teams.csv (default: migrated/)

fixtures.csv columns: Date, Team, Type, Opponent, Venue, Status, Competition, Changing room, Notes
Import fixtures.csv into the first tab of the new sheet and teams.csv into the second (File > Import).
Rows the script had to interpret are listed on stdout so they can be checked by hand.
"""
import csv, datetime, pathlib, re, sys

SEASON_START = datetime.date(2026, 8, 2)
VENUE = {'HG': 'Home grass', 'HA': 'Home AGP', 'AW': 'Away'}
SESSION_RE = re.compile(r'^\??\s*(pre-?season|training|indoors|joint training)', re.I)
BREAK_RE = re.compile(r'christmas|easter|half.?term|^bye$', re.I)
is_date = lambda v: re.fullmatch(r'\s*\d{1,2}/\d{1,2}\s*', v or '') is not None

def clean_team(t):
    return re.sub(r'^(U\d+)s$', r'\1', re.sub(r'\s+', ' ', t).strip(), flags=re.I)

def group_key(g):
    u = g.upper()
    return 'MINIS' if 'MINI' in u else 'JUNIOR BOYS' if 'BOYS' in u else 'JUNIOR GIRLS' if 'GIRLS' in u else 'WOMEN'

def parse_blocks(rows, first):
    g_row, t_row = rows[first - 2], rows[first - 1]
    width = max(len(r) for r in rows)
    blocks, group, last = [], '', ''
    for c in range(1, width):
        g = (g_row[c] if c < len(g_row) else '').strip()
        t = (t_row[c] if c < len(t_row) else '').strip()
        if g: group = g
        if t and t != last:
            blocks.append({'team': clean_team(t), 'group': group_key(group), 'cols': [c]}); last = t
        elif blocks:
            blocks[-1]['cols'].append(c)
    return blocks

def migrate(rows):
    first = next((i for i, r in enumerate(rows) if is_date(r[0] if r else '')), -1)
    if first < 2: sys.exit('FAILED: could not find the team headers or dates')
    blocks = parse_blocks(rows, first)
    cell = lambda r, c: (r[c] if c is not None and c < len(r) else '').strip()
    out, notes = [], []
    for r in rows[first:]:
        if not is_date(r[0] if r else ''): continue
        d, m = (int(x) for x in r[0].strip().split('/'))
        date = datetime.date(SEASON_START.year + (1 if m < SEASON_START.month else 0), m, d)
        for b in blocks:
            act = cell(r, b['cols'][0])
            vr = cell(r, b['cols'][1] if len(b['cols']) > 1 else None).upper()
            venue = vr if vr in VENUE else ''
            cp = len(b['cols']) > 2 and cell(r, b['cols'][2]).lower() == 'cp'
            extra = ' · '.join(v for v in (cell(r, c) for c in b['cols'][3:]) if v and not re.match(r'HG\s*=', v, re.I))
            if not act and not venue: continue
            note = []
            if vr and not venue:
                note.append(f'venue in old sheet was "{vr}"'); notes.append((date, b['team'], act, f'unrecognised venue "{vr}"'))
            status = 'Confirmed'
            if '?' in act:
                status = 'Provisional'
            if SESSION_RE.match(act):
                typ = 'Pre-season' if re.match(r'\??\s*pre-?season', act, re.I) else 'Indoors' if re.match(r'indoors', act, re.I) else 'Training'
                opp = ''
                if not re.fullmatch(r'\??\s*(pre-?season|training|indoors)\??\s*', act, re.I):
                    opp = act.replace('?', '').strip(); notes.append((date, b['team'], act, 'training row had extra text, kept as Opponent'))
            elif BREAK_RE.search(act):
                typ, opp = 'Break', act
            elif re.search(r'fest', act, re.I):
                typ, opp = 'Festival', act.replace('?', '').strip()
            elif not venue:
                typ, opp = 'Other', act.replace('?', '').strip(); notes.append((date, b['team'], act, 'no venue, set to Type "Other"'))
            else:
                typ, opp = 'Match', re.sub(r'\s+', ' ', act.replace('?', '')).strip()
            if re.search(r'\(A\)|\baway\b|\(H\)|\bhome\b', opp, re.I):
                notes.append((date, b['team'], act, 'opponent name contains home/away text, check it'))
            out.append([date.isoformat(), b['team'], typ, opp, VENUE.get(venue, ''), status, extra, 'Yes' if cp else '', '; '.join(note)])
    return out, blocks, notes

def main():
    here = pathlib.Path(__file__).parent
    src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else here / 'latest.csv'
    outdir = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else here / 'migrated'
    rows = list(csv.reader(open(src, newline='', encoding='utf-8-sig')))
    out, blocks, notes = migrate(rows)
    outdir.mkdir(parents=True, exist_ok=True)
    head = ['Date', 'Team', 'Type', 'Opponent', 'Venue', 'Status', 'Competition', 'Changing room', 'Notes']
    out.sort(key=lambda x: (x[0], [b['team'] for b in blocks].index(x[1])))
    with open(outdir / 'fixtures.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(head); w.writerows(out)
    shares = {'U6': '1/3', 'U7': '1/3', 'U8': '1/3', 'U9': '1/3', 'U10': '1/3', 'U11': '1/2', 'U12 Boys': '1/2', 'U12 Girls': '1/2'}
    with open(outdir / 'teams.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['Team', 'Group', 'Pitch share'])
        for b in blocks: w.writerow([b['team'], b['group'], shares.get(b['team'], 'Full')])
    for d, team, act, why in notes: print(f'CHECK {d} {team}: "{act}" ({why})')
    print(f'OK: {len(out)} rows for {len(blocks)} teams written to {outdir}/')

if __name__ == '__main__':
    main()
