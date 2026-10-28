// UI smoke test: every page loads in a fresh browser without script errors or a stuck "Loading", and the guided demo runs.
// node tools/ui_smoke.js [base_url] [screenshot_dir]   (Playwright from PLAYWRIGHT or the local npx cache)
const { chromium } = require(process.env.PLAYWRIGHT || '/home/kizil/.npm/_npx/e41f203b7505f1fb/node_modules/playwright');
const BASE = process.argv[2] || 'http://127.0.0.1:8765', OUT = process.argv[3] || '/tmp/pwtest';
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  let bad = 0;
  for (const u of ['home.html', 'plant.html?case=chem_c01', 'plant.html?case=dairy_refrig', 'workspace.html?case=roseburg', 'index.html?case=williams_geismar']) {
    await p.goto(`${BASE}/${u}`); await p.waitForTimeout(u.startsWith('home') ? 2500 : 8000);
    const stuck = (await p.content()).includes('Loading case data');
    await p.screenshot({ path: `${OUT}/${u.replace(/[^a-z0-9]+/gi, '_')}.png` });
    console.log(stuck || errs.length ? 'FAIL' : 'ok  ', u, stuck ? 'stuck loading' : '', errs.splice(0).join(' | '));
    bad += stuck ? 1 : 0;
  }
  await p.goto(`${BASE}/plant.html?case=chem_c01&tour=1`); await p.waitForSelector('#tour', { state: 'visible', timeout: 20000 });
  for (let i = 0; i < 6; i++) { await p.waitForTimeout(1200); await p.click('#tourNext'); }
  console.log(errs.length ? 'FAIL' : 'ok  ', 'guided demo, 6 steps', errs.join(' | '));
  await b.close(); process.exit(bad || errs.length ? 1 : 0);
})();
