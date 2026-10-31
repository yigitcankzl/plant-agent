// UI smoke test: every page loads in a fresh browser without script errors or a stuck "Loading", and the guided demo runs.
// node tools/ui_smoke.js [base_url] [screenshot_dir]   (Playwright from PLAYWRIGHT or the local npx cache)
let playwright;
try { playwright = require(process.env.PLAYWRIGHT || 'playwright'); }
catch (_) { playwright = require('/home/kizil/.npm/_npx/e41f203b7505f1fb/node_modules/playwright'); }
const { chromium } = playwright;
const BASE = process.argv[2] || 'http://127.0.0.1:8765', OUT = process.argv[3] || '/tmp/pwtest';
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  let bad = 0;
  for (const u of ['home.html', 'plant.html?case=chem_c01', 'plant.html?case=dairy_refrig', 'plant.html?case=salt_mvr', 'plant.html?case=swro_monterey', 'plant.html?case=swro_brownsville', 'workspace.html?case=roseburg', 'index.html?case=williams_geismar']) {
    await p.goto(`${BASE}/${u}`); await p.waitForTimeout(u.startsWith('home') ? 2500 : 8000);
    const stuck = (await p.content()).includes('Loading case data');
    await p.screenshot({ path: `${OUT}/${u.replace(/[^a-z0-9]+/gi, '_')}.png` });
    console.log(stuck || errs.length ? 'FAIL' : 'ok  ', u, stuck ? 'stuck loading' : '', errs.splice(0).join(' | '));
    bad += stuck ? 1 : 0;
  }
  await p.goto(`${BASE}/plant.html?case=chem_c01`); await p.waitForSelector('#sheet [data-tag="H1007"]');
  const startsFocused = await p.evaluate(() => !document.querySelector('#infoDrawer').classList.contains('open') &&
    document.querySelector('#inspectorTitle').textContent === 'Result' && document.querySelector('#scenario').hidden === false);
  await p.click('#infoBtn'); const drawerOpened = await p.locator('#infoDrawer').evaluate(e => e.classList.contains('open'));
  await p.click('#infoDrawer .drawer-head button');
  await p.click('[data-mode="troubleshoot"]');
  const troubleshootFocused = await p.evaluate(() => document.querySelector('#inspectorTitle').textContent === 'Troubleshoot' && document.querySelector('#scenario').hidden);
  await p.click('[data-mode="capacity"]');
  await p.locator('#sheet [data-tag="H1007"]').evaluate(e => e.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, button: 0 })));
  await p.locator('#sheet [data-tag="H1007"]').evaluate(e => e.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, button: 0 })));
  await p.waitForFunction(() => document.querySelector('#inspectorTitle').textContent === 'Equipment', null, { timeout: 15000 }).catch(() => {});
  const equipmentFocused = await p.evaluate(() => document.querySelector('#inspectorTitle').textContent === 'Equipment' && !document.querySelector('#answers').hidden);
  console.log(startsFocused && drawerOpened && troubleshootFocused && equipmentFocused ? 'ok  ' : 'FAIL', 'focused capacity layout, drawer, modes and equipment inspector');
  bad += startsFocused && drawerOpened && troubleshootFocused && equipmentFocused ? 0 : 1;
  await p.click('.inspector-back');
  const readableAnswer = await p.evaluate(() => {
    P.answers = [{ request: 'Reach 120%', headline: 'One verified change is required', summary: 'Test summary', seconds: 1, cost_usd: 0,
      highlights: [{ tag: 'H1007', severity: 'fail', text: 'Cooling duty reaches its limit.' }],
      field_checks: [{ item: 'Cooling-water flow', where: 'Check the supply header', changes: 'A low reading changes the recommendation.' }],
      proposals: [{ title: 'Restore cooling-water flow', tag: 'H1007', fixes: 'H1007', cost_class: 'no capex', verified: true,
        changes: [{ path: 'units.H1007.duty_kW', value: 1 }], electrical: { summary: 'TX-47 68 → 70 % loaded; all electrical checks within limits', svg: '/x.svg', over: [] } }], cards: [{ title: 'Duty check', result: 'Within limit', inputs: [] }], checks: [] }];
    answers();
    return !!document.querySelector('.field-check') && !document.querySelector('.field-checks table') && !!document.querySelector('.prop-actions') && /TX-47/.test(document.querySelector('.electrical-line')?.textContent || '');
  });
  console.log(readableAnswer ? 'ok  ' : 'FAIL', 'result inspector uses stacked field checks and proposal actions');
  bad += readableAnswer ? 0 : 1;
  await p.goto(`${BASE}/plant.html?case=salt_mvr`); await p.waitForTimeout(5000);
  const saltReady = await p.evaluate(() => Number(P?.built?.review?.blocking || 0) === 0 &&
    Number(P?.capacity?.capacity_multiple || 0) >= 1);
  console.log(saltReady ? 'ok  ' : 'FAIL', 'salt model review and replayed capacity');
  bad += saltReady ? 0 : 1;
  // the UI rule under test does not depend on which case happens to be blocked today: force a blocking review on salt_mvr
  await p.route('**/api/plant/salt_mvr/project', async route => {
    const res = await route.fetch(); const d = await res.json();
    d.built = d.built || {};
    d.built.review = { ...(d.built.review || {}), status: 'model needs review', blocking: 1,
      findings: [{ severity: 'block', check: 'forced for the smoke test', evidence: 'injected', items: [] }] };
    d.built.review_status = 'model needs review';
    await route.fulfill({ response: res, json: d });
  });
  await p.goto(`${BASE}/plant.html?case=salt_mvr`); await p.waitForTimeout(5000);
  await p.unroute('**/api/plant/salt_mvr/project');
  const blockedIsReadOnly = await p.evaluate(() => Number(P?.built?.review?.blocking || 0) > 0 &&
    !document.querySelector('#answers .prop-actions') && ![...document.querySelectorAll('button')].some(b => /decision file/i.test(b.textContent)));
  console.log(blockedIsReadOnly ? 'ok  ' : 'FAIL', 'blocked model cannot apply proposals or issue a pack');
  bad += blockedIsReadOnly ? 0 : 1;
  await p.goto(`${BASE}/plant.html?case=salt_mvr`); await p.waitForTimeout(5000);
  await p.click('[data-mode="troubleshoot"]'); await p.waitForTimeout(800);
  const forecastShown = await p.evaluate(() => { const c = document.querySelector('#troublePanel .forecast-card');
    return !!c && /E-201 (passed|reaches) its limit/.test(c.textContent) && /verified in DWSIM/i.test(c.textContent) && !!c.querySelector('img'); });
  await p.screenshot({ path: `${OUT}/salt_forecast_card.png` });
  console.log(forecastShown ? 'ok  ' : 'FAIL', 'salt morning-check fouling forecast card');
  bad += forecastShown ? 0 : 1;
  await p.goto(`${BASE}/plant.html?case=chem_c01`); await p.waitForSelector('#sheet [data-tag="H1007"]');
  const viewport = p.locator('#pidViewport'), before = await p.locator('#sheet').evaluate(e => new DOMMatrix(getComputedStyle(e).transform).a);
  const bounds = await viewport.boundingBox();
  await p.mouse.move(bounds.x + bounds.width / 2, bounds.y + bounds.height / 2); await p.mouse.wheel(0, -200);
  const after = await p.locator('#sheet').evaluate(e => new DOMMatrix(getComputedStyle(e).transform).a);
  await p.locator('#zoomFit').click();
  const tag = p.locator('#sheet [data-tag="H1007"]'); const box = await tag.boundingBox();
  await p.mouse.move(box.x + box.width / 2, box.y + box.height / 2); await p.mouse.down();
  await p.mouse.move(box.x + box.width / 2 + 40, box.y + box.height / 2 + 20, { steps: 5 }); await p.mouse.up();
  await p.waitForTimeout(500);
  const draggedSelection = await p.locator('#sheet [data-tag="H1007"]').evaluate(e => e.classList.contains('u-sel'));
  console.log(after > before && !draggedSelection ? 'ok  ' : 'FAIL', 'P&ID wheel zoom and drag without selection');
  bad += after > before && !draggedSelection ? 0 : 1;
  const badges = p.locator('#sheet .badge');
  const badgeCount = await badges.count();
  await p.click('#toggleLabels');
  const labelsHidden = await p.evaluate(() => document.querySelector('#pidViewport').classList.contains('labels-off') &&
    document.querySelector('#toggleLabels').getAttribute('aria-pressed') === 'false' &&
    (!document.querySelector('#sheet .badge') || getComputedStyle(document.querySelector('#sheet .badge')).display === 'none'));
  await p.click('#toggleLabels');
  const labelsRestored = await p.evaluate(() => !document.querySelector('#pidViewport').classList.contains('labels-off') &&
    document.querySelector('#toggleLabels').getAttribute('aria-pressed') === 'true');
  console.log(badgeCount && labelsHidden && labelsRestored ? 'ok  ' : 'FAIL', 'P&ID labels hide and restore');
  bad += badgeCount && labelsHidden && labelsRestored ? 0 : 1;
  await p.goto(`${BASE}/plant.html?case=chem_c01&tour=1`); await p.waitForSelector('#tour', { state: 'visible', timeout: 20000 });
  for (let i = 0; i < 6; i++) { await p.waitForTimeout(1200); await p.click('#tourNext'); }
  console.log(errs.length ? 'FAIL' : 'ok  ', 'guided demo, 6 steps', errs.join(' | '));
  await b.close(); process.exit(bad || errs.length ? 1 : 0);
})();
