#!/usr/bin/env python3
"""Copy the old grid fixtures sheet into the new table-format sheet.

Usage: python3 sync_tables.py [--dry-run]
Reads  the first tab of the old grid sheet, converts it with migrate_grid.migrate(), and rewrites the values in the
       new sheet's Fixtures, Teams and Sync notes tabs. Dropdowns, protection and formatting are left alone.
Only runs while the new sheet's Config tab has  "Sync from grid" = ON  (cells A1:B1). Set it to OFF to cut over:
       after that the new sheet is maintained by hand and this script never touches it again.
Writes "Last synced" to Config!B2. Aborts without writing if the grid looks wrong or the row count drops by more than 20%.
Needs a service account with Editor access to the new sheet (see gsheets.py).
"""
import csv, datetime, io, sys
import gsheets, migrate_grid

HEAD = ['Date', 'Team', 'Type', 'Opponent', 'Venue', 'Status', 'Competition', 'Car park duty', 'Notes']
MAX_DROP = 0.2

def pad(rows, n):
    return [[str(c) for c in r] + [''] * (n - len(r)) for r in rows]

def write_tab(sess, sheet_id, tab, values, width, label):
    """Write values from A1, then clear whatever is left below (so a failure never leaves a half-empty tab)."""
    last = chr(ord('A') + width - 1)
    gsheets.put_values(sess, sheet_id, f'{tab}!A1', values, label)
    gsheets.clear_values(sess, sheet_id, f'{tab}!A{len(values) + 1}:{last}', label)

def main(argv):
    dry = '--dry-run' in argv
    sess = gsheets.session(write=True)
    if not sess: sys.exit('FAILED: no service account configured')
    target = gsheets.SHEET_IDS['table']
    if not target: sys.exit('FAILED: gsheets.SHEET_IDS["table"] is not set')
    cfg = gsheets.get_values(sess, target, 'Config!A1:B10', 'the table sheet Config tab')
    flag = next((r[1] for r in cfg if len(r) > 1 and r[0].strip().lower() == 'sync from grid'), '')
    if flag.strip().upper() != 'ON':
        print(f'Sync from grid is "{flag.strip() or "not set"}", not ON: nothing to do'); return

    rows = list(csv.reader(io.StringIO(gsheets.export_csv(sess, gsheets.SHEET_IDS['latest'], 'grid'))))
    problem = migrate_grid.check_grid(rows)
    if problem: sys.exit(f'FAILED: {problem}; the table sheet was not changed')
    out, blocks, notes = migrate_grid.migrate(rows)
    fixtures = [HEAD] + out
    teams = [['Team', 'Group', 'Pitch share']] + migrate_grid.team_rows(blocks)
    sync_notes = [['Date', 'Team', 'Original text', 'What the sync did']] + [[d.isoformat(), t, a, w] for d, t, a, w in notes]

    current = gsheets.get_values(sess, target, 'Fixtures!A1:I', 'the current Fixtures tab')
    old_n = max(0, len(current) - 1)
    if old_n and len(out) < old_n * (1 - MAX_DROP):
        sys.exit(f'FAILED: the grid gives {len(out)} rows but the table has {old_n}; not overwriting (check the grid sheet)')
    if pad(current, 9) == pad(fixtures, 9):
        print(f'Unchanged: {len(out)} rows, {len(blocks)} teams'); return
    print(f'{"Would write" if dry else "Writing"} {len(out)} fixture rows (was {old_n}), {len(blocks)} teams, {len(notes)} notes')
    if dry: return
    write_tab(sess, target, 'Fixtures', fixtures, 9, 'the Fixtures tab')
    write_tab(sess, target, 'Teams', teams, 3, 'the Teams tab')
    write_tab(sess, target, 'Sync notes', sync_notes, 4, 'the Sync notes tab')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%-d %b %Y %H:%M UTC')
    gsheets.put_values(sess, target, 'Config!A2:B2', [['Last synced', f'{stamp}, {len(out)} rows']], 'the Config tab')
    print(f'OK: synced {len(out)} rows for {len(blocks)} teams')

if __name__ == '__main__':
    main(sys.argv[1:])
