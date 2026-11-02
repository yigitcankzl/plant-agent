// Browser audit for the README's no-key/no-engine clean-clone claim.
// node tools/clean_clone_audit.js [base_url] [output.json] [screenshot_dir]
let playwright;
try { playwright = require(process.env.PLAYWRIGHT || 'playwright'); }
catch (_) { playwright = require('/home/kizil/.npm/_npx/e41f203b7505f1fb/node_modules/playwright'); }
const fs = require('fs'), path = require('path'), { chromium } = playwright;
const BASE = process.argv[2] || 'http://127.0.0.1:8765';
const OUTPUT = process.argv[3] || '/tmp/clean-clone-audit.json';
const SHOTS = process.argv[4] || '/tmp/clean-clone-audit';

const fixed = [
  ['home', 'home.html'],
  ['salt', 'plant.html?case=salt_mvr'],
  ['salt-tour', 'plant.html?case=salt_mvr&tour=1'],
  ['basf-c02', 'plant.html?case=basf_process_column_k_2750_dexpi_c02_uns'],
  ['salt-vision', 'plant.html?case=salt_mvr_vision'],
  ['ucte', 'plant.html?case=ucte_2006'],
  ['freeport', 'plant.html?case=freeport_lng_2022'],
  ['nrel-a300', 'plant.html?case=nrel_ethanol_a300'],
  ['nrel-a500', 'plant.html?case=nrel_ethanol_a500'],
  ['chem-c01', 'plant.html?case=chem_c01'],
  ['brownsville', 'plant.html?case=swro_brownsville'],
  ['monterey', 'plant.html?case=swro_monterey'],
  ['dairy', 'plant.html?case=dairy_refrig'],
  ['review', 'review.html?case=salt_mvr'],
  ['scan-story', 'scan.html?case=salt_mvr_vision'],
  ['openweights-story', 'plant.html?case=ucte_2006&present=1&story=openweights'],
];

const safe = value => String(value).replace(/[^a-z0-9-]+/gi, '_');

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const cases = await fetch(`${BASE}/api/cases`).then(r => r.json());
  const studies = cases.filter(c => c.runs?.length).map(c => [`study-${c.name}`, `index.html?case=${c.name}`]);
  const browser = await chromium.launch({ headless: true });
  const results = [];
  for (const [name, url] of [...fixed, ...studies]) {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    const consoleErrors = [], pageErrors = [], requestFailures = [], apiFailures = [];
    page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
    page.on('pageerror', error => pageErrors.push(error.message));
    page.on('requestfailed', request => requestFailures.push({ url: request.url(), error: request.failure()?.errorText }));
    page.on('response', response => {
      if (response.url().startsWith(`${BASE}/api/`) && response.status() >= 400)
        apiFailures.push({ url: response.url().slice(BASE.length), status: response.status() });
    });
    let status = 0, navigationError = null;
    try {
      const response = await page.goto(`${BASE}/${url}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
      status = response?.status() || 0;
      await page.waitForTimeout(url.startsWith('plant') || url.startsWith('scan') ? 6500 : 3000);
    } catch (error) { navigationError = error.message; }
    const visible = await page.evaluate(() => {
      const text = document.body?.innerText || '';
      const shown = id => { const e = document.getElementById(id); return e && getComputedStyle(e).display !== 'none'; };
      return {
        title: document.title,
        heading: document.querySelector('h1,h2')?.textContent?.trim() || '',
        verdict: document.querySelector('#verdict')?.textContent?.trim() || '',
        stuck: /Loading case data|Case unavailable|Cases could not be loaded/.test(text),
        notAnswered: /Not answered yet/.test(text),
        replayOnly: /Replay only/.test(text),
        proposedToggle: shown('viewTog'),
        proposedLabel: document.querySelector('#scenarioName')?.textContent?.trim() || '',
        visibleError: [...document.querySelectorAll('#err,.error,.fail')].map(e => e.textContent.trim()).filter(Boolean).slice(0, 8),
        brokenImages: [...document.images].filter(img => img.complete && !img.naturalWidth).map(img => img.currentSrc || img.src),
        bodySample: text.replace(/\s+/g, ' ').slice(0, 500),
      };
    }).catch(error => ({ evaluateError: error.message }));
    await page.screenshot({ path: path.join(SHOTS, `${safe(name)}.png`), fullPage: false }).catch(() => {});
    const hardFailure = navigationError || status >= 400 || pageErrors.length || requestFailures.some(x => x.url.startsWith(`${BASE}/api/`)) || visible.stuck;
    results.push({ name, url, status: hardFailure ? 'fail' : apiFailures.length || consoleErrors.length || visible.brokenImages?.length ? 'warn' : 'pass',
      http_status: status, navigation_error: navigationError, console_errors: consoleErrors, page_errors: pageErrors,
      request_failures: requestFailures, api_failures: apiFailures, visible });
    console.log(`${results.at(-1).status.padEnd(4)} ${url}`);
    await page.close();
  }
  await browser.close();
  const out = { base: BASE, image: 'python:3.12-slim', pages: results,
    summary: Object.fromEntries(['pass', 'warn', 'fail'].map(s => [s, results.filter(r => r.status === s).length])) };
  fs.writeFileSync(OUTPUT, JSON.stringify(out, null, 2) + '\n');
  console.log(JSON.stringify(out.summary));
})().catch(error => { console.error(error); process.exit(1); });
