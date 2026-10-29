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
  await p.waitForTimeout(500);
  const equipmentFocused = await p.evaluate(() => document.querySelector('#inspectorTitle').textContent === 'Equipment' && !document.querySelector('#answers').hidden);
  console.log(startsFocused && drawerOpened && troubleshootFocused && equipmentFocused ? 'ok  ' : 'FAIL', 'focused capacity layout, drawer, modes and equipment inspector');
  bad += startsFocused && drawerOpened && troubleshootFocused && equipmentFocused ? 0 : 1;
  await p.click('.inspector-back');
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
  await p.goto(`${BASE}/plant.html?case=chem_c01&tour=1`); await p.waitForSelector('#tour', { state: 'visible', timeout: 20000 });
  for (let i = 0; i < 6; i++) { await p.waitForTimeout(1200); await p.click('#tourNext'); }
  console.log(errs.length ? 'FAIL' : 'ok  ', 'guided demo, 6 steps', errs.join(' | '));
  await b.close(); process.exit(bad || errs.length ? 1 : 0);
})();
