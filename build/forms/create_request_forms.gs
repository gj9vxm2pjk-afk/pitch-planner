/**
 * WBR Pitch Planner: request / modify / cancel a session.
 *
 * The form's dropdowns come from the club's table sheet (WBR Fixtures 26/27): teams from the Teams tab, and for modify and cancel
 * the team's upcoming fixtures from the Fixtures tab (and the Seniors tab if it exists). Type, venue and session time use the same
 * fixed values as the sheet's own dropdowns (see validate_table.py).
 *
 * First time (about 2 minutes), signed in as the club coordinator, who must be able to open the table sheet:
 *  1. Go to https://script.google.com and press New project.
 *  2. Delete the sample code, paste this whole file, press Save.
 *  3. Edit EDITORS below (the people who approve changes).
 *  4. Press Run (function createForms). Approve the permission prompts.
 *  5. Open View > Logs: it prints the form link to share and the editor link.
 *  6. Press Run (function installWeeklyRefresh) so the dropdowns follow the sheet.
 *
 * To keep the form link you already share, do not run createForms. Put the existing form's ID (the long code in its edit link,
 * https://docs.google.com/forms/d/<ID>/edit) in FORM_ID and run refreshForm. That replaces the questions and keeps the link and
 * the responses. Editors and the email notification stay as they are.
 *
 * Run refreshForm by hand after a big change to the fixtures. The weekly refresh does it for you.
 */
const EDITORS = ['coordinator@example.com'];            // <-- replace with the 2-3 editors' email addresses
const FORM_ID = '1MjbGzPncwrqyAV2JlS5-YBzRgY5ufTX3pJraBa495HY';   // existing form to update; leave blank for createForms to make a new one
const TABLE_SHEET_ID = '1tyHepQWdOvekFNW3gSeV_8pICxETJMfHZktI7c6tOCY';   // WBR Fixtures 26/27 (table)

// Same values as the sheet's dropdowns (validate_table.py). Breaks are not sessions, so they are not offered.
const TYPES = ['Match', 'Training', 'Pre-season', 'Indoors', 'Festival', 'Other'];
const VENUES = ['Home grass', 'Home AGP', 'Away'];
const SESSION_TIMES = ['09:00–10:30', '10:30–12:30', '12:30–15:00'];
const CHANGES = ['Date', 'Session time', 'Venue', 'Opponent', 'Car park duty', 'Other'];

const REQUEST = 'Request a session';
const MODIFY = 'Modify a session';
const CANCEL = 'Cancel a session';

function createForms() {
  const form = FormApp.create('WBR Pitch Planner: request, modify or cancel a session');
  form.setCollectEmail(true).setConfirmationMessage('Thanks. The coordinator will confirm once it is in the planner.');
  form.setProgressBar(true);
  buildQuestions(form);

  // Responses go to their own sheet, shared with the editors only
  const ss = SpreadsheetApp.create('WBR Pitch Planner: session requests');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());
  SpreadsheetApp.flush();
  const sheet = ss.getSheets().filter(function (s) { return /Form responses/.test(s.getName()); })[0] || ss.getSheets()[0];
  const lastCol = sheet.getLastColumn();
  sheet.getRange(1, lastCol + 1, 1, 2).setValues([['Status', 'Handled by']]).setFontWeight('bold');
  sheet.getRange(2, lastCol + 1, 500, 1).setDataValidation(
    SpreadsheetApp.newDataValidation().requireValueInList(['New', 'Approved', 'Done', 'Rejected'], true).build());
  sheet.setFrozenRows(1);

  // Only the editors can see responses or the sheet; an email goes to them on every submission
  EDITORS.forEach(function (e) { ss.addEditor(e); form.addEditor(e); });
  ScriptApp.newTrigger('notifyEditors').forSpreadsheet(ss).onFormSubmit().create();
  const props = PropertiesService.getScriptProperties();
  props.setProperty('EDITORS', EDITORS.join(','));
  props.setProperty('FORM_ID', form.getId());

  Logger.log('Share this link with managers: ' + form.getPublishedUrl());
  Logger.log('Edit the form: ' + form.getEditUrl());
  Logger.log('Requests sheet (editors only): ' + ss.getUrl());
}

/** Replaces the form's questions with ones built from today's sheet. Keeps the link, the responses and the settings. */
function refreshForm() {
  const id = FORM_ID || PropertiesService.getScriptProperties().getProperty('FORM_ID');
  if (!id) throw new Error('Set FORM_ID at the top of the script, or run createForms first.');
  const form = FormApp.openById(id);
  buildQuestions(form);
  Logger.log('Form refreshed: ' + form.getPublishedUrl());
}

/** Runs refreshForm every Monday morning so new fixtures appear and past ones drop off. */
function installWeeklyRefresh() {
  ScriptApp.getProjectTriggers().filter(function (t) { return t.getHandlerFunction() === 'refreshForm'; })
    .forEach(function (t) { ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('refreshForm').timeBased().onWeekDay(ScriptApp.WeekDay.MONDAY).atHour(6).create();
}

function buildQuestions(form) {
  const data = readSheet();
  form.getItems().forEach(function (item) { form.deleteItem(item); });

  form.setDescription('Use this to request a new session, change an existing one, or cancel one. The coordinator will confirm by reply. ' +
    'Please send changes by Thursday noon for the weekend; for anything urgent, message the coordinator on WhatsApp. ' +
    'For a block of weeks or a whole age group, send one request and say so in the reason.');

  form.addTextItem().setTitle('Your name').setRequired(true);
  const action = form.addMultipleChoiceItem().setTitle('What do you want to do?').setRequired(true);

  // Request: a new session or fixture
  const request = form.addPageBreakItem().setTitle(REQUEST);
  form.addListItem().setTitle('Team').setChoiceValues(data.teams).setRequired(true);
  form.addDateItem().setTitle('Date').setRequired(true);
  form.addListItem().setTitle('Type').setChoiceValues(TYPES).setRequired(true);
  form.addListItem().setTitle('Venue').setChoiceValues(VENUES).setRequired(true);
  form.addListItem().setTitle('Session time').setChoiceValues(SESSION_TIMES).setHelpText('Leave blank if you are not sure or it is a match with a set kick-off.');
  form.addTextItem().setTitle('Opponent (matches)');
  form.addParagraphTextItem().setTitle('Reason / anything else we should know');
  request.setGoToPage(FormApp.PageNavigationType.SUBMIT);

  // Modify: pick the team, then one of its upcoming sessions, then say what changes
  const modifyTeam = form.addPageBreakItem().setTitle(MODIFY);
  const modifyPick = form.addMultipleChoiceItem().setTitle('Which team? (' + MODIFY.toLowerCase() + ')').setRequired(true);
  const modifyTeamPages = data.teamsWithFixtures.map(function (team) {
    const page = form.addPageBreakItem().setTitle(team + ': pick the session to change');
    form.addListItem().setTitle('Modify: which ' + team + ' session?').setChoiceValues(data.fixtures[team]).setRequired(true);
    return page;
  });
  const modifyDetails = form.addPageBreakItem().setTitle('What needs to change?');
  form.addCheckboxItem().setTitle('What needs to change?').setChoiceValues(CHANGES).setRequired(true);
  form.addDateItem().setTitle('New date (if changing)');
  form.addListItem().setTitle('New session time (if changing)').setChoiceValues(SESSION_TIMES);
  form.addListItem().setTitle('New venue (if changing)').setChoiceValues(VENUES);
  form.addTextItem().setTitle('New opponent (if changing)');
  form.addParagraphTextItem().setTitle('Reason / anything else we should know');
  modifyDetails.setGoToPage(FormApp.PageNavigationType.SUBMIT);

  // Cancel: pick the team, then one of its upcoming sessions, then the reason
  const cancelTeam = form.addPageBreakItem().setTitle(CANCEL);
  const cancelPick = form.addMultipleChoiceItem().setTitle('Which team? (' + CANCEL.toLowerCase() + ')').setRequired(true);
  const cancelTeamPages = data.teamsWithFixtures.map(function (team) {
    const page = form.addPageBreakItem().setTitle(team + ': pick the session to cancel');
    form.addListItem().setTitle('Cancel: which ' + team + ' session?').setChoiceValues(data.fixtures[team]).setRequired(true);
    return page;
  });
  const cancelDetails = form.addPageBreakItem().setTitle('Why is it being cancelled?');
  form.addParagraphTextItem().setTitle('Reason for cancelling').setRequired(true);

  // Wire the navigation now that every page exists
  action.setChoices([action.createChoice(REQUEST, request), action.createChoice(MODIFY, modifyTeam), action.createChoice(CANCEL, cancelTeam)]);
  modifyPick.setChoices(data.teamsWithFixtures.map(function (t, i) { return modifyPick.createChoice(t, modifyTeamPages[i]); }));
  cancelPick.setChoices(data.teamsWithFixtures.map(function (t, i) { return cancelPick.createChoice(t, cancelTeamPages[i]); }));
  modifyTeamPages.forEach(function (p) { p.setGoToPage(modifyDetails); });
  cancelTeamPages.forEach(function (p) { p.setGoToPage(cancelDetails); });
}

/** Teams and each team's upcoming sessions, read from the table sheet. */
function readSheet() {
  const ss = SpreadsheetApp.openById(TABLE_SHEET_ID);
  const tz = ss.getSpreadsheetTimeZone();
  const today = Utilities.formatDate(new Date(), tz, 'yyyy-MM-dd');

  const teams = [];
  const teamsTab = ss.getSheetByName('Teams');
  if (!teamsTab) throw new Error('The table sheet has no Teams tab.');
  teamsTab.getRange(2, 1, Math.max(teamsTab.getLastRow() - 1, 1), 1).getValues().forEach(function (r) {
    const t = String(r[0]).trim();
    if (t && teams.indexOf(t) < 0) teams.push(t);
  });

  const fixtures = {};
  ['Fixtures', 'Seniors'].forEach(function (name) {
    const tab = ss.getSheetByName(name);
    if (!tab || tab.getLastRow() < 2) return;
    const rows = tab.getDataRange().getValues();
    const col = {};
    rows[0].forEach(function (h, i) { col[String(h).trim()] = i; });
    if (col['Date'] === undefined || col['Team'] === undefined) return;
    rows.slice(1).forEach(function (r) {
      const team = String(r[col['Team']]).trim();
      const type = String(r[col['Type']] || '').trim();
      const d = r[col['Date']];
      if (!team || !d || type === 'Break') return;
      const iso = d instanceof Date ? Utilities.formatDate(d, tz, 'yyyy-MM-dd') : String(d).trim().slice(0, 10);
      if (!/^\d{4}-\d{2}-\d{2}$/.test(iso) || iso < today) return;
      const pretty = Utilities.formatDate(new Date(iso + 'T12:00:00'), tz, 'EEE d MMM');
      const get = function (k) { return col[k] === undefined ? '' : String(r[col[k]] || '').trim(); };
      const opp = get('Opponent');
      const bits = [pretty, type + (opp ? ' v ' + opp : ''), get('Venue'), get('Session time') || get('Kick-off')].filter(String);
      if (get('Status') === 'Provisional') bits.push('(provisional)');
      (fixtures[team] = fixtures[team] || []).push({ iso: iso, label: bits.join(' – ') });
      if (teams.indexOf(team) < 0) teams.push(team);
    });
  });

  const out = {};
  Object.keys(fixtures).forEach(function (team) {
    const seen = {};
    out[team] = fixtures[team].sort(function (a, b) { return a.iso < b.iso ? -1 : a.iso > b.iso ? 1 : 0; })
      .map(function (f) {          // list choices must be unique: tell apart two identical rows
        seen[f.label] = (seen[f.label] || 0) + 1;
        return seen[f.label] > 1 ? f.label + ' (' + seen[f.label] + ')' : f.label;
      });
  });
  return { teams: teams, teamsWithFixtures: teams.filter(function (t) { return out[t]; }), fixtures: out };
}

function notifyEditors(e) {
  const to = PropertiesService.getScriptProperties().getProperty('EDITORS');
  const lines = Object.keys(e.namedValues).filter(function (k) { return e.namedValues[k].join('').trim(); })
    .map(function (k) { return k + ': ' + e.namedValues[k].join(' '); });
  MailApp.sendEmail(to, 'Pitch Planner session request', lines.join('\n') + '\n\nUpdate the Status column in the Requests sheet once handled.');
}
