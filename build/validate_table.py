#!/usr/bin/env python3
"""Add data validation to the new table sheet's Fixtures tab.

Usage: python3 validate_table.py            (prints what it would do)
       python3 validate_table.py --apply    (does it)
Dropdowns for Team, Type, Venue, Status and Car park duty; date and session-time checks; highlighting for duplicate Date + Team and
for Match rows with no Opponent; the header row is frozen and protected (warning only, so the sync can still write it).
Run it once: running it again adds the highlight rules and header protection a second time (dropdowns are simply replaced). Needs the service account to be an Editor of the sheet.
"""
import sys
import gsheets

ROWS = 2000                                       # rules cover rows 2..ROWS
TYPES = ['Match', 'Training', 'Pre-season', 'Indoors', 'Festival', 'Break', 'Other']
VENUES = ['Home grass', 'Home AGP', 'Away']
STATUSES = ['Confirmed', 'Provisional', 'Requested']
COL = {'Date': 0, 'Team': 1, 'Type': 2, 'Opponent': 3, 'Venue': 4, 'Status': 5, 'Car park duty': 7, 'Session time': 9}

def rng(sid, col):
    return {'sheetId': sid, 'startRowIndex': 1, 'endRowIndex': ROWS, 'startColumnIndex': col, 'endColumnIndex': col + 1}

def rule(sid, col, condition, strict=True, message=''):
    return {'setDataValidation': {'range': rng(sid, col), 'rule': {'condition': condition, 'strict': strict, 'showCustomUi': True, 'inputMessage': message}}}

def one_of(values): return {'type': 'ONE_OF_LIST', 'values': [{'userEnteredValue': v} for v in values]}

def requests(fixtures_id, teams_id):
    r = [
        rule(fixtures_id, COL['Date'], {'type': 'DATE_IS_VALID'}, message='A date, e.g. 25/10/2026'),
        # Team comes from the Teams tab, column A
        rule(fixtures_id, COL['Team'], {'type': 'ONE_OF_RANGE', 'values': [{'userEnteredValue': "=Teams!$A$2:$A"}]}, message='Pick a team from the list'),
        rule(fixtures_id, COL['Type'], one_of(TYPES)),
        rule(fixtures_id, COL['Venue'], one_of(VENUES), strict=False, message='Leave blank for a break or off-site day'),
        rule(fixtures_id, COL['Status'], one_of(STATUSES), message='Blank counts as Confirmed'),
        rule(fixtures_id, COL['Car park duty'], one_of(['Yes']), message='Yes, or leave blank'),
    ]
    r.append(rule(fixtures_id, COL['Session time'], {'type': 'CUSTOM_FORMULA', 'values': [{'userEnteredValue': '=OR(J2="",REGEXMATCH(TO_TEXT(J2),"^\\d{1,2}[:.]\\d{2}\\s*[-–]\\s*\\d{1,2}[:.]\\d{2}$"))'}]}, message='Start–end, e.g. 09:00–10:30. Clear the cell to use the default.'))
    def cf(formula, red=True):
        return {'addConditionalFormatRule': {'index': 0, 'rule': {
            'ranges': [{'sheetId': fixtures_id, 'startRowIndex': 1, 'endRowIndex': ROWS, 'startColumnIndex': 0, 'endColumnIndex': 10}],
            'booleanRule': {'condition': {'type': 'CUSTOM_FORMULA', 'values': [{'userEnteredValue': formula}]},
                            'format': {'backgroundColor': {'red': 1, 'green': 0.85, 'blue': 0.85}}}}}}
    r += [cf('=AND($A2<>"",COUNTIFS($A$2:$A,$A2,$B$2:$B,$B2,$D$2:$D,$D2)>1)'),     # same date + team + opponent twice
          cf('=AND($C2="Match",$B2<>"",$D2="")')]                                    # a match with no opponent
    r += [{'updateSheetProperties': {'properties': {'sheetId': fixtures_id, 'gridProperties': {'frozenRowCount': 1}}, 'fields': 'gridProperties.frozenRowCount'}},
          {'addProtectedRange': {'protectedRange': {'range': {'sheetId': fixtures_id, 'startRowIndex': 0, 'endRowIndex': 1},
                                                    'description': 'Header row: please do not rename the columns', 'warningOnly': True}}}]
    return r

def main(argv):
    sess = gsheets.session(write=True)
    if not sess: sys.exit('FAILED: no service account configured')
    target = gsheets.SHEET_IDS['table']
    ids = gsheets.sheet_ids(sess, target, 'the table sheet')
    if 'Fixtures' not in ids or 'Teams' not in ids: sys.exit(f'FAILED: the table sheet needs Fixtures and Teams tabs (found {", ".join(ids)})')
    reqs = requests(ids['Fixtures'], ids['Teams'])
    print(f'{len(reqs)} changes: dropdowns on Team, Type, Venue, Status, Car park duty; date and session-time checks; 2 highlight rules; frozen, warning-protected header')
    if '--apply' not in argv: print('Dry run. Add --apply to make the changes.'); return
    gsheets.batch_update(sess, target, reqs, 'the table sheet validation')
    print('OK: validation applied')

if __name__ == '__main__':
    main(sys.argv[1:])
