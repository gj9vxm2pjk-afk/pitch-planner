#!/usr/bin/env python3
"""Build the "WBR Pitch Planner: UAT script" Google Sheet.

Usage: python3 make_uat_sheet.py csv OUTDIR        write Tests.csv (create the sheet from it in Google Drive)
       python3 make_uat_sheet.py apply SHEET_ID    add tabs, dropdowns, colours and the summary to that sheet
Needs the service account to be an Editor of the sheet (share it with the service account's email first).
Only reads/writes the UAT sheet you name. Edit uat_tests.py for the tests and TEST_DATA below for the facts testers should see.
"""
import csv, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import gsheets
from uat_tests import TESTS, TM, FC, FT, CA

PERSONAS = [TM, FC, FT, CA]
HEAD = ['ID', 'Persona', 'Area', 'Test (what to do)', 'Expected result', 'Data needed', 'Result', 'Severity', 'Tester', 'Date', 'Notes']
HOWTO = [
 ['WBR Pitch Planner: user acceptance test (UAT) script'], [''],
 ['Purpose', 'Check that the app and its Google Sheets work for the people who use them, before and after launch.'],
 ['App link', '[paste the app link here]  (add #tv for the clubhouse TV view)'],
 ['Who tests what', 'Team managers: tests TM-xx on a phone. Fixtures coordinator / editors: FC-xx. Facilities / TV: FT-xx. Club admin / owner: CA-xx.'],
 ['How to record', 'On the Tests tab, work down your rows. Pick Result (Pass / Fail / Blocked) from the dropdown, add your name and the date, and a note if something is odd. Give each Fail a Severity.'],
 ['Severity', 'Blocker = cannot use the app or a sheet; Major = wrong information shown or lost; Minor = looks odd or is confusing.'],
 ['If something fails', 'Write the test ID and what you saw in Notes, take a screenshot if you can, and tell the fixtures coordinator.'],
 ['Test data', 'Some tests refer to the weekends on the Test data tab. Refresh that tab before each test round.'],
 ['Do not', 'Do not change real fixtures while testing unless the test says so and you change them back. Put TEST in any request you submit.'],
 ['Pre-checked by Claude', 'Smoke test of the live page (no page errors, Plan/Message, phone and dark layouts, TV mode, search, bad weather, request link) and sheet checks: see the Notes column on the rows marked Pre-checked, and the date in build/tests/README.md.'],
]
TEST_DATA = [
 ['Test data (taken from the live sheet when this script was built: refresh before each round)'], [''],
 ['Week', 'What you should see'],
 ['26 Oct-1 Nov (Week B)', 'Day buttons: Tue, Sun. Sunday home sessions: U10 v Morpeth (AGP 09:00), U12 Boys v Blyth (Grass 09:00, car park), U13 Boys v Blaydon (AGP 10:30, car park, Room 3), U15 Boys v Hartlepool (Grass 10:30, Room 1), Colts (AGP 12:30, car park, Room 1), U14 Girls "game request" (Grass 12:30, no changing room), U16 Girls v Tynedale/Gosforth (AGP 12:30, car park, Room 3).'],
 ['', 'Car park marshals Sunday: U12 Boys, U13 Boys, Colts, U16 Girls. Needs attention: "Sun 15:00 no changing room free for U14 Girls" and "1 unconfirmed: U14 Girls (game request)". Paddock: U6 Sunday 09:00; U18 Girls Tuesday 18:55. 4 training sessions on Tuesday.'],
 ['2-8 Nov (Week A)', 'Clean week, no problems. Sunday: U7-U12 Boys training 09:00 on Grass/AGP, U15 Boys v Morpeth (AGP 10:30, car park, Room 1), U14 Girls v Tynedale (AGP 12:30, car park, Room 3), U16 Girls v Egremont (Grass 12:30, Room 1). Marshals: U7, U15 Boys, U14 Girls.'],
 ['9-15 Nov (Week B)', 'Sunday: U7 and U9 v Wallsend/Alnwick (joint fixtures), U14 Boys training 10:30, U16 Boys v Percy Park (AGP 10:30), Colts v Gateshead (Grass 12:30), U16 Girls (AGP 12:30). Marshals: U9, U16 Boys, U16 Girls.'],
 ['Always', 'Sync from grid = OFF. Opposition clubs summary = 37 clubs. Fixtures backup (opponents) tab present.'],
]

def tests_rows(): return [HEAD] + [list(t) + [''] * 5 for t in TESTS]

def write_csv(out):
    out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    with open(out / 'Tests.csv', 'w', newline='', encoding='utf-8') as f: csv.writer(f).writerows(tests_rows())
    print('wrote', out / 'Tests.csv', len(TESTS), 'tests')

def rgb(r, g, b): return {'red': r, 'green': g, 'blue': b}

def apply(sheet_id):
    sess = gsheets.session(write=True)
    if not sess: sys.exit('FAILED: no service account configured')
    ids = gsheets.sheet_ids(sess, sheet_id, 'the UAT sheet')
    first = next(iter(ids))
    reqs = [{'updateSheetProperties': {'properties': {'sheetId': ids[first], 'title': 'Tests', 'gridProperties': {'frozenRowCount': 1}}, 'fields': 'title,gridProperties.frozenRowCount'}}]
    for t in ('How to test', 'Summary', 'Test data'):
        if t not in ids: reqs.append({'addSheet': {'properties': {'title': t}}})
    gsheets.batch_update(sess, sheet_id, reqs, 'the UAT tabs')
    ids = gsheets.sheet_ids(sess, sheet_id, 'the UAT sheet')
    n = len(TESTS) + 1
    gsheets.put_values(sess, sheet_id, 'Tests!A1', tests_rows(), 'the Tests tab')
    gsheets.put_values(sess, sheet_id, "'How to test'!A1", HOWTO, 'the How to test tab')
    gsheets.put_values(sess, sheet_id, "'Test data'!A1", TEST_DATA, 'the Test data tab')
    summ = [['Persona', 'Tests', 'Pass', 'Fail', 'Blocked', 'Not run', '% done']]
    for i, p in enumerate(PERSONAS + ['All'], start=2):
        crit = '' if p == 'All' else f',Tests!$B$2:$B,$A{i}'
        base = lambda extra='': f'COUNTIFS(Tests!$A$2:$A,"<>"{crit}{extra})'
        summ.append([p, '=' + base(), '=' + base(',Tests!$G$2:$G,"Pass"'), '=' + base(',Tests!$G$2:$G,"Fail"'), '=' + base(',Tests!$G$2:$G,"Blocked"'),
                     f'=B{i}-C{i}-D{i}-E{i}', f'=IF(B{i}=0,0,(C{i}+D{i}+E{i})/B{i})'])
    summ += [[], ['Fails by severity', 'Blocker', 'Major', 'Minor'],
             ['', '=COUNTIFS(Tests!$G$2:$G,"Fail",Tests!$H$2:$H,"Blocker")', '=COUNTIFS(Tests!$G$2:$G,"Fail",Tests!$H$2:$H,"Major")', '=COUNTIFS(Tests!$G$2:$G,"Fail",Tests!$H$2:$H,"Minor")']]
    gsheets.put_values(sess, sheet_id, 'Summary!A1', summ, 'the Summary tab')
    # formulas were written RAW above: rewrite as formulas
    _formulas(sess, sheet_id, summ)
    T, S, H, D = ids['Tests'], ids['Summary'], ids['How to test'], ids['Test data']
    def dv(col, values):
        return {'setDataValidation': {'range': {'sheetId': T, 'startRowIndex': 1, 'endRowIndex': n, 'startColumnIndex': col, 'endColumnIndex': col + 1},
                'rule': {'condition': {'type': 'ONE_OF_LIST', 'values': [{'userEnteredValue': v} for v in values]}, 'strict': True, 'showCustomUi': True}}}
    def cf(col, text, color):
        return {'addConditionalFormatRule': {'index': 0, 'rule': {'ranges': [{'sheetId': T, 'startRowIndex': 1, 'endRowIndex': n, 'startColumnIndex': col, 'endColumnIndex': col + 1}],
                'booleanRule': {'condition': {'type': 'TEXT_EQ', 'values': [{'userEnteredValue': text}]}, 'format': {'backgroundColor': color}}}}}
    wrap = {'userEnteredFormat': {'wrapStrategy': 'WRAP', 'verticalAlignment': 'TOP'}}
    def width(sid, c, px): return {'updateDimensionProperties': {'range': {'sheetId': sid, 'dimension': 'COLUMNS', 'startIndex': c, 'endIndex': c + 1}, 'properties': {'pixelSize': px}, 'fields': 'pixelSize'}}
    def bold(sid, r0, r1, c1): return {'repeatCell': {'range': {'sheetId': sid, 'startRowIndex': r0, 'endRowIndex': r1, 'startColumnIndex': 0, 'endColumnIndex': c1}, 'cell': {'userEnteredFormat': {'textFormat': {'bold': True}}}, 'fields': 'userEnteredFormat.textFormat.bold'}}
    reqs = [dv(6, ['Pass', 'Fail', 'Blocked']), dv(7, ['Blocker', 'Major', 'Minor']),
            cf(6, 'Pass', rgb(.78, .92, .78)), cf(6, 'Fail', rgb(.96, .74, .74)), cf(6, 'Blocked', rgb(.99, .9, .65)),
            {'repeatCell': {'range': {'sheetId': T, 'startRowIndex': 0, 'endRowIndex': n, 'startColumnIndex': 0, 'endColumnIndex': 11}, 'cell': wrap, 'fields': 'userEnteredFormat(wrapStrategy,verticalAlignment)'}},
            bold(T, 0, 1, 11), bold(S, 0, 1, 7), bold(H, 0, 1, 1), bold(D, 0, 1, 1),
            {'repeatCell': {'range': {'sheetId': S, 'startRowIndex': 1, 'endRowIndex': 6, 'startColumnIndex': 6, 'endColumnIndex': 7}, 'cell': {'userEnteredFormat': {'numberFormat': {'type': 'PERCENT', 'pattern': '0%'}}}, 'fields': 'userEnteredFormat.numberFormat'}},
            {'repeatCell': {'range': {'sheetId': H, 'startRowIndex': 0, 'endRowIndex': 20, 'startColumnIndex': 0, 'endColumnIndex': 2}, 'cell': wrap, 'fields': 'userEnteredFormat(wrapStrategy,verticalAlignment)'}},
            {'repeatCell': {'range': {'sheetId': D, 'startRowIndex': 0, 'endRowIndex': 20, 'startColumnIndex': 0, 'endColumnIndex': 2}, 'cell': wrap, 'fields': 'userEnteredFormat(wrapStrategy,verticalAlignment)'}},
            width(T, 0, 60), width(T, 1, 150), width(T, 2, 110), width(T, 3, 320), width(T, 4, 360), width(T, 5, 160), width(T, 6, 80), width(T, 7, 80), width(T, 8, 100), width(T, 9, 90), width(T, 10, 220),
            width(S, 0, 210), width(H, 0, 160), width(H, 1, 640), width(D, 0, 170), width(D, 1, 700),
            {'setBasicFilter': {'filter': {'range': {'sheetId': T, 'startRowIndex': 0, 'endRowIndex': n, 'startColumnIndex': 0, 'endColumnIndex': 11}}}}]
    gsheets.batch_update(sess, sheet_id, reqs, 'the UAT formatting')
    print('OK: UAT sheet built with', len(TESTS), 'tests')

def _formulas(sess, sheet_id, rows):
    """Re-write cells that start with '=' so Sheets treats them as formulas (put_values writes RAW text)."""
    from urllib.parse import quote
    r = gsheets._call(sess, 'put', f'{gsheets.SHEETS}/{sheet_id}/values/{quote("Summary!A1", safe="")}', 'the Summary formulas',
                      params={'valueInputOption': 'USER_ENTERED'}, json={'range': 'Summary!A1', 'majorDimension': 'ROWS', 'values': rows})

if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == 'csv': write_csv(a[1])
    elif len(a) == 2 and a[0] == 'apply': apply(a[1])
    else: sys.exit(__doc__)
