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
| Changing room | `Yes` if the team needs a changing room (the old "CP") | Yes / blank |
| Notes | Anything else, e.g. "moved from Sat" | Free text |

Rules the app applies: a bad date or a missing team stops the refresh with a message naming the row; Provisional and Requested rows show as Unconfirmed; Home grass uses the grass pitch and Home AGP the AGP; Away rows never use a pitch.

## Tab 2: Teams
| Team | Group | Pitch share |
|---|---|---|
Group is one of MINIS, JUNIOR BOYS, JUNIOR GIRLS, WOMEN. Pitch share is 1/3, 1/2 or Full. This feeds the Team dropdown. (The app does not read this tab yet; it still uses its built-in shares and works out the group from the team name.)

Current teams: U6, U7, U8, U9, U10, U11, U12 Boys, U13 Boys, U14 Boys, U15 Boys, U16 Boys, Colts, U12 Girls, U14 Girls, U16 Girls, U18 Girls, 1st XV, 2nd XV. Shares: U6–U10 1/3, U11 and U12 1/2, all others Full.

## Tab 3: Config
Season start and end, and the Week A start date (the app still has these built in).

## Setting it up
1. Create a new Google Sheet with the three tabs above and add data validation (dropdowns) to Team, Type, Venue, Status and Changing room. Protect the header row and freeze it.
2. Run `python3 migrate_grid.py` (see below) and import `migrated/fixtures.csv` into the Fixtures tab and `migrated/teams.csv` into the Teams tab.
3. Fix the rows the script lists as `CHECK` by hand.
4. Add the new sheet's ID to `SHEET_IDS` in `refresh.py` and share it with the service account. Run the refresh against both sheets and compare the pages before switching over.

## Converting the existing grid
`python3 migrate_grid.py [grid.csv] [outdir]` reads the grid sheet's CSV (default `latest.csv`, which `refresh.py` writes) and writes `fixtures.csv` and `teams.csv`. It prints a `CHECK` line for each row it had to interpret: unrecognised venues, opponent names containing "away"/"(A)", training rows with extra text, and rows with no venue that it set to Type "Other".
