// Smoke test for the Pitch Planner page. Usage: node smoke.cjs [path-or-url]   (default: ../../index.html)
// Needs Playwright (npm i playwright) and a Chromium. Prints PASS/FAIL per check and exits 1 on any failure.
const path = require('path');
const { chromium } = require('playwright');
const target = process.argv[2] || 'file://' + path.resolve(__dirname, '../../index.html');
const results = []; const ok = (name, cond, extra = '') => { results.push(cond); console.log((cond ? 'PASS ' : 'FAIL ') + name + (extra ? '  ' + extra : '')); };
(async () => {
  const b = await chromium.launch({ args: ['--no-sandbox'] });
  for (const [label, vp, scheme] of [['desktop', { width: 1100, height: 900 }, 'light'], ['phone', { width: 390, height: 844 }, 'light'], ['dark', { width: 1100, height: 900 }, 'dark']]) {
    const p = await (await b.newContext({ viewport: vp, colorScheme: scheme })).newPage(); const errs = [];
    p.on('pageerror', e => errs.push(String(e)));
    await p.goto(target); await p.waitForTimeout(1200);
    ok(`${label}: no page errors`, errs.length === 0, errs.join(' | '));
    ok(`${label}: Plan and Message tabs`, await p.locator('#viewSeg button').count() === 2);
    ok(`${label}: request link points at the form`, /docs\.google\.com\/forms/.test(await p.locator('#reqlink').getAttribute('href') || ''));
    ok(`${label}: no sideways scroll`, await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    ok(`${label}: usage footer hidden when no counter URL`, await p.evaluate(() => !document.getElementById('foot') || document.getElementById('foot').hidden));
    if (label === 'phone') ok('phone: list view replaces the grid', await p.evaluate(() => getComputedStyle(document.querySelector('.plist')).display !== 'none' && getComputedStyle(document.querySelector('.gridwrap')).display === 'none'));
    if (label === 'desktop') {
      const msg = await p.evaluate(() => { S.sat = upcomingSaturday(); return buildWeekendMessage(modelFor(S.sat)); });
      ok('message has no kick-off or referee wording', !/KO \[|Ref \[|Referee|Kick-off/.test(msg));
      ok('message never says "not on duty"', !/not on duty/i.test(msg));
      await p.click('#viewSeg button[data-v=message]'); ok('Message tab shows the text box', await p.locator('#msgText').count() === 1);
      await p.click('#viewSeg button[data-v=day]').catch(() => {});
      await p.fill('#q', 'zzzzz'); await p.waitForTimeout(200); await p.fill('#q', '');
      const t = await b.newContext({ viewport: { width: 1280, height: 720 } }).then(c => c.newPage());
      await t.goto(target + '#tv'); await t.waitForTimeout(900);
      ok('TV mode hides the controls', await t.evaluate(() => getComputedStyle(document.querySelector('.bar')).display === 'none'));
    }
  }
  await b.close();
  const bad = results.filter(x => !x).length; console.log(`\n${results.length - bad}/${results.length} checks passed`); process.exit(bad ? 1 : 0);
})();
