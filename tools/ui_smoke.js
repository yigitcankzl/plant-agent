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
  for (const u of ['home.html', 'plant.html?case=chem_c01', 'plant.html?case=dairy_refrig', 'plant.html?case=salt_mvr', 'plant.html?case=swro_monterey', 'plant.html?case=swro_brownsville', 'plant.html?case=freeport_lng_2022', 'plant.html?case=ucte_2006', 'workspace.html?case=roseburg', 'index.html?case=williams_geismar']) {
    await p.goto(`${BASE}/${u}`); await p.waitForTimeout(u.startsWith('home') ? 2500 : 8000);
    const stuck = (await p.content()).includes('Loading case data') || (await p.locator('#verdict').count() && (await p.locator('#verdict').innerText()) === 'Case unavailable');
    await p.screenshot({ path: `${OUT}/${u.replace(/[^a-z0-9]+/gi, '_')}.png` });
    console.log(stuck || errs.length ? 'FAIL' : 'ok  ', u, stuck ? 'stuck loading or case unavailable' : '', errs.splice(0).join(' | '));
    bad += stuck ? 1 : 0;
  }
  await p.goto(`${BASE}/plant.html?case=salt_mvr`); await p.waitForTimeout(5000);
  const saltStartup = await p.evaluate(() => P.has_compressor_curve && !!document.querySelector('#machines button'));
  await p.goto(`${BASE}/plant.html?case=chem_c01`); await p.waitForTimeout(5000);
  const chemStartup = await p.evaluate(() => !P.has_compressor_curve && !document.querySelector('#machines button'));
  console.log(saltStartup && chemStartup ? 'ok  ' : 'FAIL', 'compressor start-up action only appears with a compressor curve');
  bad += saltStartup && chemStartup ? 0 : 1;
  await p.setViewportSize({ width: 1920, height: 1080 });
  await p.goto(`${BASE}/plant.html?case=salt_mvr&worklog=sample&replay=sample`);
  await p.waitForSelector('#worklogPanel:not([hidden])', { timeout: 30000 }).catch(() => {});
  await p.waitForFunction(() => document.querySelector('#replayProgress')?.textContent !== '0 / 0', null, { timeout: 10000 }).catch(() => {});
  const replayOk = await p.evaluate(async () => {
    replayPause(); await replayShow(0);
    const full = document.querySelector('#replayStage').textContent.includes('Clean E-201; add parallel compressor K-202; trim purge steam') &&
      document.querySelector('#replayStage').textContent.includes('Yes, with cleaning and extra compression');
    const bridge = REPLAY.events.findIndex(e => e.kind === 'round'); await replayShow(bridge);
    const between = /Round 1: \d+ checks? failed → back to Muse/.test(document.querySelector('#replayStage').textContent);
    const before = REPLAY.index; replayPlay(); await new Promise(resolve => setTimeout(resolve, 1700)); const advanced = REPLAY.index > before;
    replayPause();
    return full && between && advanced && ['replayToggle', 'replayBack', 'replayNext', 'replaySpeed'].every(id => document.getElementById(id));
  });
  await p.click('#workRunOpen');
  const workConfirmOk = await p.evaluate(() => !document.querySelector('#workConfirm').hidden && document.querySelector('#workGoal').value === P.question && /\$5.?10/.test(document.querySelector('.work-runner .estimate').textContent));
  await p.click('#workCancel');
  const worklogOk = await p.evaluate(() => {
    const rounds = [...document.querySelectorAll('.work-round')], actors = [...document.querySelectorAll('.work-actor')].map(x => x.textContent.trim());
    return rounds.length === 2 && !rounds[0].open && rounds[1].open && actors.includes('Muse') && actors.includes('DWSIM') && actors.includes('pandapower') &&
      workActor({actor: 'muse'}, 'baseten:meta-models/muse-spark-open-1026') === 'Muse Spark Open' &&
      !!document.querySelector('[data-work-result]') && !!document.querySelector('.worklog-sample') && /ILLUSTRATIVE SAMPLE/.test(document.querySelector('.worklog-sample').textContent);
  });
  await p.screenshot({ path: `${OUT}/salt_mvr_worklog_sample_1920x1080.png` });
  await p.screenshot({ path: `${OUT}/salt_mvr_replay_1920x1080.png` });
  await p.locator('[data-work-result]').scrollIntoViewIfNeeded();
  await p.screenshot({ path: `${OUT}/salt_mvr_worklog_result_1920x1080.png` });
  const worklogErrors = errs.splice(0);
  console.log(workConfirmOk && worklogOk && replayOk && !worklogErrors.length ? 'ok  ' : 'FAIL', 'engineering run sample: confirmation, replay, rounds, actors and result', worklogErrors.join(' | '));
  bad += workConfirmOk && worklogOk && replayOk && !worklogErrors.length ? 0 : 1;
  await p.goto(`${BASE}/plant.html?case=ucte_2006`); await p.waitForSelector('[data-open-weights]', { timeout: 30000 }).catch(() => {});
  await p.evaluate(() => { openDetails(true); setWorkspaceView('engineering'); });
  const comparisonOk = await p.evaluate(() => {
    const card = document.querySelector('[data-open-weights]'), rows = card?.querySelectorAll('[data-open-model]') || [];
    return rows.length === 2 && /Muse Wonder/.test(card.textContent) && /Muse Spark Open/.test(card.textContent) &&
      /content-policy filtered/i.test(card.textContent) && /not a model-quality result/i.test(card.textContent) && !!card.querySelector('a[href*="replay=20261101-164315"]');
  });
  await p.locator('[data-open-weights]').scrollIntoViewIfNeeded();
  await p.screenshot({ path: `${OUT}/ucte_open_weights_1920x1080.png` });
  console.log(comparisonOk ? 'ok  ' : 'FAIL', 'UCTE open-weights comparison: two honest model rows and replay link');
  bad += comparisonOk ? 0 : 1;
  await p.goto(`${BASE}/plant.html?case=nrel_ethanol_a300`); await p.waitForSelector('[data-nrel-parity] img', { timeout: 30000 }).catch(() => {});
  const parityOk = await p.evaluate(() => { const card = document.querySelector('[data-nrel-parity]'), img = card?.querySelector('img');
    return !!card && /33 of 35 checks within 5%/.test(card.textContent) && img?.naturalWidth > 0 && !/Not answered yet/.test(document.querySelector('#qaA').textContent); });
  await p.click('#qaBadges [data-act="showParity"]');
  await p.locator('[data-nrel-parity]').scrollIntoViewIfNeeded();
  await p.screenshot({ path: `${OUT}/nrel_a300_parity_1920x1080.png` });
  console.log(parityOk ? 'ok  ' : 'FAIL', 'NREL A300 parity chart and calibration result replace the empty answer');
  bad += parityOk ? 0 : 1;
  await p.setViewportSize({ width: 1440, height: 900 });
  await p.goto(`${BASE}/home.html`); await p.waitForTimeout(2000);
  const homeOk = await p.evaluate(() => !document.body.innerHTML.includes('bt_column_debottleneck') &&
    /case=salt_mvr&tour=1/.test(document.querySelector('.hero-actions a').getAttribute('href')));
  const heroEvidence = await p.evaluate(() => { const line = document.querySelector('#openWeightsHero'), links = [...line.querySelectorAll('a')];
    return /refused the UCTE blackout prompt four times/.test(line.textContent) && /0 violations/.test(line.textContent) &&
      links.some(a => /case=ucte_2006/.test(a.href)) && links.some(a => /evidence\/open-weights-engineering\/README.md/.test(a.href)); });
  console.log(homeOk && heroEvidence ? 'ok  ' : 'FAIL', 'home: demo opens salt_mvr and first-screen open-weights evidence is linked');
  bad += homeOk && heroEvidence ? 0 : 1;
  await p.goto(`${BASE}/plant.html?case=salt_mvr`); await p.waitForSelector('#asOpen', { timeout: 30000 });
  await p.evaluate(() => document.querySelector('#asOpen').click()); await p.waitForSelector('#asTop10 li', { timeout: 30000 }).catch(() => {});
  const assumptionsScale = await p.evaluate(() => {
    const top = document.querySelector('#asTop10'), bulk = document.querySelector('button[data-bulk]');
    window.__bulkPrompt = ''; window.confirm = text => { window.__bulkPrompt = text; return false; }; bulk?.click();
    return !!top?.querySelector('li') && !!(top.compareDocumentPosition(document.querySelector('.as-sum')) & Node.DOCUMENT_POSITION_FOLLOWING) &&
      /maximum throughput|limit \d+/i.test(top.textContent) && /Confirm all \d+ values/.test(window.__bulkPrompt);
  });
  await p.screenshot({ path: `${OUT}/salt_assumptions_top10_1440x900.png` });
  console.log(assumptionsScale ? 'ok  ' : 'FAIL', 'assumptions: sensitivity-ranked inputs first and one counted bulk-confirm dialog');
  bad += assumptionsScale ? 0 : 1;
  for (const c of ['chem_c01', 'salt_mvr']) {  // the verified design leads the result even after a later follow-up
    await p.goto(`${BASE}/plant.html?case=${c}`); await p.waitForSelector('#answers .decision-brief h2', { timeout: 30000 }).catch(() => {});
    const leads = await p.evaluate(() => { const d = designAnswer(), last = P.answers.at(-1);
      return !d || last.combined?.reaches_target || document.querySelector('#answers .decision-brief h2')?.textContent === (plain(d.headline) || 'Engineering decision'); });
    console.log(leads ? 'ok  ' : 'FAIL', `${c}: the verified design leads the result`);
    bad += leads ? 0 : 1;
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
      disciplines: [{ id: 'process', status: 'pass', summary: 'Target solve passes', source: 'DWSIM target solve', checks: [{ check: 'capacity', result: 'pass' }] },
        { id: 'electrical', status: 'fail', summary: 'Transformer overloads on start', source: 'pandapower load flow', checks: [{ check: 'starting voltage', value: 0.82, limit: 0.9 }] }],
      field_checks: [{ item: 'Cooling-water flow', where: 'Check the supply header', changes: 'A low reading changes the recommendation.' }],
      proposals: [{ title: 'Restore cooling-water flow', tag: 'H1007', fixes: 'H1007', cost_class: 'no capex', verified: true,
        changes: [{ path: 'units.H1007.duty_kW', value: 1 }], electrical: { summary: 'TX-47 68 → 70 % loaded; all electrical checks within limits', svg: '/x.svg', over: [] } }], cards: [{ title: 'Duty check', result: 'Within limit', inputs: [] }], checks: [] }];
    answers();
    return !!document.querySelector('.decision-brief') && getComputedStyle(document.querySelector('.engineering-detail')).display === 'none' &&
      document.querySelectorAll('.discipline-gate').length === GATE_ORDER.length && document.body.textContent.includes('Not checked: needs') && !!document.querySelector('.package-action') &&
      !!document.querySelector('.field-check') && !document.querySelector('.field-checks table') && !!document.querySelector('.prop-actions') && /TX-47/.test(document.querySelector('.electrical-line')?.textContent || '');
  });
  await p.screenshot({ path: `${OUT}/decision_workspace.png` });
  await p.evaluate(() => openDetails(true));  // the decision lives in the details drawer
  await p.click('#engineeringView');
  const engineeringView = await p.evaluate(() => getComputedStyle(document.querySelector('.engineering-detail')).display !== 'none' && document.querySelector('#inspectorTitle').textContent === 'Engineering session');
  await p.screenshot({ path: `${OUT}/engineering_workspace.png` });
  await p.click('.discipline-gate.fail');
  const gateEvidence = await p.evaluate(() => document.querySelector('#modal').classList.contains('on') && /pandapower/.test(document.querySelector('#modalBox').textContent));
  await p.evaluate(() => document.querySelector('#modal').classList.remove('on'));
  await p.click('#decisionView');
  await p.click('#focusBtn');
  const focusOn = await p.evaluate(() => document.body.classList.contains('canvas-focus') && getComputedStyle(document.querySelector('aside.right')).display === 'none');
  await p.screenshot({ path: `${OUT}/drawing_focus.png` });
  await p.keyboard.press('Escape');
  const focusOff = await p.evaluate(() => !document.body.classList.contains('canvas-focus'));
  await p.keyboard.press('d');
  const detailShortcut = await p.evaluate(() => document.querySelector('#engineeringView').getAttribute('aria-pressed') === 'true');
  await p.keyboard.press('d');
  await p.keyboard.press('l');
  const labelsShortcut = await p.evaluate(() => document.querySelector('#pidViewport').classList.contains('labels-off'));
  await p.keyboard.press('l');
  const workspaceUi = readableAnswer && engineeringView && gateEvidence && focusOn && focusOff && detailShortcut && labelsShortcut;
  console.log(workspaceUi ? 'ok  ' : 'FAIL', 'decision/engineering views, calculated discipline rail, package action and focus mode', workspaceUi ? '' : JSON.stringify({readableAnswer, engineeringView, gateEvidence, focusOn, focusOff, detailShortcut, labelsShortcut}));
  bad += workspaceUi ? 0 : 1;
  await p.evaluate(() => openDetails(false));
  await p.keyboard.press('/');  // the ask box lives in the details drawer
  await p.waitForFunction(() => document.activeElement === document.querySelector('#q'), null, { timeout: 5000 }).catch(() => {});
  const askOpen = await p.evaluate(() => document.body.classList.contains('dd-open') && document.activeElement === document.querySelector('#q'));
  await p.click('#ddClose');
  const whatIfFloats = await p.evaluate(() => !document.body.classList.contains('dd-open') && !document.querySelector('#scenario').hidden &&
    getComputedStyle(document.querySelector('#workbench')).position === 'absolute');
  console.log(askOpen && whatIfFloats ? 'ok  ' : 'FAIL', 'ask in the details drawer; what-if floats on the drawing');
  bad += askOpen && whatIfFloats ? 0 : 1;
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
    !document.querySelector('#answers .prop-actions') && ![...document.querySelectorAll('button')].some(b => /decision file|engineering package/i.test(b.textContent)));
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
  await p.waitForSelector('#sheet .badge', { timeout: 20000 }).catch(() => {}); const badges = p.locator('#sheet .badge');
  const badgeCount = await badges.count();
  await p.click('#toggleLabels');
  const labelsHidden = await p.evaluate(() => document.querySelector('#pidViewport').classList.contains('labels-off') &&
    document.querySelector('#toggleLabels').getAttribute('aria-pressed') === 'false' &&
    (!document.querySelector('#sheet .badge') || getComputedStyle(document.querySelector('#sheet .badge')).display === 'none'));
  await p.click('#toggleLabels');
  const labelsRestored = await p.evaluate(() => !document.querySelector('#pidViewport').classList.contains('labels-off') &&
    document.querySelector('#toggleLabels').getAttribute('aria-pressed') === 'true');
  console.log(badgeCount && labelsHidden && labelsRestored ? 'ok  ' : 'FAIL', 'P&ID labels hide and restore');
  // a hostile DEXPI tag must reach the handler as data, never run as script
  let dialogs = 0; const onDialog = d => { dialogs += 1; d.dismiss(); }; p.on('dialog', onDialog);
  const evil = ["x');alert(1);//", '"><img src=x onerror=alert(2)>'];
  const got = await p.evaluate(tags => {
    const seen = [], keep = window.select; window.select = t => seen.push(t);
    const box = document.createElement('div');
    box.innerHTML = tags.map(t => `<div class="eq" ${act('select', t)}>${esc(t)}</div>`).join('');
    document.body.append(box); box.querySelectorAll('.eq').forEach(e => e.click()); box.remove();
    window.select = keep; return seen;
  }, evil);
  await p.waitForTimeout(300); p.off('dialog', onDialog);
  const xssSafe = !dialogs && JSON.stringify(got) === JSON.stringify(evil);
  console.log(xssSafe ? 'ok  ' : 'FAIL', 'hostile P&ID tags stay data (no script runs)', xssSafe ? '' : JSON.stringify({dialogs, got}));
  bad += xssSafe ? 0 : 1;
  bad += badgeCount && labelsHidden && labelsRestored ? 0 : 1;
  for (const c of ['salt_mvr', 'chem_c01']) {
    await p.goto(`${BASE}/plant.html?case=${c}&tour=1`); await p.waitForSelector('#tour', { state: 'visible', timeout: 20000 });
    const texts = [];
    let limitsOnExisting = false, fixOnProposed = false;
    for (let i = 0; i < 6; i++) {
      await p.waitForFunction(() => document.querySelector('#tourText').textContent !== '…', null, { timeout: 30000 }).catch(() => {});
      await p.waitForTimeout(800); texts.push(await p.locator('#tourText').innerText());
      const step = await p.locator('#tourStep').innerText(), view = await p.evaluate(() => document.querySelector('#vExisting')?.classList.contains('on') ? 'existing' : 'proposed');
      if (/What limits it/.test(step)) limitsOnExisting = view === 'existing';
      if (/fix/.test(step)) fixOnProposed = view === 'proposed';
      await p.click('#tourNext');
    }
    const stale = texts.some(t => /14 measured values|Three limits bind|No capital spend/.test(t));
    const ok = !stale && limitsOnExisting && fixOnProposed && texts.some(t => /Muse/.test(t));
    console.log(errs.length || !ok ? 'FAIL' : 'ok  ', `guided demo on ${c}: limits on Existing, Muse's fix on Proposed, text from the case data`, errs.join(' | '));
    bad += ok ? 0 : 1;
  }
  // every discipline gate is visible without a hidden horizontal scroll
  await p.goto(`${BASE}/plant.html?case=salt_mvr`); await p.waitForSelector('.discipline-rail', { timeout: 30000 }).catch(() => {});
  const railFits = await p.evaluate(() => { const r = document.querySelector('.discipline-rail'); return !!r && r.scrollWidth <= r.clientWidth + 1 && document.querySelectorAll('.discipline-gate').length >= 5; });
  console.log(railFits ? 'ok  ' : 'FAIL', 'discipline gates on salt_mvr: calculated shown, the rest folded');
  bad += railFits ? 0 : 1;
  // a blind case with a recorded outcome shows the agent and the engineers side by side
  const bv = await (await fetch(`${BASE}/api/plant/swro_brownsville/project`)).json().catch(() => ({}));
  if (bv.outcome) {
    await p.goto(`${BASE}/plant.html?case=swro_brownsville`); const shown = await p.waitForSelector('.outcome-compare', { timeout: 30000 }).then(() => true).catch(() => false);
    console.log(shown ? 'ok  ' : 'FAIL', 'Brownsville compares the agent with the recorded decision');
    bad += shown ? 0 : 1;
  }
  await b.close(); process.exit(bad || errs.length ? 1 : 0);
})();
