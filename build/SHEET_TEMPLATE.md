# New fixtures sheet (table layout)

A parallel version of "WBR Age Grade Fixtures 26/27" where each row is one fixture or session. The app reads it with `parseFixtureTable()` in `src.html`; the old grid sheet keeps working until the switch.

## Tab 1: Fixtures (must be the first tab)
One row per team per date. Header row exactly as below (order doesn't matter, names are case-insensitive).

| Column | What goes in it | Dropdown / format |
|---|---|---|
| Date | The day of the fixture or session | A real date (dd/mm/yyyy or yyyy-mm-dd) |
| Team | The team | Dropdown from the Teams tab |
| Type | What it is | Match, Training, Pre-season, Indoors, Festival, Break, Other |
| Opponent | Opposition name only, e.g. `Morpeth`. Leave blank for training | Free text; no "(A)", "away" or "?" |
| Venue | Where | Home grass, Home AGP, Away (blank for training with no pitch, festivals elsewhere, breaks) |
| Status | How firm it is | Confirmed, Provisional, Requested (blank counts as Confirmed) |
| Competition | League, Cup, Friendly, County... | Optional |
| Car park duty | `Yes` if the team is marshalling the car park that day (the old "CP" column) | Yes / blank |
| Notes | Anything else, e.g. "moved from Sat" | Free text |

Rules the app applies: a bad date or a missing team stops the refresh with a message naming the row; Provisional and Requested rows show as Unconfirmed; Home grass uses the grass pitch and Home AGP the AGP; Away rows never use a pitch.

## Tab 2: Teams
| Team | Group | Pitch share |
|---|---|---|
Group is one of MINIS, JUNIOR BOYS, JUNIOR GIRLS, WOMEN. Pitch share is 1/3, 1/2 or Full. This feeds the Team dropdown. (The app does not read this tab yet; it still uses its built-in shares and works out the group from the team name.)

Current teams: U6, U7, U8, U9, U10, U11, U12 Boys, U13 Boys, U14 Boys, U15 Boys, U16 Boys, Colts, U12 Girls, U14 Girls, U16 Girls, U18 Girls, 1st XV, 2nd XV. Shares: U6–U10 1/3, U11 and U12 1/2, all others Full.

## Optional tab: Seniors (senior men's fixtures)
The senior men's teams (Men's 1st XV, Vikings, Rangers, Vets) are not in the grid sheet, so their home and away fixtures go on a **Seniors** tab in this same sheet. The grid sync never touches it. Use the same columns as the Fixtures tab, plus **Kick-off** and **Group**:

`Date, Team, Type, Opponent, Venue, Status, Competition, Car park duty, Kick-off, Group, Notes`

- Team names: `Men's 1st XV` (not `1st XV`, which is the women's team), `Vikings`, `Rangers`, `Vets`.
- Kick-off as `HH:MM` (e.g. `15:00`). The pitch is held from 60 minutes before to 110 minutes after kick-off (`KO_WINDOW` in `src.html`); the changing room starts when that ends. A match with no Kick-off falls back to the 12:30-15:00 slot.
- Group: `MEN`.
- Home matches take a pitch from the Venue column (Home grass / Home AGP) and book a changing room; Away rows use neither.

## Tab 3: Config
| A | B |
|---|---|
| Sync from grid | ON (or OFF) |
| Last synced | filled in by the sync |

Cell B1 controls `sync_tables.py`: while it is ON the sync rewrites the Fixtures, Teams and Sync notes tabs from the old grid sheet; set it to OFF to cut over. Anything other than ON (including a blank cell) means the sync does nothing. Season dates and the Week A start date can go below these rows later (the app still has them built in).

## Tab 4: Sync notes
Written by the sync: one row per grid cell it had to interpret (Date, Team, Original text, What the sync did). Fix these in the old sheet while the sync is on, or in the Fixtures tab after cutover.

Format the Date column as plain `yyyy-mm-dd` (Format > Number > Custom date and time), because the app reads dates from the sheet's CSV export and the sync writes them in that form.

## Setting it up
1. Create a new Google Sheet with the three tabs above and add data validation (dropdowns) to Team, Type, Venue, Status and Car park duty. Protect the header row and freeze it.
2. Run `python3 migrate_grid.py` (see below) and import `migrated/fixtures.csv` into the Fixtures tab and `migrated/teams.csv` into the Teams tab.
3. Fix the rows the script lists as `CHECK` by hand.
4. Put the new sheet's ID in `SHEET_IDS['table']` in `gsheets.py` and share it with the service account as **Editor** (the old sheets stay Viewer).
5. Protect the Fixtures, Teams and Sync notes tabs ("generated from the old sheet, don't edit") while the sync is on.

## Running the sync and switching over
1. **Parallel:** `python3 sync_tables.py` (add `--dry-run` to preview). Edit only the old grid sheet; the new tabs are rewritten each run. Safety checks: it stops without writing if the grid looks wrong or the row count drops by more than 20%.
2. **Switch the feed:** run the routine with `FIXTURES_FEED=table` (`python3 refresh.py`) so the page is built from the new table. The sync keeps running first.
3. **Cut over:** set Config!B1 to OFF and remove the protection. The table is now edited by hand and nothing overwrites it. Archive the old sheet.
4. **Clean up:** later, delete `parseGrid`, `migrate_grid.py`, `sync_tables.py` and the grid feed.

## Converting the existing grid
`python3 migrate_grid.py [grid.csv] [outdir]` reads the grid sheet's CSV (default `latest.csv`, which `refresh.py` writes) and writes `fixtures.csv` and `teams.csv`. It prints a `CHECK` line for each row it had to interpret: unrecognised venues, opponent names containing "away"/"(A)", training rows with extra text, and rows with no venue that it set to Type "Other".
