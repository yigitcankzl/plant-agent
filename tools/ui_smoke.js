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
  // The redline flow uses only stubbed responses: never make a paid vision call.
  const redlineId = 'a'.repeat(64), redlineRoot = `**/api/plant/salt_mvr/redline`;
  let redlineConfirmation = null;
  await p.route('**/api/plant/salt_mvr/project', route => route.fulfill({json: {title: 'Salt MVR redline test', allow_runs: true, simulator_available: true}}));
  await p.route(redlineRoot, route => route.fulfill({json: {job: 'redline-smoke'}}));
  await p.route('**/api/job/redline-smoke', route => route.fulfill({json: {done: true, answer: {id: redlineId, items: [
    {index: 0, tag: 'E-201', ink: 'Clean to U 2,500', confidence: .95, valid: true, errors: [], unreadable: [], change: {path: 'units.V-201.U_W_m2K', value: 2500}},
    {index: 1, tag: 'P-101B', ink: 'Add parallel pump', confidence: .7, valid: false, errors: ['needs its own limits'], unreadable: ['rating not written'], change: {add_unit: {id: 'P-101B', type: 'pump'}}}
  ], unreadable: ['signature']}}}));
  await p.route(`${redlineRoot}/${redlineId}/confirm`, route => { redlineConfirmation = route.request().postDataJSON(); return route.fulfill({json: {status: 'confirmed'}}); });
  await p.route(`${redlineRoot}/${redlineId}/check`, route => route.fulfill({json: {
    engineer: [{check: 'process', status: 'pass', title: 'Target holds', engine: 'DWSIM', numbers: {capacity_multiple: 1.2}}],
    muse: [{check: 'process', status: 'fail', title: 'Target short', engine: 'DWSIM', numbers: {capacity_multiple: 1.1}},
           {check: 'vendor', status: 'open', title: 'Vendor curve needed', numbers: {}}], muse_headline: 'Saved Muse design', drawing_url: null
  }}));
  await p.goto(`${BASE}/redline.html?case=salt_mvr`);
  await p.waitForFunction(() => !document.querySelector('#read').disabled);
  await p.setInputFiles('#image', {name: 'redline.png', mimeType: 'image/png', buffer: Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl6FoAAAAAASUVORK5CYII=', 'base64')});
  await p.click('#read'); await p.waitForSelector('.reading');
  await p.locator('.reading textarea').first().fill(JSON.stringify({path: 'units.V-201.U_W_m2K', value: 2600}));
  await p.click('#confirm'); await p.waitForFunction(() => !document.querySelector('#check').disabled);
  await p.click('#check'); await p.waitForSelector('#comparison:not([hidden])');
  const redlineOk = await p.evaluate(() => document.querySelectorAll('.reading').length === 2 &&
    document.querySelector('#items').textContent.includes('needs its own limits') && document.querySelectorAll('.column-title').length === 2 &&
    document.querySelector('#rows .pass') && document.querySelector('#rows .fail') && document.querySelector('#rows .open') && /Target holds/.test(document.querySelector('#rows').textContent) &&
    /Vendor curve needed/.test(document.querySelector('#rows').textContent) && document.querySelector('#preview').naturalWidth > 0 &&
    getComputedStyle(document.body).colorScheme === 'dark' && getComputedStyle(document.body).backgroundColor === 'rgb(21, 25, 31)');
  const confirmedEdit = redlineConfirmation?.items?.length === 1 && redlineConfirmation.items[0].change.value === 2600;
  await p.setViewportSize({width: 1920, height: 1080});
  await p.screenshot({path: `${OUT}/engineer_redline_stub.png`, fullPage: true});
  await p.setViewportSize({width: 1440, height: 900});
  console.log(redlineOk && confirmedEdit ? 'ok  ' : 'FAIL', 'engineer redline: fake vision read, invalid item, edited confirmation and both design checks');
  bad += redlineOk && confirmedEdit ? 0 : 1;
  const unmappedOk = await p.evaluate(() => {
    renderRead({id: 'unmapped', items: [{index: 0, change: null, ink: 'note', errors: ['change 1 is not an object']}]});
    return !document.querySelector('#items textarea') && document.querySelector('#items').textContent.includes('Not mapped — the ink gave no connections/setpoint') &&
      !document.querySelector('#items').textContent.includes('is not an object') && document.querySelector('#items input').disabled;
  });
  console.log(unmappedOk ? 'ok  ' : 'FAIL', 'unmapped redline ink is plain text, not null JSON'); bad += unmappedOk ? 0 : 1;
  await p.unroute('**/api/plant/salt_mvr/project'); await p.unroute(redlineRoot);
  await p.unroute('**/api/job/redline-smoke'); await p.unroute(`${redlineRoot}/${redlineId}/confirm`); await p.unroute(`${redlineRoot}/${redlineId}/check`);
  await p.goto(`${BASE}/redline.html?case=salt_mvr`);
  await p.waitForSelector('#comparison:not([hidden])', {timeout: 15000}).catch(() => {});
  const savedRedline = await p.evaluate(() => document.querySelector('#preview').naturalWidth > 0 &&
    document.querySelectorAll('.reading').length > 0 && !document.querySelector('#comparison').hidden &&
    /Live reading is off in this demo/.test(document.querySelector('#mode').textContent) && !/WEB_ALLOW_RUNS/.test(document.body.innerText));
  console.log(savedRedline ? 'ok  ' : 'FAIL', 'redline replay preloads saved image, confirmation and comparison without running engines');
  bad += savedRedline ? 0 : 1;
  for (const u of ['home.html', 'plant.html?case=chem_c01', 'plant.html?case=dairy_refrig', 'plant.html?case=salt_mvr', 'plant.html?case=swro_monterey', 'plant.html?case=swro_brownsville', 'plant.html?case=freeport_lng_2022', 'plant.html?case=ucte_2006', 'workspace.html?case=roseburg', 'index.html?case=williams_geismar']) {
    await p.goto(`${BASE}/${u}`); await p.waitForTimeout(u.startsWith('home') ? 2500 : 8000);
    if (u.startsWith('plant.html')) await p.waitForFunction(() => typeof ST !== 'undefined' && ST && document.querySelector('#qaA')?.textContent !== 'Loading the plant…', null, {timeout: 30000}).catch(() => {});
    const stuck = (await p.content()).includes('Loading case data') || (await p.locator('#verdict').count() && (await p.locator('#verdict').innerText()) === 'Case unavailable');
    await p.screenshot({ path: `${OUT}/${u.replace(/[^a-z0-9]+/gi, '_')}.png` });
    console.log(stuck || errs.length ? 'FAIL' : 'ok  ', u, stuck ? 'stuck loading or case unavailable' : '', errs.splice(0).join(' | '));
    bad += stuck ? 1 : 0;
  }
  await p.setViewportSize({width: 1920, height: 1080});
  await p.goto(`${BASE}/plant.html?case=basf_process_column_k_2750_dexpi_c02_uns`);
  await p.waitForSelector('#redteamPanel', {timeout: 30000}).catch(() => {});
  await p.evaluate(() => { openDetails(true); setWorkspaceView('engineering'); });
  const redteamShots = [
    ['trays', '8 / 8 stayed within the modelled process limits', 'redteam_trays_live_design.png'],
    ['600-envelope', '8 / 8 stayed within the modelled process limits', 'redteam_600mm_envelope.png'],
    ['600-harsh', '8 / 8 broke the modelled limits', 'redteam_600mm_125x.png'],
    ['700-robust', '8 / 8 stayed within the modelled process limits', 'redteam_700mm_holds.png']
  ];
  let redteamOk = true;
  for (let i = 0; i < redteamShots.length; i++) {
    await p.evaluate(i => { redteamSet(i); openDetails(true); setWorkspaceView('engineering'); document.querySelector('#redteamPanel')?.scrollIntoView({block: 'start'}); }, i);
    await p.waitForFunction(() => document.body.classList.contains('dd-open'), null, {timeout: 10000});
    await p.waitForTimeout(1350);
    const [id, summary, shot] = redteamShots[i];
    redteamOk = redteamOk && await p.evaluate(({id, summary}) => {
      const panel = document.querySelector('#redteamPanel');
      const expected = id === '600-harsh' ? 3 : 8;
      return document.querySelectorAll('#redteamPanel').length === 1 && panel?.dataset.redteamSet === id && panel.querySelectorAll('.redteam-attack').length === expected &&
        panel.textContent.includes(summary) && panel.querySelectorAll('.redteam-attack a[href]').length >= expected &&
        (expected === 8 || /5 more attacks also broke it.*20261102-194930/.test(panel.querySelector('.redteam-missing')?.textContent)) &&
        [...panel.querySelectorAll('.redteam-attack')].every(card => card.scrollWidth <= card.clientWidth + 1);
    }, {id, summary});
    await p.screenshot({path: `${OUT}/${shot}`});
  }
  redteamOk = redteamOk && await p.evaluate(() => /86\.4%/.test(document.querySelector('#redteamPanel').textContent));
  const redteamErrors = errs.splice(0);
  console.log(redteamOk && !redteamErrors.length ? 'ok  ' : 'FAIL', 'red team: one panel, three sets, missing details grouped and no overflow', redteamErrors.join(' | '));
  bad += redteamOk && !redteamErrors.length ? 0 : 1;
  await p.setViewportSize({width: 1440, height: 900});
  await p.goto(`${BASE}/plant.html?case=salt_mvr`); await p.waitForTimeout(5000);
  const saltStartup = await p.evaluate(() => { const card = document.createElement('div'); card.innerHTML = costConfidence({uncertainty: {p_target: 1, solved: 1}}); return P.has_compressor_curve && !!card.querySelector('#machines button'); });
  const proposedSource = await p.evaluate(() => /Stored DWSIM · proposed design/.test(document.querySelector('#stateSource').textContent));
  await p.goto(`${BASE}/plant.html?case=chem_c01`); await p.waitForTimeout(5000);
  const chemStartup = await p.evaluate(() => { const card = document.createElement('div'); card.innerHTML = costConfidence({uncertainty: {p_target: 1, solved: 1}}); return !P.has_compressor_curve && !card.querySelector('#machines button'); });
  console.log(saltStartup && chemStartup ? 'ok  ' : 'FAIL', 'compressor start-up action only appears with a compressor curve');
  console.log(proposedSource ? 'ok  ' : 'FAIL', 'proposed view labels its stored proposed-design DWSIM state');
  bad += proposedSource ? 0 : 1;
  const noEngineActions = await p.evaluate(() => {
    P.simulator_available = false; P.simulator_unavailable_reason = 'Simulator unavailable in smoke fixture';
    const box = document.createElement('div'); box.innerHTML = '<button data-needs-simulator>Re-solve</button>'; document.body.append(box);
    applyEngineAvailability();
    return box.querySelector('button').disabled && !document.querySelector('#engineUnavailable').hidden && /Simulator unavailable/.test(document.querySelector('#engineUnavailable').textContent);
  });
  console.log(noEngineActions ? 'ok  ' : 'FAIL', 'engine-dependent actions are disabled with a visible reason when no simulator is installed');
  bad += noEngineActions ? 0 : 1;
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
  await p.evaluate(() => { P.allow_runs = true; });  // exercise live confirmation with the fixture; no POST is sent
  await p.click('#workRunOpen');
  const workConfirmOk = await p.evaluate(() => !document.querySelector('#workConfirm').hidden && document.querySelector('#workGoal').value === P.question && /\$5.?10/.test(document.querySelector('.work-runner .estimate').textContent));
  await p.click('#workCancel');
  const worklogOk = await p.evaluate(() => {
    const rounds = [...document.querySelectorAll('.work-round')], actors = [...document.querySelectorAll('.work-actor')].map(x => x.textContent.trim());
    return rounds.length === 2 && !rounds[0].open && rounds[1].open && actors.includes('Muse') && actors.includes('DWSIM') && actors.includes('pandapower') &&
      workActor({actor: 'muse'}, 'baseten:meta-models/muse-spark-open-1026') === 'Muse Spark Open' &&
      !!document.querySelector('[data-work-result]') && !!document.querySelector('.worklog-sample') && /ILLUSTRATIVE SAMPLE/.test(document.querySelector('.worklog-sample').textContent) &&
      /4 human approval items open/.test(document.querySelector('.work-status').textContent) &&
      [...document.querySelectorAll('.work-deliverables a')].some(a => /decision\.pdf$/.test(a.href)) &&
      [...document.querySelectorAll('.work-deliverables a')].some(a => /decision\.zip$/.test(a.href));
  });
  await p.screenshot({ path: `${OUT}/salt_mvr_worklog_sample_1920x1080.png` });
  await p.screenshot({ path: `${OUT}/salt_mvr_replay_1920x1080.png` });
  await p.locator('[data-work-result]').scrollIntoViewIfNeeded();
  await p.screenshot({ path: `${OUT}/salt_mvr_worklog_result_1920x1080.png` });
  const worklogErrors = errs.splice(0);
  console.log(workConfirmOk && worklogOk && replayOk && !worklogErrors.length ? 'ok  ' : 'FAIL', 'engineering run sample: confirmation, replay, rounds, actors and result', worklogErrors.join(' | '));
  bad += workConfirmOk && worklogOk && replayOk && !worklogErrors.length ? 0 : 1;
  await p.goto(`${BASE}/plant.html?case=salt_mvr&present=1&worklog=sample&replay=sample`);
  await p.waitForSelector('#presentCaption:not([hidden])', { timeout: 30000 }).catch(() => {});
  await p.waitForFunction(() => REPLAY.events.length > 0, null, { timeout: 30000 }).catch(() => {});
  const presentOk = await p.evaluate(async () => {
    replayPause(); await replayShow(0);
    const caption = document.querySelector('#presentCaption'), title = document.querySelector('#worklogPanel .work-step-title');
    return document.body.classList.contains('present-mode') && /Muse proposed|DWSIM checked|pandapower checked/.test(document.querySelector('#presentActor').textContent) &&
      parseFloat(getComputedStyle(document.querySelector('#presentText')).fontSize) >= 18 && parseFloat(getComputedStyle(title).fontSize) >= 18 &&
      getComputedStyle(title).overflow === 'visible' && !document.querySelector('#presentText').textContent.endsWith('…') &&
      getComputedStyle(document.querySelector('.agent-log-toggle')).display === 'none' &&
      getComputedStyle(document.querySelector('#workbench')).display === 'none' &&
      getComputedStyle(document.querySelector('#changeSummary')).display === 'none' && getComputedStyle(document.querySelector('#workingRevision')).display === 'none' &&
      document.querySelector('#pidViewport').getBoundingClientRect().bottom <= caption.getBoundingClientRect().top + 1 &&
      parseFloat(getComputedStyle(document.querySelector('#presentChecks .discipline-gate')).fontSize) >= 15;
  });
  await p.screenshot({ path: `${OUT}/video_present_salt_1920x1080.png` });
  console.log(presentOk ? 'ok  ' : 'FAIL', 'presentation mode: large actor caption and untruncated replay step');
  bad += presentOk ? 0 : 1;
  await p.goto(`${BASE}/plant.html?case=shell_norco_c2splitter`);
  await p.waitForFunction(() => document.querySelector('#stateSource')?.textContent.includes('proposed design'), null, {timeout: 30000});
  const norcoOk = await p.evaluate(() => {
    const d = designAnswer(), text = decisionBrief(d, P.answers.indexOf(d));
    return ST.state_source === 'proposed design' && ST.scale === 1.25 && ST.checks.some(c => c.id === 'PV-1767' && Math.abs(c.value - .744) < .001) &&
      /PV-1767/.test(document.querySelector('#verdict').textContent) && /74.4% flood vs 85.0% allowed/.test(document.querySelector('#eqlist').textContent) &&
      !/combined target not yet cleared/.test(text);
  });
  await p.screenshot({path: `${OUT}/norco_proposed_1920x1080.png`});
  console.log(norcoOk ? 'ok  ' : 'FAIL', 'Norco: featured proposed state, flood check and cached gate verdict'); bad += norcoOk ? 0 : 1;
  await p.goto(`${BASE}/scan.html?case=salt_mvr_vision`);
  await p.waitForFunction(() => document.querySelectorAll('[data-read-tag]').length >= 10, null, { timeout: 30000 }).catch(() => {});
  await p.waitForFunction(() => document.querySelector('#scan').naturalWidth > 0 || document.querySelector('.scan-missing'), null, { timeout: 30000 }).catch(() => {});
  const scanOk = await p.evaluate(() => {
    finishScanStory();
    return document.querySelectorAll('[data-read-tag]').length >= 10 && document.querySelectorAll('#corrections li').length === 9 &&
      document.querySelectorAll('.review.fixed').length === 3 && /226\.8 t\/h to K-201/.test(document.querySelector('#counter').textContent) && document.body.dataset.scanPhase === 'done';
  });
  await p.screenshot({ path: `${OUT}/video_scan_to_simulator_1920x1080.png` });
  console.log(scanOk ? 'ok  ' : 'FAIL', 'scan story: stored tags, nine corrections, DWSIM counter and three closed reviews');
  bad += scanOk ? 0 : 1;
  await p.goto(`${BASE}/plant.html?case=ucte_2006&present=1&story=openweights`);
  await p.waitForFunction(() => typeof finishOpenWeightsStory === 'function' && document.querySelector('#storyN1'), null, { timeout: 30000 }).catch(() => {});
  const ucteStoryOk = await p.evaluate(() => {
    finishOpenWeightsStory();
    return /refused 4 attempts/.test(document.querySelector('#openWeightsStory').textContent) && /N-1:\s*0 violations/.test(document.querySelector('#storyN1').textContent) &&
      document.querySelector('#sheet [data-tag="BIO-SPX 220"]')?.classList.contains('story-open') && document.body.dataset.storyPhase === 'done';
  });
  await p.screenshot({ path: `${OUT}/video_ucte_openweights_1920x1080.png` });
  const videoErrors = errs.splice(0);
  console.log(ucteStoryOk && !videoErrors.length ? 'ok  ' : 'FAIL', 'UCTE story: stored refusal count, opened tie and N-1 zero stamp', videoErrors.join(' | '));
  bad += ucteStoryOk && !videoErrors.length ? 0 : 1;
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
  await p.click('[data-workspace-page="evidence"]');
  await p.locator('[data-nrel-parity]').scrollIntoViewIfNeeded();
  await p.screenshot({ path: `${OUT}/nrel_a300_parity_1920x1080.png` });
  console.log(parityOk ? 'ok  ' : 'FAIL', 'NREL A300 parity chart and calibration result replace the empty answer');
  bad += parityOk ? 0 : 1;
  await p.setViewportSize({ width: 1440, height: 900 });
  // the MOC sign-off page: read only here (no signature is written by the smoke test)
  await p.goto(`${BASE}/review.html?case=salt_mvr`); await p.waitForSelector('#block .stamp', { timeout: 15000 }).catch(() => {});
  const signoffOk = await p.evaluate(() => /Draft|Reviewed|Approved|Rejected/.test(document.querySelector('#block .stamp')?.textContent || '') &&
    document.querySelectorAll('#block .cell').length === 3 && document.querySelectorAll('#fails .check').length >= 1 &&
    document.querySelectorAll('#files li').length >= 1 && !!document.querySelector('#pack a[href$="decision.pdf"]') &&
    !!document.querySelector('#pack a[href$="decision.zip"]') && !/None yet/.test(document.body.textContent) &&
    /files frozen for review/.test(document.querySelector('#pack').textContent) && !document.querySelector('.file-list').open &&
    /The transformer would be overloaded: 133 %/.test(document.querySelector('#fails').textContent));
  await p.screenshot({ path: `${OUT}/review_signoff.png`, fullPage: true });
  console.log(signoffOk ? 'ok  ' : 'FAIL', 'MOC sign-off page: approval block, failed checks with dispositions, package files');
  bad += signoffOk ? 0 : 1;
  await p.goto(`${BASE}/home.html`); await p.waitForTimeout(2000);
  await p.waitForFunction(() => !/Loading saved decisions/.test(document.querySelector('#queueDecisions')?.textContent || ''), null, {timeout: 30000}).catch(() => {});
  await p.waitForFunction(() => document.querySelector('#liveRun .runlog-term'), null, {timeout: 10000}).catch(() => {});
  const homeOk = await p.evaluate(() => !document.body.innerHTML.includes('bt_column_debottleneck') &&
    /case=salt_mvr&tour=1/.test(document.querySelector('.hero-actions a').getAttribute('href')));
  const heroEvidence = await p.evaluate(() => { const line = document.querySelector('#openWeightsHero'), links = [...line.querySelectorAll('a')];
    return /refused the UCTE blackout prompt four times/.test(line.textContent) && /0 violations/.test(line.textContent) &&
      links.some(a => /case=ucte_2006/.test(a.href)) && links.some(a => /evidence\/open-weights-engineering\/README.md/.test(a.href)); });
  await p.waitForFunction(() => /model-graded/.test(document.querySelector('#stats')?.textContent || ''), null, {timeout: 20000}).catch(() => {});
  const homePlain = await p.evaluate(() => !document.querySelector('.hero').contains(document.querySelector('#openWeightsHero')) &&
    document.querySelector('.hero .lead').textContent.split(/[.!?]+/).filter(s => s.trim()).length === 2 &&
    /of real engineers' conclusions, blind, model-graded/.test(document.querySelector('#stats').textContent));
  // the hero tells one stored decision in five steps over the real Rev A / Rev B sheets, ending blocked
  await p.waitForFunction(() => document.querySelectorAll('#heroDecision .hd-svg svg').length === 2, null, {timeout: 10000}).catch(() => {});
  const accentSystem = await p.evaluate(() => getComputedStyle(document.querySelector('.hero-actions .go')).backgroundColor === 'rgb(16, 44, 12)' &&
    document.querySelectorAll('#heroDecision .hd-step').length === 5 && document.querySelectorAll('#heroDecision .hd-svg svg').length === 2 &&
    document.querySelectorAll('#heroDecision .hd-step.on').length === 5 && document.querySelector('#heroDecision').classList.contains('blocked') &&
    /45 % → 133 %/.test(document.querySelector('#heroDecision').textContent) && /Draft blocked/.test(document.querySelector('#heroDecision').textContent) &&
    /Approval blocked/.test(document.querySelector('.hd-compare')?.textContent || '') &&
    document.querySelectorAll('#hero-title span').length === 2 && !document.querySelector('.case-story') && !document.querySelector('.featured-run') &&
    /Muse is wrong twice/.test(document.querySelector('#liveRun')?.textContent || '') &&
    document.querySelectorAll('.model-stack-body .model-rail article').length === 4 && document.querySelector('.model-brand img')?.naturalWidth > 0 &&
    document.querySelector('.queue-shell #engineeringQueue'));
  const queueOk = await p.evaluate(() => document.querySelectorAll('#queueCounts .queue-count').length === 3 &&
    document.querySelectorAll('#queueDecisions .queue-item').length > 0 && !/owner:|due today|last data|updated .* ago/i.test(document.querySelector('.queue-columns').textContent));
  await p.goto(`${BASE}/home.html?present=1`); await p.waitForTimeout(500);
  const homePresent = await p.evaluate(() => document.body.classList.contains('presentation-home') && getComputedStyle(document.querySelector('#engineeringQueue')).display === 'none');
  console.log(homeOk && heroEvidence && homePlain && accentSystem && queueOk && homePresent ? 'ok  ' : 'FAIL', 'home: one brand accent, semantic status colours, real queue and clean presentation mode');
  bad += homeOk && heroEvidence && homePlain && accentSystem && queueOk && homePresent ? 0 : 1;
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
  await p.waitForFunction(() => ST && document.querySelector('[data-workspace-page][aria-current="page"]')?.dataset.workspacePage === 'overview');
  const startsFocused = await p.evaluate(() => !document.querySelector('#infoDrawer').classList.contains('open') &&
    document.querySelector('#inspectorTitle').textContent === 'Decision' && document.querySelector('#scenario').hidden === false &&
    getComputedStyle(document.body).getPropertyValue('--act').trim() === '#102c0c');
  await p.click('[data-workspace-page="sources"]'); const sourcesFocused = await p.evaluate(() =>
    document.body.classList.contains('workspace-page-sources') && getComputedStyle(document.querySelector('#sourcesWorkspace')).display !== 'none' &&
    !document.querySelector('#infoDrawer').classList.contains('open'));
  await p.click('[data-workspace-page="health"]');
  const troubleshootFocused = await p.evaluate(() => document.querySelector('#inspectorTitle').textContent === 'Troubleshoot' && document.querySelector('#scenario').hidden);
  await p.click('[data-workspace-page="overview"]');
  await p.locator('#sheet [data-tag="H1007"]').evaluate(e => e.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, button: 0 })));
  await p.locator('#sheet [data-tag="H1007"]').evaluate(e => e.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, button: 0 })));
  await p.waitForFunction(() => document.querySelector('#inspectorTitle').textContent === 'Equipment', null, { timeout: 15000 }).catch(() => {});
  const equipmentFocused = await p.evaluate(() => document.querySelector('#inspectorTitle').textContent === 'Equipment' &&
    document.body.classList.contains('dd-open') && document.querySelector('#detailTitle').textContent === 'Equipment detail' && !document.querySelector('#answers').hidden);
  console.log(startsFocused && sourcesFocused && troubleshootFocused && equipmentFocused ? 'ok  ' : 'FAIL', 'one left workspace panel for sources and modes; secondary equipment detail still opens separately');
  bad += startsFocused && sourcesFocused && troubleshootFocused && equipmentFocused ? 0 : 1;
  await p.click('.inspector-back');
  const readableAnswer = await p.evaluate(() => {
    LAST_WORK = {needs_human: ['Confirm the cooling-water measurement']};
    P.answers = [{ request: 'Reach 120%', headline: 'One verified change is required', summary: 'Test summary', seconds: 1, cost_usd: 0,
      highlights: [{ tag: 'H1007', severity: 'fail', text: 'Cooling duty reaches its limit.' }],
      disciplines: [{ id: 'process', status: 'pass', summary: 'Target solve passes', source: 'DWSIM target solve', checks: [{ check: 'capacity', result: 'pass' }] },
        { id: 'electrical', status: 'fail', summary: 'Transformer overloads on start', source: 'pandapower load flow', checks: [{ check: 'starting voltage', value: 0.82, limit: 0.9 }] }],
      field_checks: [{ item: 'Cooling-water flow', where: 'Check the supply header', changes: 'A low reading changes the recommendation.' }],
      proposals: [{ title: 'Restore cooling-water flow', tag: 'H1007', fixes: 'H1007', cost_class: 'no capex', verified: true,
        changes: [{ path: 'units.H1007.duty_kW', value: 1 }], electrical: { summary: 'TX-47 68 → 70 % loaded; all electrical checks within limits', svg: '/x.svg', over: [] } }], cards: [{ title: 'Duty check', result: 'Within limit', inputs: [] }], checks: [] }];
    answers();
    return !!document.querySelector('.decision-brief') && proposedDraft()?.proposal?.changes?.length === 1 && document.querySelector('#vProposed').textContent === 'Working revision' &&
      !document.querySelector('#workingRevision').hidden && /Draft design/.test(document.querySelector('#workingRevision').textContent) && /1 human decision open/.test(document.querySelector('#workingRevision').textContent) &&
      !!document.querySelector('#adoptProposed') && getComputedStyle(document.querySelector('.engineering-detail')).display === 'none' &&
      document.querySelectorAll('.discipline-gate').length === GATE_ORDER.length && document.body.textContent.includes('Not checked: needs') && !!document.querySelector('.package-action') &&
      !!document.querySelector('.field-check') && !document.querySelector('.field-checks table') && !!document.querySelector('.prop-actions') && /TX-47/.test(document.querySelector('.electrical-line')?.textContent || '');
  });
  await p.screenshot({ path: `${OUT}/decision_workspace.png` });
  const decisionSeparated = await p.evaluate(() => getComputedStyle(document.querySelector('.work-runner')).display === 'none' &&
    !document.querySelector('.decision-question').open && document.querySelectorAll('#runStory .run-story-line').length === 4 &&
    [...document.querySelectorAll('#runStory .run-story-line b')].map(e => e.textContent).join('|') === 'Target|Bottleneck|Recommendation|Result' &&
    getComputedStyle(document.querySelector('#qaBadges')).display === 'none' && getComputedStyle(document.querySelector('#spend')).display === 'none' &&
    (P.allow_runs ? getComputedStyle(document.querySelector('#askDock')).display === 'grid' : getComputedStyle(document.querySelector('#askDock')).display === 'none'));
  await p.click('[data-workspace-page="run"]');
  const runSeparated = await p.evaluate(() => getComputedStyle(document.querySelector('.work-runner')).display !== 'none' && getComputedStyle(document.querySelector('#qa')).display === 'none' &&
    getComputedStyle(document.querySelector('#sourcesWorkspace')).display === 'none');
  await p.click('[data-workspace-page="evidence"]');
  const engineeringView = await p.evaluate(() => getComputedStyle(document.querySelector('.engineering-detail')).display !== 'none' &&
    document.querySelector('#inspectorTitle').textContent === 'Evidence' && !document.body.classList.contains('dd-open') &&
    getComputedStyle(document.querySelector('#resultPane')).display !== 'none' && document.querySelectorAll('#evidenceSummary .evidence-metrics > div').length === 4);
  await p.screenshot({ path: `${OUT}/engineering_workspace.png` });
  await p.click('.discipline-gate.fail');
  const gateEvidence = await p.evaluate(() => document.querySelector('#modal').classList.contains('on') && /pandapower/.test(document.querySelector('#modalBox').textContent));
  await p.evaluate(() => document.querySelector('#modal').classList.remove('on'));
  await p.click('[data-workspace-page="overview"]');
  await p.click('[data-workspace-page="drawing"]');
  const focusOn = await p.evaluate(() => document.body.classList.contains('workspace-page-drawing') && getComputedStyle(document.querySelector('aside.right')).display === 'none' &&
    document.querySelector('main').getBoundingClientRect().left < 100 && !document.querySelector('#changeSummary').hidden &&
    /What changed/.test(document.querySelector('#changeSummary').textContent) && document.querySelectorAll('#changeSummary .change-summary-row').length === 1);
  await p.screenshot({ path: `${OUT}/drawing_focus.png` });
  await p.click('[data-workspace-page="overview"]');
  const focusOff = await p.evaluate(() => !document.body.classList.contains('workspace-page-drawing') && getComputedStyle(document.querySelector('aside.right')).display !== 'none');
  await p.keyboard.press('d');
  const detailShortcut = await p.evaluate(() => document.querySelector('#engineeringView').getAttribute('aria-pressed') === 'true');
  await p.keyboard.press('d');
  await p.keyboard.press('l');
  const labelsShortcut = await p.evaluate(() => document.querySelector('#pidViewport').classList.contains('labels-off'));
  await p.keyboard.press('l');
  await p.click('[data-workspace-page="package"]');
  const packageSeparated = await p.evaluate(() => getComputedStyle(document.querySelector('.package-tools')).display !== 'none' &&
    getComputedStyle(document.querySelector('#redlineLink')).display !== 'none' && document.querySelector('.package-tools').getBoundingClientRect().height > 0 &&
    getComputedStyle(document.querySelector('#answers')).display === 'none' && !!document.querySelector('#packageIssue') && !!document.querySelector('#packageReview') &&
    document.querySelectorAll('#packageFlow .package-step').length === 3 && !document.querySelector('#ddOpen') && document.querySelector('#inspectorTitle').textContent === 'Engineering package' && !document.body.classList.contains('dd-open'));
  await p.click('[data-workspace-page="overview"]');
  const actionHierarchy = await p.evaluate(() => [...document.querySelectorAll('.rail-group-label')].map(e => e.textContent).join('|') === 'Change|Operate|Data' &&
    [...document.querySelectorAll('[data-workspace-page="run"] span')].some(e => e.textContent === 'Checks') && !document.querySelector('#workspaceActions').hidden &&
    getComputedStyle(document.querySelector('.decision-actions')).display === 'none' && /Show on drawing/.test(document.querySelector('#workspaceActions').textContent) && /Review/.test(document.querySelector('#workspacePrimary').textContent));
  const workspaceUi = readableAnswer && decisionSeparated && runSeparated && engineeringView && gateEvidence && packageSeparated && focusOn && focusOff && detailShortcut && labelsShortcut && actionHierarchy;
  console.log(workspaceUi ? 'ok  ' : 'FAIL', 'decision, checks, evidence and package use one page-level action hierarchy', workspaceUi ? '' : JSON.stringify({readableAnswer, decisionSeparated, runSeparated, engineeringView, gateEvidence, packageSeparated, focusOn, focusOff, detailShortcut, labelsShortcut, actionHierarchy}));
  bad += workspaceUi ? 0 : 1;
  await p.evaluate(() => openDetails(false));
  await p.keyboard.press('/');  // the shared command line is available without opening another page
  if (await p.evaluate(() => P.allow_runs)) await p.waitForFunction(() => document.activeElement === document.querySelector('#q'), null, { timeout: 5000 }).catch(() => {});
  const askOpen = await p.evaluate(() => !document.body.classList.contains('dd-open') &&
    (P.allow_runs ? document.activeElement === document.querySelector('#q') : getComputedStyle(document.querySelector('#askDock')).display === 'none'));
  const whatIfFloats = await p.evaluate(() => !document.body.classList.contains('dd-open') && !document.querySelector('#scenario').hidden &&
    getComputedStyle(document.querySelector('#workbench')).position === 'absolute');
  console.log(askOpen && whatIfFloats ? 'ok  ' : 'FAIL', 'shared ask command stays out of the page content; what-if floats on the drawing');
  bad += askOpen && whatIfFloats ? 0 : 1;
  const failureClearsStory = await p.evaluate(() => {
    document.querySelector('#qaBadges').innerHTML = '<span>stale pass</span>';
    document.querySelector('#runStory').textContent = 'stale recommendation';
    showLoadFailure(new Error('smoke fixture'));
    return !document.querySelector('#qaBadges').textContent && !document.querySelector('#runStory').textContent &&
      document.querySelector('.decision-actions').hidden && document.querySelector('.work-runner').hidden && document.querySelector('#askDock').hidden;
  });
  console.log(failureClearsStory ? 'ok  ' : 'FAIL', 'load failure clears stale recommendation and actions');
  bad += failureClearsStory ? 0 : 1;
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
  const blockedIsReadOnly = await p.evaluate(() => {
    const issueButtons = [...document.querySelectorAll('button')].filter(b => /decision file|engineering package/i.test(b.textContent));
    return Number(P?.built?.review?.blocking || 0) > 0 && !document.querySelector('#answers .prop-actions') &&
      issueButtons.length > 0 && issueButtons.every(b => b.disabled);
  });
  console.log(blockedIsReadOnly ? 'ok  ' : 'FAIL', 'blocked model cannot apply proposals or issue a pack');
  bad += blockedIsReadOnly ? 0 : 1;
  await p.goto(`${BASE}/plant.html?case=salt_mvr`); await p.waitForTimeout(5000);
  await p.click('[data-workspace-page="health"]'); await p.waitForTimeout(800);
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
  // Judge-size regressions: every tour target is visible and the popover leaves it unobstructed.
  for (const viewport of [{width: 1600, height: 1000}, {width: 1920, height: 1080}]) {
    await p.setViewportSize(viewport);
    await p.goto(`${BASE}/plant.html?case=salt_mvr&tour=1`); await p.waitForFunction(() => !!P?.built && TOUR.length > 0);
    let targetsVisible = true;
    for (let i = 1; i <= 4; i++) {
      await p.evaluate(i => tourGo(i), i); await p.waitForTimeout(350);
      targetsVisible &&= await p.evaluate(() => {
        const pop = document.querySelector('#tour').getBoundingClientRect();
        return [...document.querySelectorAll('.tour-on')].every(el => {
          const r = el.getBoundingClientRect();
          return r.left >= 0 && r.top >= 0 && r.right <= innerWidth + 1 && r.bottom <= innerHeight + 1 &&
            (pop.right <= r.left || pop.left >= r.right || pop.bottom <= r.top || pop.top >= r.bottom);
        });
      });
    }
    const chips = await p.evaluate(() => !tourGateRow.hidden && /Process ✓/.test(tourGateRow.textContent) && /Electrical ✕ TX-1 133 %/.test(tourGateRow.textContent) &&
      tourGateRow.getBoundingClientRect().top >= document.querySelector('#viewTog').getBoundingClientRect().bottom + 8);
    await p.screenshot({path: `${OUT}/cold_judge_tour_${viewport.width}x${viewport.height}.png`});
    console.log(targetsVisible && chips ? 'ok  ' : 'FAIL', `guided tour targets and discipline chips at ${viewport.width}x${viewport.height}`);
    bad += targetsVisible && chips ? 0 : 1;
  }
  await p.goto(`${BASE}/plant.html?case=shell_norco_c2splitter`); await p.waitForSelector('.norco-column');
  await p.waitForFunction(() => ST && document.querySelectorAll('#runStory .run-story-line').length === 4);
  const norcoPlain = await p.evaluate(() => {
    const drawing = document.querySelector('.norco-column');
    return ['Feed', 'Side reboiler', 'Pasteurization', 'product draw', 'condenser'].every(t => drawing.textContent.toLowerCase().includes(t.toLowerCase())) &&
      !!document.querySelector('.outcome-compare') && !document.querySelector('#note details').open &&
      document.querySelectorAll('#runStory .run-story-line').length === 4 && !document.querySelector('#chatThread').classList.contains('show-log') &&
      ![...document.querySelectorAll('#chatThread > .chat-turn, #chatThread > .chat-earlier')].some(el => el.getClientRects().length);
  });
  await p.click('[data-workspace-page="run"]');
  await p.click('.agent-log-toggle');
  const logOpens = await p.evaluate(() => document.querySelector('#chatThread').classList.contains('show-log'));
  console.log(norcoPlain && logOpens ? 'ok  ' : 'FAIL', 'Norco sections, comparison, four-line story and opt-in raw agent log');
  bad += norcoPlain && logOpens ? 0 : 1;
  await p.goto(`${BASE}/plant.html?case=basf_process_column_k_2750_dexpi_c02_uns`); await p.waitForFunction(() => V.scale > V.fit * 1.2);
  const basfReadable = await p.evaluate(() => !sheet.classList.contains('has-selection') && getComputedStyle(sheet.querySelector('[data-tag="K 2750"]')).opacity === '1');
  console.log(basfReadable ? 'ok  ' : 'FAIL', 'BASF opens zoomed to its column and clearing selection restores full contrast');
  bad += basfReadable ? 0 : 1;
  await p.setViewportSize({width: 1440, height: 900});
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
  // Layout uses a fixed check fixture; saved gate caches can legitimately be absent/stale on a clone.
  await p.goto(`${BASE}/plant.html?case=salt_mvr`); await p.waitForFunction(() => !!P?.built);
  const railFits = await p.evaluate(async () => {
    $('answers').innerHTML = disciplineImpact({disciplines: GATE_ORDER.map((id, i) => ({id, status: i < 5 ? 'pass' : 'open', summary: 'Smoke fixture', source: 'ILLUSTRATIVE test row'}))});
    openDetails(true); await new Promise(resolve => requestAnimationFrame(resolve));
    const r = document.querySelector('.discipline-rail');
    return !!r && r.scrollWidth <= r.clientWidth + 1 && document.querySelectorAll('.discipline-gate').length === GATE_ORDER.length && !document.querySelector('.gates-open').open;
  });
  console.log(railFits ? 'ok  ' : 'FAIL', 'sample discipline gates: calculated shown, the rest folded');
  bad += railFits ? 0 : 1;
  // a blind case with a recorded outcome shows the agent and the engineers side by side
  const bv = await (await fetch(`${BASE}/api/plant/swro_brownsville/project`)).json().catch(() => ({}));
  if (bv.outcome) {
    await p.goto(`${BASE}/plant.html?case=swro_brownsville`); await p.waitForFunction(() => P && P.outcome);
    await p.click('[data-workspace-page="evidence"]');
    const shown = await p.waitForSelector('.outcome-compare', { state: 'visible', timeout: 30000 }).then(() => true).catch(() => false);
    console.log(shown ? 'ok  ' : 'FAIL', 'Brownsville compares the agent with the recorded decision');
    bad += shown ? 0 : 1;
  }
  // No paid call: stub the existing ask/job protocol and prove the strip streams steps, focuses the drawing and carries follow-up context.
  const askBodies = [], jobs = {};
  await p.route('**/api/plant/chem_c01/ask', async route => {
    const body = JSON.parse(route.request().postData() || '{}'), id = `chat-stub-${askBodies.length + 1}`;
    askBodies.push(body); jobs[id] = {poll: 0, request: body.text};
    await route.fulfill({json: {job: id}});
  });
  await p.route('**/api/job/chat-stub-*', async route => {
    const id = new URL(route.request().url()).pathname.split('/').pop(), job = jobs[id], poll = job.poll++;
    const answer = {request: job.request, headline: 'Cooling fix verified at the target', summary: 'DWSIM found and verified the cooling limit.',
      model: 'muse-spark-1.3-contributor', cost_usd: .009, seconds: 3,
      highlights: [{tag: 'H1007', severity: 'fail', text: 'H1007 reaches 104% at 120% throughput.'}],
      cards: [{title: 'Cooling duty', result: 'H1007 104% at 120%'}],
      proposals: [{title: 'Restore cooling-water flow', tag: 'H1007', fixes: 'H1007', verified: true, changes: [{path: 'units.H1007.duty_kW', value: 1}]}]};
    if (id.endsWith('-1') && poll === 0) return route.fulfill({json: {done: false, offset: 1, model: answer.model, seconds: 1, cost_usd: .003,
      events: [{kind: 'tool', name: 'read_pid', summary: '11 equipment items', tags: ['H1007'], status: 'info'}]}});
    if (id.endsWith('-1') && poll === 1) return route.fulfill({json: {done: false, offset: 2, model: answer.model, seconds: 2, cost_usd: .006,
      events: [{kind: 'tool', name: 'run_process', label: 'scale 1.2', summary: 'H1007 104% ✕', tags: ['H1007'], status: 'fail'}]}});
    await route.fulfill({json: {done: true, offset: id.endsWith('-1') ? 2 : 0, model: answer.model, seconds: 3, cost_usd: .009, events: [], answer}});
  });
  await p.goto(`${BASE}/plant.html?case=chem_c01`); await p.waitForSelector('#sheet [data-tag="H1007"]');
  await p.click('[data-workspace-page="run"]');
  await p.evaluate(() => { P.allow_runs = true; document.querySelector('#askDock').classList.remove('ask-replay-only'); document.querySelector('#q').disabled = false; document.querySelector('#askBtn').disabled = false; document.querySelector('#askBtn').textContent = 'Ask'; });
  await p.fill('#q', 'Check H1007 at 120%'); await p.click('#askBtn');
  await p.waitForSelector('#chatThread > .chat-turn:last-child .chat-answer', {state: 'visible', timeout: 15000});
  const liveChat = await p.evaluate(() => {
    const turn = document.querySelector('#chatThread > .chat-turn:last-child'), actors = [...turn.querySelectorAll('.chat-actor')].map(x => x.textContent);
    return actors.includes('Muse') && actors.includes('DWSIM') && document.querySelector('#sheet [data-tag="H1007"]').classList.contains('chat-fail') &&
      /Muse Spark.*\$0\.009.*3s/.test(turn.querySelector('.chat-meta').textContent) && /Cooling fix verified/.test(turn.querySelector('.chat-answer').textContent);
  });
  await p.screenshot({path: `${OUT}/engineering_chat_stub_1920x1080.png`});
  await p.getByRole('button', {name: 'Ask a follow-up'}).last().click(); await p.fill('#q', 'What field reading would change that?'); await p.click('#askBtn');
  await p.waitForTimeout(1200);
  const followContext = askBodies.length === 2 && Number.isInteger(askBodies[1].context?.answer) && askBodies[1].context?.headline === 'Cooling fix verified at the target';
  console.log(liveChat && followContext ? 'ok  ' : 'FAIL', 'engineering chat: streamed actors, drawing focus, answer provenance and follow-up context');
  bad += liveChat && followContext ? 0 : 1;
  await p.unroute('**/api/plant/chem_c01/ask'); await p.unroute('**/api/job/chat-stub-*');
  await b.close(); process.exit(bad || errs.length ? 1 : 0);
})();
