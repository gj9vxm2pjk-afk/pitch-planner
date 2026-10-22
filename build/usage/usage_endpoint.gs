/**
 * WBR Pitch Planner: anonymous usage counter.
 *
 * What it does: the app sends an event name (for example "visit_phone" or "copy_message"). This script adds 1 to that day's
 * count for that event in a "Usage" tab of the table sheet. No cookie, no ID, no address and no names are stored: only
 * date + event name + a count. It also builds a "Usage summary" tab (last 7 / 30 days, by event).
 *
 * Set up (about 5 minutes, signed in as the sheet owner):
 *  1. Go to https://script.google.com, New project, paste this whole file, Save.
 *  2. Press Run on "setup" and approve the permission prompts (it creates the two tabs).
 *  3. Deploy > New deployment > type "Web app": Execute as "Me", Who has access "Anyone". Press Deploy.
 *  4. Copy the Web app URL (it ends in /exec) and send it to whoever maintains the app, who puts it in CONFIG.USAGE_URL.
 * To stop counting, set CONFIG.USAGE_URL back to '' in the app (or delete the deployment).
 */
const SHEET_ID = '1tyHepQWdOvekFNW3gSeV_8pICxETJMfHZktI7c6tOCY';      // the table sheet
const EVENTS = ['visit_phone', 'visit_desktop', 'tv', 'tab_message', 'copy_message', 'request_change', 'bad_weather', 'search'];
const DAILY_CAP = 2000;                                               // ignore anything beyond this per event per day

function doPost(e) {
  const name = e && e.parameter && e.parameter.e;
  if (EVENTS.indexOf(name) === -1) return ContentService.createTextOutput('ignored');
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const sh = SpreadsheetApp.openById(SHEET_ID).getSheetByName('Usage');
    const day = Utilities.formatDate(new Date(), 'Europe/London', 'yyyy-MM-dd');
    const last = sh.getLastRow();
    const rows = last > 1 ? sh.getRange(2, 1, last - 1, 3).getValues() : [];
    for (let i = rows.length - 1; i >= 0 && i >= rows.length - 40; i--) {      // today's rows are at the bottom
      if (Utilities.formatDate(new Date(rows[i][0]), 'Europe/London', 'yyyy-MM-dd') === day && rows[i][1] === name) {
        if (rows[i][2] < DAILY_CAP) sh.getRange(i + 2, 3).setValue(rows[i][2] + 1);
        return ContentService.createTextOutput('ok');
      }
    }
    sh.appendRow([day, name, 1]);
  } finally { lock.releaseLock(); }
  return ContentService.createTextOutput('ok');
}

function doGet() { return ContentService.createTextOutput('WBR Pitch Planner usage counter'); }

function setup() {
  const ss = SpreadsheetApp.openById(SHEET_ID);
  let usage = ss.getSheetByName('Usage') || ss.insertSheet('Usage');
  if (usage.getLastRow() === 0) usage.getRange(1, 1, 1, 3).setValues([['Date', 'Event', 'Count']]).setFontWeight('bold');
  usage.getRange('A:A').setNumberFormat('yyyy-mm-dd');
  usage.setFrozenRows(1);
  let sum = ss.getSheetByName('Usage summary') || ss.insertSheet('Usage summary');
  sum.clear();
  sum.getRange(1, 1, 1, 4).setValues([['Event', 'Last 7 days', 'Last 30 days', 'All time']]).setFontWeight('bold');
  EVENTS.forEach(function (ev, i) {
    const r = i + 2;
    sum.getRange(r, 1, 1, 4).setFormulas([[ev,
      '=SUMIFS(Usage!$C:$C,Usage!$B:$B,$A' + r + ',Usage!$A:$A,">="&(TODAY()-6))',
      '=SUMIFS(Usage!$C:$C,Usage!$B:$B,$A' + r + ',Usage!$A:$A,">="&(TODAY()-29))',
      '=SUMIFS(Usage!$C:$C,Usage!$B:$B,$A' + r + ')']]);
  });
  const n = EVENTS.length + 3;
  sum.getRange(n, 1).setValue('Visits (phone + desktop)').setFontWeight('bold');
  sum.getRange(n, 2, 1, 3).setFormulas([['=B2+B3', '=C2+C3', '=D2+D3']]);
  sum.getRange(n + 2, 1).setValue('A visit is counted once per browser session. Counts are anonymous and cannot be traced to a person.');
}
