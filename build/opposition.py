#!/usr/bin/env python3
"""List the clubs we play, from the Opponent column of the table sheet's Fixtures tab.

Usage: python3 opposition.py            (dry run: prints counts and the first rows)
       python3 opposition.py --apply    (writes the two tabs below; creates them if missing)
Writes only "Opposition clubs" (one row per club and age group) and "Opposition clubs (summary)" (one row per club, with a
"not a club / to check" list underneath). Nothing else in the sheet is touched. This is the thin version: it knows only
the clubs we have fixtures against. County, league and the clubs we never play are to be added later (the County column is blank).
Edit ALIAS (spelling variants) and NOT_CLUB (labels that are not clubs) below when a name comes out wrong, then run again.
"""
import collections, re, sys
import gsheets
from opponents import clean_parts, SUSPECT

LONG, SUMMARY = 'Opposition clubs', 'Opposition clubs (summary)'
SOURCE = 'WBR fixtures 26/27'

def side(team):
    return 'Girls' if 'girls' in team.lower() else 'Boys' if re.search(r'boys|colts', team.lower()) else 'Mixed'

def build(rows):
    seen = collections.defaultdict(lambda: collections.defaultdict(list))   # club -> team -> [dates]
    raws, joint, check = collections.defaultdict(set), collections.defaultdict(int), []
    for r in rows:
        r = (r + [''] * 4)[:4]
        date, team, typ, opp = [c.strip() for c in r]
        if not opp or typ.lower() not in ('match', 'other'): continue
        names, why = clean_parts(opp)
        if why or not names:
            check.append([opp, team, date, why or 'no club name found']); continue
        for n in names:
            seen[n][team].append(date); raws[n].add(opp)
            if len(names) > 1: joint[n] += 1
    return seen, raws, joint, check

AGE = lambda team: (int(m.group(1)) if (m := re.match(r'U\s?(\d+)', team, re.I)) else 99, team)

def tables(seen, raws, joint, check):
    long_ = [['Club', 'Age group', 'Boys/Girls', 'Fixtures', 'First date', 'Last date', 'Source', 'Confidence']]
    summ = [['Club', 'County / area', 'Age groups seen', 'Fixtures', 'Spellings seen', 'Confidence', 'Notes']]
    for club in sorted(seen, key=str.lower):
        teams = seen[club]; total = sum(len(d) for d in teams.values())
        for team in sorted(teams, key=AGE):
            d = sorted(x for x in teams[team] if x)
            long_.append([club, team, side(team), len(teams[team]), d[0] if d else '', d[-1] if d else '', SOURCE, 'listed only'])
        notes = []
        if total == 1: notes.append('seen once: check the spelling')
        if club in SUSPECT: notes.append(SUSPECT[club])
        if joint[club]: notes.append(f'{joint[club]} joint fixture(s)')
        summ.append([club, '', ', '.join(sorted(teams, key=AGE)), total, ' | '.join(sorted(raws[club])), 'listed only', '; '.join(notes)])
    summ += [[], ['Not a club / to check', 'Team', 'Date', 'Why']] + sorted(check, key=lambda c: c[0].lower())
    return long_, summ

def main(argv):
    sess = gsheets.session(write='--apply' in argv)
    if not sess: sys.exit('FAILED: no service account configured')
    target = gsheets.SHEET_IDS['table']
    rows = gsheets.get_values(sess, target, 'Fixtures!A2:D2000', 'the Fixtures tab')
    rows = [r for r in rows if r]
    seen, raws, joint, check = build(rows)
    long_, summ = tables(seen, raws, joint, check)
    print(f'{len(seen)} clubs, {len(long_) - 1} club/age-group rows, {len(check)} not-a-club or to-check entries')
    for r in summ[:21]: print('  ', r[:4], r[6] if len(r) > 6 else '')
    if '--apply' not in argv: print('Dry run. Add --apply to write the two tabs.'); return
    ids = gsheets.sheet_ids(sess, target, 'the table sheet')
    add = [{'addSheet': {'properties': {'title': t}}} for t in (LONG, SUMMARY) if t not in ids]
    if add: gsheets.batch_update(sess, target, add, 'new opposition tabs')
    for tab, vals, width in ((LONG, long_, 8), (SUMMARY, summ, 7)):
        gsheets.clear_values(sess, target, f'{tab}!A1:H', tab)
        gsheets.put_values(sess, target, f'{tab}!A1', [r + [''] * (width - len(r)) for r in vals], tab)
    print('OK: wrote', LONG, 'and', SUMMARY)

if __name__ == '__main__':
    main(sys.argv[1:])
