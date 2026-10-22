/**
 * WBR Pitch Planner: creates the change request form and its "Requests" sheet.
 *
 * How to run (one time, about 2 minutes), signed in as the club coordinator:
 *  1. Go to https://script.google.com and press New project.
 *  2. Delete the sample code, paste this whole file, press Save.
 *  3. Edit EDITORS below (the people who approve changes).
 *  4. Press Run (function createForms). Approve the permission prompts.
 *  5. Open View > Logs: it prints the form link to share and the editor link.
 */
const EDITORS = ['coordinator@example.com'];            // <-- replace with the 2-3 editors' email addresses

const TEAMS = ['U6', 'U7', 'U8', 'U9', 'U10', 'U11', 'U12 Boys', 'U13 Boys', 'U14 Boys', 'U15 Boys', 'U16 Boys', 'Colts',
  'U12 Girls', 'U14 Girls', 'U16 Girls', 'U18 Girls', "Women's 1st XV", "Women's 2nd XV",
  "Men's 1st XV", 'Vikings', 'Rangers', 'Vets', 'Several teams / whole club'];
const CHANGES = ['Cancel a fixture or session', 'Move date or time', 'Change venue (home grass / AGP / away)', 'Add a new fixture or session',
  'Change opponent or kick-off', 'Car park duty swap', 'Other'];

function createForms() {
  const form = FormApp.create('WBR Pitch Planner: request a change');
  form.setDescription('Use this to ask for a change to fixtures, training or pitch bookings. The coordinator will confirm by reply. ' +
    'Please send changes by Thursday noon for the weekend; for anything urgent, message the coordinator on WhatsApp.');
  form.setCollectEmail(true).setConfirmationMessage('Thanks. The coordinator will confirm once it is in the planner.');
  form.setProgressBar(true);

  form.addTextItem().setTitle('Your name').setRequired(true);
  const kind = form.addMultipleChoiceItem().setTitle('What kind of request is this?').setRequired(true);

  // Path 1: a single change
  const single = form.addPageBreakItem().setTitle('One change');
  form.addListItem().setTitle('Team').setChoiceValues(TEAMS).setRequired(true);
  form.addDateItem().setTitle('Date of the fixture or session (the original date)').setRequired(true);
  form.addMultipleChoiceItem().setTitle('What do you need?').setChoiceValues(CHANGES).setRequired(true);
  form.addTextItem().setTitle('New date, time, venue or opponent (if any)');
  form.addParagraphTextItem().setTitle('Reason / anything else we should know');

  // Path 2: several changes
  const bulk = form.addPageBreakItem().setTitle('Several changes');
  form.addParagraphTextItem().setTitle('List the changes, one per line: team, date, what changes')
    .setHelpText('Example: U12 Boys, 25 Oct, move to AGP. Or paste a link to a sheet that lists them.').setRequired(true);
  form.addParagraphTextItem().setTitle('Reason / anything else we should know');

  kind.setChoices([
    kind.createChoice('One change', single),
    kind.createChoice('Several changes (e.g. a block of weeks or a whole age group)', bulk)]);
  single.setGoToPage(FormApp.PageNavigationType.SUBMIT);   // after the single-change page, submit (skip the bulk page)

  // Responses go to their own sheet, shared with the editors only
  const ss = SpreadsheetApp.create('WBR Pitch Planner: change requests');
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
  PropertiesService.getScriptProperties().setProperty('EDITORS', EDITORS.join(','));

  Logger.log('Share this link with managers: ' + form.getPublishedUrl());
  Logger.log('Edit the form: ' + form.getEditUrl());
  Logger.log('Requests sheet (editors only): ' + ss.getUrl());
}

function notifyEditors(e) {
  const to = PropertiesService.getScriptProperties().getProperty('EDITORS');
  const lines = Object.keys(e.namedValues).map(function (k) { return k + ': ' + e.namedValues[k].join(' '); });
  MailApp.sendEmail(to, 'Pitch Planner change request', lines.join('\n') + '\n\nUpdate the Status column in the Requests sheet once handled.');
}
