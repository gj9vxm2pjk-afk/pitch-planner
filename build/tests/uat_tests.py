"""The UAT test list: (ID, persona, area, what to do, expected result, data needed).
Edit here, then run make_uat_sheet.py. Expected results use the "Test data" tab (week 26 Oct-1 Nov and week 2-8 Nov 2026);
refresh that data before each round."""
TM, FC, FT, CA = 'Team manager (phone)', 'Fixtures coordinator / editor', 'Facilities / TV', 'Club admin / owner'
LINK = '[the app link]'

TESTS = [
 # --- Team manager, on a phone ---
 ('TM-01', TM, 'First look', f'Open {LINK} on your phone.', 'Page loads in a few seconds. Header shows the crest, "Pitch Planner", "Request a change" and an "Updated" time. No sideways scrolling.', ''),
 ('TM-02', TM, 'First look', 'Look at the top of the screen.', 'You see Plan and Message tabs, a week arrow bar (e.g. 26 Oct-1 Nov), a "Find a team" box and day buttons (Tue, Sun) with a short summary under each.', 'Week 26 Oct-1 Nov'),
 ('TM-03', TM, 'Navigate', 'Tap the right arrow, then the left arrow, then "This week" (appears when you are not on the current week).', 'The week changes each time; "This week" brings you back; the day buttons follow the week.', ''),
 ('TM-04', TM, 'Find my team', 'Type your team (e.g. U13 Boys) in "Find a team".', 'Only your team stays visible on the day; clear the box and everything returns.', 'U13 Boys on Sun 1 Nov'),
 ('TM-05', TM, 'Read the plan', 'Tap Sun 1 Nov. Find your own team.', 'On a phone the plan is a simple list by time slot. Your team shows opponent, pitch (Grass or AGP) and the time slot. You can say where and when you play.', 'Week 26 Oct-1 Nov'),
 ('TM-06', TM, 'Read the plan', 'Look for free pitch space.', 'Free space is shown as "Free: ..." lines in the list (and a light hatch on the desktop grid). You understand it means room for an extra session.', ''),
 ('TM-07', TM, 'Problems', 'Tap the yellow "needs attention" bar.', 'It opens to a short plain-English list (e.g. "Sun 15:00 - no changing room free for U14 Girls" and "1 unconfirmed: U14 Girls"). Tapping again closes it.', 'Week 26 Oct-1 Nov'),
 ('TM-08', TM, 'Car park', 'Check the car park line on Sunday.', '"Car park marshals" lists the teams on duty (U12 Boys, U13 Boys, Colts, U16 Girls) and a small P marks those teams in the list. Women and senior men never appear.', 'Week 26 Oct-1 Nov'),
 ('TM-09', TM, 'Changing rooms', 'Scroll to "Changing rooms".', 'Rooms are stacked as Room 1-4 per time; home teams and their visitors are paired (e.g. Room 1 home, Room 2 visitors). A red "No room free" line appears where there is none.', 'Week 26 Oct-1 Nov'),
 ('TM-10', TM, 'Message', 'Tap Message.', 'A short weekend message with emoji appears (e.g. "🏉 U13 Boys v Blaydon / ⏰ 10:30-12:30 / 🏟 AGP 1 + 2 · 🚪 Room 3 (visitors 4)"). Car park shows only for teams that are on duty. There is no kick-off or referee text.', 'Week 26 Oct-1 Nov'),
 ('TM-11', TM, 'Message', 'Fill in a [gap], edit a line, tap "Copy message", paste it into WhatsApp.', 'Button says Copied; the pasted text matches what you edited. Emoji show correctly.', ''),
 ('TM-12', TM, 'Message', 'Tap Reset.', 'Your edits are removed and the original message returns.', ''),
 ('TM-13', TM, 'Request a change', 'Tap "Request a change" and submit a test request marked TEST.', 'The Google Form opens, lets you choose one or several changes, and shows a thank-you message.', ''),
 ('TM-14', TM, 'Look and feel', 'Turn on dark mode on the phone, then rotate to landscape, then pinch to zoom.', 'Text stays readable (nothing white-on-white); layout adjusts; no part of the page is cut off.', ''),
 ('TM-15', TM, 'Look and feel', 'Reload with poor signal (or airplane mode then back on).', 'The page shows the last loaded data or a clear message; it does not stay blank.', ''),

 # --- Fixtures coordinator / sheet editor ---
 ('FC-01', FC, 'Access', 'Open the table sheet "WBR Fixtures 26/27 (table)" and its Fixtures tab.', 'You can edit. Header row is frozen. Column J is "Session time". There is a Config tab with "Sync from grid" = OFF.', ''),
 ('FC-02', FC, 'Validation', 'In a blank row type a Team that is not in the list (e.g. "U99").', 'The cell is rejected or flagged (red triangle / message).', ''),
 ('FC-03', FC, 'Validation', 'Pick Type, Venue and Status from their dropdowns; try typing "Bananas" in Type.', 'Only Match, Training, Pre-season, Indoors, Festival, Break, Other (Type), Home grass, Home AGP, Away (Venue), Confirmed, Provisional, Requested (Status) are accepted.', ''),
 ('FC-04', FC, 'Validation', 'Type a text value such as "tomorrow" in Date and "abc" in Session time.', 'Both are rejected or flagged with a hint (Date: a real date; Session time: Start-End like 09:00-10:30).', ''),
 ('FC-05', FC, 'Validation', 'Copy a fixture row so Date + Team + Opponent appear twice.', 'Both rows turn red.', ''),
 ('FC-06', FC, 'Validation', 'Set Type to Match and leave Opponent blank.', 'The row turns red.', ''),
 ('FC-07', FC, 'Edit', 'Change an Opponent for a fixture in the week 2-8 Nov (note the old value). Ask the coordinator to refresh.', 'After the next refresh the new opponent shows on the Plan and in the Message. Change it back afterwards.', 'Week 2-8 Nov'),
 ('FC-08', FC, 'Session time', 'Type 10:00-11:30 in Session time for a Sunday home match.', 'After refresh the match occupies 10:00-11:30 on the plan and a clash is flagged if another team is on that pitch at the same time. Clear the cell afterwards.', 'Week 2-8 Nov'),
 ('FC-09', FC, 'Session time', 'Look at Session time on Sunday home sessions.', 'Pre-filled with the club default (minis 09:00-10:30, junior boys 10:30-12:30, others 12:30-15:00). Blank means the app uses the same defaults.', ''),
 ('FC-10', FC, 'Car park', 'Set Car park duty to Yes on a junior team for a Sunday; refresh.', 'That team gets the P marker and appears in "Car park marshals". Setting it on a Women or Men team has no effect.', ''),
 ('FC-11', FC, 'Weather', 'On the app, open a Sunday and tap "Bad weather"; then "Copy link".', 'Grass sessions show as unavailable and the banner explains who needs to move. The link opens with bad weather already on.', ''),
 ('FC-12', FC, 'Message', 'Open the Message tab for the coming weekend and copy it.', 'Contains each home, away and training session with emoji, only the teams on car park duty, no kick-off or referee wording, and the sign-off from CONFIG. Nothing is missing.', ''),
 ('FC-13', FC, 'Requests', 'Open the Requests sheet after a test form submission.', 'The test request is there with Status and Handled by columns; the editors received an email; Status can be set to Done from a dropdown.', 'Submit TM-13 first'),
 ('FC-14', FC, 'Refresh', 'Ask the coordinator to run the refresh (or wait for 06:15 UTC) after a change.', 'The page "Updated" time moves and the change appears. The morning routine succeeded today.', ''),
 ('FC-15', FC, 'Safety', 'Try to rename a header (e.g. Opponent) on the Fixtures tab.', 'A warning appears about the header row; undo it.', ''),
 ('FC-16', FC, 'Safety', 'Ask a developer to run the sync dry run.', 'It says "Sync from grid is OFF: nothing to do". Hand edits are never overwritten.', ''),

 # --- Facilities / TV ---
 ('FT-01', FT, 'TV mode', 'Open the app link followed by #tv on the clubhouse screen.', 'Large text, no search or buttons, the week bar and day buttons are hidden, the page fills the screen.', 'Add #tv to the link'),
 ('FT-02', FT, 'TV mode', 'Leave it for two minutes on a week with a Saturday and Sunday.', 'It cycles through the days that have pitch use. Nothing flickers or goes blank.', ''),
 ('FT-03', FT, 'Pitches', 'Read the Sunday pitch grid from across the room.', 'Grass and AGP columns, time on the left, team and opponent in each block, coloured by age group. A key is shown. A block with a problem would have a red outline and "Over capacity" (none this week).', 'Week 26 Oct-1 Nov'),
 ('FT-04', FT, 'Rooms', 'Look at "Changing rooms" for Sunday.', 'Rooms 1-4 by time; visitors next to the home team; "No room free: U14 Girls" shown in red.', 'Week 26 Oct-1 Nov'),
 ('FT-05', FT, 'Paddock', 'Look at "Paddock & scrum machines" for Sunday.', 'U6 is listed on the Paddock at 09:00. If another team is booked at the same time a red "Clash" appears.', 'Week 26 Oct-1 Nov'),
 ('FT-06', FT, 'Bookings', 'Look at the Tuesday plan.', 'Training sessions on Grass and AGP and the U18 Girls paddock booking at 18:55 appear.', 'Week 26 Oct-1 Nov'),
 ('FT-07', FT, 'Free space', 'Look for hatched blocks on the grid.', 'Free pitch space is shown as a light hatch with its size (whole, half or third).', ''),
 ('FT-08', FT, 'Exit', 'Remove #tv from the address.', 'Normal controls return.', ''),

 # --- Club admin / owner ---
 ('CA-01', CA, 'Access', 'Open Share on each source sheet (fixtures table, bookings, training, requests, usage).', 'Only the named editors can edit; nobody has "Anyone with the link can edit"; the service account is a Viewer on the old grid, bookings and training sheets and an Editor on the table sheet only.', ''),
 ('CA-02', CA, 'Access', 'Open the Requests sheet in a private window as a non-editor.', 'No access.', ''),
 ('CA-03', CA, 'Sync', 'Check Config on the table sheet.', '"Sync from grid" is OFF and stays OFF.', ''),
 ('CA-04', CA, 'Backups', 'Look at the tab list of the table sheet.', 'There is a "Fixtures backup (opponents)" tab; version history is available.', ''),
 ('CA-05', CA, 'Routine', 'Open the daily routine and the repository commit list.', 'A "Refresh fixtures" commit exists for today; the routine has a second email for failure notices.', ''),
 ('CA-06', CA, 'Address', 'Open the club web address on a phone and a laptop.', 'Loads over HTTPS with the club address; the old GitHub Pages address is off or unadvertised.', 'After the domain is set up'),
 ('CA-07', CA, 'Usage', 'Visit the app on a phone and a laptop, copy the message, tap Request a change, then open the Usage summary tab.', 'Counts rise for visit_phone, visit_desktop, copy_message and request_change (once the counter is deployed). Nothing identifies a person.', 'After the counter is deployed'),
 ('CA-08', CA, 'Privacy', 'Read the footer and the page source.', 'Footer says counts are anonymous; no names, emails or phone numbers are visible on the page. With Do Not Track on, no counts are added.', ''),
 ('CA-09', CA, 'Form', 'Open the form settings.', 'Responses go to the Requests sheet only; only editors can see responses.', ''),
 ('CA-10', CA, 'Data quality', 'Open "Opposition clubs (summary)" and the "not a club" list.', '37 clubs listed, Blyton and Creighton fine; non-clubs (COUNTY CUP, FNL, TBC, Tour...) are in the list underneath, not among the clubs.', ''),
 ('CA-11', CA, 'Recovery', 'Ask a developer how to restore yesterday\'s page.', 'Revert the latest "Refresh fixtures" commit on main, or restore from the sheet\'s version history / backup tab.', ''),
 ('CA-12', CA, 'Comms', 'Read the WhatsApp announcement and the editors\' guide.', 'Colleagues know the link, who can edit, how to request changes and the Thursday-noon cut-off.', ''),
]
