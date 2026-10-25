/**
 * WBR Pitch Planner: request, modify or cancel a session.
 *
 * Coaches and managers start from the Pitch Planner page. "Request change" on a session opens this form with the team, date,
 * venue and session time already filled in (see REQUEST_ENTRIES in build/src.html), so they only pick what they want to do, add a
 * note and give their name. The request is emailed to the leader of that team's group (Minis, Junior Boys or Junior Girls) and
 * copied to the coordinator. Women's and senior teams are not part of this yet.
 *
 * The Team dropdown comes from the Teams tab of the club's table sheet. Type, venue and session time use the same fixed values as
 * the sheet's own dropdowns (validate_table.py).
 *
 * Set up (about 5 minutes), signed in as the club coordinator, who must be able to open the table sheet and edit the form:
 *  1. Go to https://script.google.com and press New project.
 *  2. Delete the sample code, paste this whole file, press Save.
 *  3. Fill in LEADERS and COORDINATOR below.
 *  4. Press Run > refreshForm. Approve the permission prompts. This replaces the form's questions and keeps its link.
 *  5. Open View > Logs. It prints REQUEST_ENTRIES: paste that line into CONFIG in build/src.html so the page can pre-fill the form.
 *  6. Press Run > installRouting. This adds the Group, Leader, Status columns to the responses sheet and the email trigger.
 *  7. Press Run > installWeeklyRefresh so the Team dropdown follows the sheet.
 *
 * To start a new form instead, leave FORM_ID blank and run createForms (then steps 5-7).
 */
const FORM_ID = '1MjbGzPncwrqyAV2JlS5-YBzRgY5ufTX3pJraBa495HY';   // existing form to update; leave blank for createForms to make a new one
const TABLE_SHEET_ID = '1tyHepQWdOvekFNW3gSeV_8pICxETJMfHZktI7c6tOCY';   // WBR Fixtures 26/27 (table)
const COORDINATOR = 'coordinator@example.com';          // <-- copied on every request; also receives any group with no leader set
const LEADERS = {                                        // <-- who gets requests for each group
  'MINIS':        { name: 'Minis leader',         email: '' },
  'JUNIOR BOYS':  { name: 'Junior Boys leader',   email: '' },
  'JUNIOR GIRLS': { name: 'Junior Girls leader',  email: '' }
};
const GROUPS = Object.keys(LEADERS);                    // only these groups appear in the form

// Same values as the sheet's dropdowns (validate_table.py)
const ACTIONS = ['Modify this session', 'Cancel this session', 'Request a new session'];
const TYPES = ['Match', 'Training', 'Pre-season', 'Indoors', 'Festival', 'Other'];
const VENUES = ['Home grass', 'Home AGP', 'Away'];
const SESSION_TIMES = ['09:00–10:30', '10:30–12:30', '12:30–15:00'];

const T = {                                              // question titles (the page's REQUEST_ENTRIES map to these)
  name: 'Your name', team: 'Team', action: 'What do you want to do?', date: 'Date of the session',
  time: 'Session time', venue: 'Venue', type: 'Type', opp: 'Opponent', note: 'What should change, or any other detail?'
};

function createForms() {
  const form = FormApp.create('WBR Pitch Planner: request, modify or cancel a session');
  buildQuestions(form);
  const ss = SpreadsheetApp.create('WBR Pitch Planner: session requests');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());
  SpreadsheetApp.flush();
  PropertiesService.getScriptProperties().setProperty('FORM_ID', form.getId());
  Logger.log('Share this link: ' + form.getPublishedUrl());
  Logger.log('Edit the form: ' + form.getEditUrl());
  Logger.log('Responses sheet: ' + ss.getUrl());
  Logger.log('Now run installRouting and installWeeklyRefresh.');
}

/** Replaces the form's questions with ones built from today's sheet. Keeps the link and the responses. */
function refreshForm() {
  const form = openForm();
  buildQuestions(form);
  Logger.log('Form refreshed: ' + form.getPublishedUrl());
}

/** Adds Group, Leader, Status, Handled by to the responses sheet and the email trigger (safe to run again). */
function installRouting() {
  const form = openForm();
  if (!form.getDestinationId()) throw new Error('The form has no responses sheet. In the form: Responses > Link to Sheets.');
  const ss = SpreadsheetApp.openById(form.getDestinationId());
  const sheet = responsesSheet(ss);
  const head = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  ['Group', 'Leader', 'Status', 'Handled by'].forEach(function (h) {
    if (head.indexOf(h) < 0) { sheet.getRange(1, sheet.getLastColumn() + 1).setValue(h).setFontWeight('bold'); }
  });
  const statusCol = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0].indexOf('Status') + 1;
  sheet.getRange(2, statusCol, 500, 1).setDataValidation(
    SpreadsheetApp.newDataValidation().requireValueInList(['New', 'Approved', 'Done', 'Rejected'], true).build());
  sheet.setFrozenRows(1);
  PropertiesService.getScriptProperties().setProperty('SHEET_ID', ss.getId());
  ScriptApp.getProjectTriggers().filter(function (t) { return t.getHandlerFunction() === 'routeRequest'; })
    .forEach(function (t) { ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('routeRequest').forSpreadsheet(ss).onFormSubmit().create();
  [COORDINATOR].concat(GROUPS.map(function (g) { return LEADERS[g].email; })).filter(String)
    .forEach(function (e) { try { ss.addEditor(e); } catch (x) {} });
  Logger.log('Routing installed. Responses sheet: ' + ss.getUrl());
}

/** Runs refreshForm every Monday morning so new teams appear. */
function installWeeklyRefresh() {
  ScriptApp.getProjectTriggers().filter(function (t) { return t.getHandlerFunction() === 'refreshForm'; })
    .forEach(function (t) { ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('refreshForm').timeBased().onWeekDay(ScriptApp.WeekDay.MONDAY).atHour(6).create();
}

function openForm() {
  const id = FORM_ID || PropertiesService.getScriptProperties().getProperty('FORM_ID');
  if (!id) throw new Error('Set FORM_ID at the top of the script, or run createForms first.');
  return FormApp.openById(id);
}

function responsesSheet(ss) {
  return ss.getSheets().filter(function (s) { return /Form responses/.test(s.getName()); })[0] || ss.getSheets()[0];
}

function buildQuestions(form) {
  const teamGroup = readTeams();
  const teams = Object.keys(teamGroup);
  form.getItems().forEach(function (item) { form.deleteItem(item); });
  form.setCollectEmail(false).setProgressBar(false).setShowLinkToRespondAgain(false);
  form.setTitle('WBR Pitch Planner: change a session');
  form.setDescription('Opened from a session in the Pitch Planner? Most of this is filled in already. Check it, say what you want to do, ' +
    'and send. Your group leader and the coordinator get the request. Please send changes by Thursday noon for the weekend; ' +
    'for anything urgent, message your group leader directly.');
  form.setConfirmationMessage('Thanks. Your group leader and the coordinator have the request and will come back to you.');

  const ids = {};
  ids.name = form.addTextItem().setTitle(T.name).setRequired(true).getId();
  ids.team = form.addListItem().setTitle(T.team).setChoiceValues(teams).setRequired(true).getId();
  ids.action = form.addMultipleChoiceItem().setTitle(T.action).setChoiceValues(ACTIONS).setRequired(true).getId();
  ids.date = form.addDateItem().setTitle(T.date).setHelpText('For a new session, the date you would like.').setRequired(true).getId();
  ids.time = form.addListItem().setTitle(T.time).setChoiceValues(SESSION_TIMES).getId();
  ids.venue = form.addListItem().setTitle(T.venue).setChoiceValues(VENUES).getId();
  ids.type = form.addListItem().setTitle(T.type).setChoiceValues(TYPES).setHelpText('Needed for a new session.').getId();
  ids.opp = form.addTextItem().setTitle(T.opp).setHelpText('Matches only.').getId();
  ids.note = form.addParagraphTextItem().setTitle(T.note).setHelpText('For example: move to 10:30–12:30 on the AGP. Say why if you can.').getId();

  // Paste this line into CONFIG in build/src.html: the page uses it to pre-fill the form
  Logger.log('REQUEST_ENTRIES: ' + JSON.stringify(ids));
  Logger.log('Teams offered: ' + teams.length + ' (' + GROUPS.join(', ') + ')');
}

/** Team -> group for the groups that use this form, read from the Teams tab (columns Team, Group). */
function readTeams() {
  const tab = SpreadsheetApp.openById(TABLE_SHEET_ID).getSheetByName('Teams');
  if (!tab) throw new Error('The table sheet has no Teams tab.');
  const rows = tab.getDataRange().getValues();
  const head = rows[0].map(function (h) { return String(h).trim().toLowerCase(); });
  const ti = head.indexOf('team'), gi = head.indexOf('group');
  if (ti < 0 || gi < 0) throw new Error('The Teams tab needs Team and Group columns.');
  const out = {};
  rows.slice(1).forEach(function (r) {
    const team = String(r[ti]).trim(), group = String(r[gi]).trim().toUpperCase();
    if (team && GROUPS.indexOf(group) >= 0) out[team] = group;
  });
  PropertiesService.getScriptProperties().setProperty('TEAM_GROUPS', JSON.stringify(out));
  return out;
}

/** On each response: fill in Group and Leader on its row, and email the leader (copying the coordinator). */
function routeRequest(e) {
  const props = PropertiesService.getScriptProperties();
  const teamGroup = JSON.parse(props.getProperty('TEAM_GROUPS') || '{}');
  const v = function (k) { return ((e.namedValues[k] || [''])[0] || '').trim(); };
  const group = teamGroup[v(T.team)] || '';
  const leader = LEADERS[group] || { name: 'Coordinator', email: '' };

  const sheet = e.range.getSheet();
  const head = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  const put = function (h, val) { const c = head.indexOf(h); if (c >= 0) sheet.getRange(e.range.getRow(), c + 1).setValue(val); };
  put('Group', group); put('Leader', leader.name); put('Status', 'New');

  const lines = Object.keys(e.namedValues).filter(function (k) { return e.namedValues[k].join('').trim(); })
    .map(function (k) { return k + ': ' + e.namedValues[k].join(' '); });
  const to = leader.email || COORDINATOR;
  const subject = 'Pitch Planner: ' + v(T.action) + ' – ' + v(T.team) + ' – ' + v(T.date);
  const body = lines.join('\n') + '\n\nSent to: ' + leader.name + (leader.email ? '' : ' (no email set, so sent to the coordinator)') +
    '\nUpdate the Status column in the responses sheet once handled:\n' + sheet.getParent().getUrl();
  const mail = { to: to, subject: subject, body: body };
  if (to !== COORDINATOR) mail.cc = COORDINATOR;
  MailApp.sendEmail(mail);
}
