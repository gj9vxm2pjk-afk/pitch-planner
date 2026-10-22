#!/usr/bin/env python3
"""Tidy the Opponent column (D) of the table sheet's Fixtures tab, changing only what is certain.

Usage: python3 clean_opponents.py            (dry run: lists every change and every cell left alone)
       python3 clean_opponents.py --apply    (backs up Fixtures to a new tab, then writes column D and column I only)
Rules are in opponents.py (tidy). A tag such as (A), (H), away, home or @ ground is removed only when it agrees with the Venue
column, and is copied into Notes (column I) first. Joint fixtures, other brackets, events, TBC and anything doubtful stay as they are.
"""
import sys
import gsheets
from opponents import tidy

BACKUP = 'Fixtures backup (opponents)'

def plan(rows):
    """[(sheet row number, old opponent, new opponent, old notes, new notes)] for the cells that change."""
    out = []
    for n, r in enumerate(rows[1:], start=2):
        r = (r + [''] * 10)[:10]
        new_opp, new_notes = tidy(r[3], r[4], r[8])
        if new_opp != r[3] or new_notes != r[8]: out.append((n, r[3], new_opp, r[8], new_notes))
    return out

def main(argv):
    sess = gsheets.session(write='--apply' in argv)
    if not sess: sys.exit('FAILED: no service account configured')
    target = gsheets.SHEET_IDS['table']
    rows = gsheets.get_values(sess, target, 'Fixtures!A1:J2000', 'the Fixtures tab')
    if not rows or rows[0][:5] != ['Date', 'Team', 'Type', 'Opponent', 'Venue']: sys.exit('FAILED: the Fixtures tab does not look right; nothing changed')
    changes = plan(rows)
    filled = sum(1 for r in rows[1:] if len(r) > 3 and r[3].strip())
    print(f'{filled} opponents filled in; {len(changes)} would change, {filled - len(changes)} stay as they are')
    for n, old, new, on, nn in changes: print(f'  row {n}: {old!r} -> {new!r}' + (f'   notes: {on!r} -> {nn!r}' if nn != on else ''))
    if '--apply' not in argv: print('Dry run. Add --apply to back up and write.'); return
    ids = gsheets.sheet_ids(sess, target, 'the table sheet')
    if BACKUP in ids: sys.exit(f'FAILED: "{BACKUP}" already exists; rename or delete it first so the earlier backup is not overwritten')
    gsheets.batch_update(sess, target, [{'addSheet': {'properties': {'title': BACKUP}}}], 'backup tab')
    gsheets.put_values(sess, target, f'{BACKUP}!A1', [[str(c) for c in (r + [''] * 10)[:10]] for r in rows], 'the backup')
    data = []
    for n, _, new, _, nn in changes:
        data += [(f'Fixtures!D{n}', [[new]]), (f'Fixtures!I{n}', [[nn]])]
    gsheets.batch_put(sess, target, data, 'the cleaned opponents')
    print(f'OK: backed up to "{BACKUP}" and updated {len(changes)} rows (columns D and I only)')

if __name__ == '__main__':
    main(sys.argv[1:])
