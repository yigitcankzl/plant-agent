// Assumptions and inputs: every engineering input value with its source, confirmed or edited by the engineer, plus uploads
// of the engineer's own motor list, vendor curves and data sheets. API: /api/plant/<case>/assumptions, /inputs (assumptions.py).
(() => {
  const CASE_ID = new URLSearchParams(location.search).get('case');
  const body = document.getElementById('ddBody');
  if (!CASE_ID || !body) return;
  const api = p => `/api/plant/${encodeURIComponent(CASE_ID)}/${p}`;
  const h = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
  const LABEL = {documented: 'From documents', datasheet: 'Data sheet', muse_default: 'Muse default', assumed: 'Assumed', engineer_confirmed: 'Confirmed by engineer'};
  const st = document.createElement('style');
  st.textContent = `
  .as-open { display: block; width: calc(100% - 36px); margin: 12px 18px 4px; text-align: left; }
  #asDlg { width: min(920px, 94vw); max-height: 88vh; padding: 0; background: var(--panel, #1c2129); color: var(--text, #d9e0e8); border: 1px solid var(--line, #2e3742); border-radius: 8px; }
  #asDlg::backdrop { background: rgba(0,0,0,.55); }
  #asDlg header { display: flex; align-items: center; gap: 12px; padding: 14px 18px; border-bottom: 1px solid var(--line, #2e3742); position: sticky; top: 0; background: inherit; z-index: 1; }
  #asDlg header h2 { margin: 0; font-size: 16px; flex: 1; }
  #asDlg .as-tabs button[aria-selected="true"] { border-color: var(--accent, #4da3ff); color: var(--accent, #4da3ff); }
  #asDlg section { padding: 14px 18px 18px; }
  #asDlg .as-impact { margin: 0 0 14px; padding: 12px 14px; border: 1px solid var(--line, #2e3742); border-left: 3px solid var(--accent, #4da3ff); border-radius: 6px; background: var(--bg, #15191f); }
  #asDlg .as-impact h3 { margin: 0 0 7px; font-size: 14px; } #asDlg .as-impact ol { margin: 0; padding-left: 25px; }
  #asDlg .as-impact li { padding: 5px 0; border-top: 1px solid var(--line, #2e3742); } #asDlg .as-impact li:first-child { border-top: 0; }
  #asDlg .as-impact code { color: var(--text, #d9e0e8); overflow-wrap: anywhere; } #asDlg .as-impact b { display: block; color: var(--accent, #4da3ff); font-weight: 600; }
  #asDlg .as-sum { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; color: var(--muted, #8592a3); }
  #asDlg .src { display: inline-block; padding: 1px 7px; border-radius: 10px; font-size: 11px; border: 1px solid currentColor; white-space: nowrap; }
  #asDlg .src.documented { color: #8fc1ff; } #asDlg .src.datasheet { color: #7fd1b9; } #asDlg .src.muse_default { color: #c7a6ff; }
  #asDlg .src.assumed { color: var(--warn, #e3a33a); } #asDlg .src.engineer_confirmed { color: var(--ok, #3fb67a); }
  #asDlg details { border-top: 1px solid var(--line, #2e3742); padding: 8px 0; }
  #asDlg summary { cursor: pointer; font-weight: 600; }
  #asDlg .as-group-actions { display: flex; justify-content: flex-end; margin: 6px 0 2px; }
  #asDlg table { width: 100%; border-collapse: collapse; margin-top: 6px; font-size: 12.5px; }
  #asDlg td { padding: 4px 6px; vertical-align: middle; } #asDlg td.l { width: 42%; word-break: break-word; }
  #asDlg td.n { color: var(--muted, #8592a3); font-size: 11.5px; }
  #asDlg input[type=number] { width: 110px; background: var(--bg, #15191f); color: inherit; border: 1px solid var(--line, #2e3742); border-radius: 4px; padding: 3px 6px; }
  #asDlg pre { background: var(--bg, #15191f); padding: 8px; border-radius: 4px; overflow-x: auto; font-size: 12px; }
  #asDlg .tpl { border-top: 1px solid var(--line, #2e3742); padding: 12px 0; }
  #asDlg .msg { min-height: 1.4em; color: var(--muted, #8592a3); }
  #asDlg .msg.err { color: var(--fail, #ef5a4f); }`;
  document.head.appendChild(st);
  body.insertAdjacentHTML('afterbegin', '<button class="btn as-open" id="asOpen" type="button">Assumptions and inputs</button>');
  document.body.insertAdjacentHTML('beforeend', `<dialog id="asDlg" aria-labelledby="asTitle"><header><h2 id="asTitle">Assumptions and inputs</h2>
    <span class="as-tabs" role="tablist"><button class="btn" role="tab" data-t="a" aria-selected="true">Assumptions</button> <button class="btn" role="tab" data-t="i" aria-selected="false">Upload inputs</button></span>
    <button class="btn" id="asClose" type="button" aria-label="Close">✕</button></header>
    <section id="asA"></section><section id="asI" hidden></section></dialog>`);
  const dlg = document.getElementById('asDlg'), A = document.getElementById('asA'), I = document.getElementById('asI');
  let showAll = false, wantSensitivity = false;

  async function loadA() {
    const r = await fetch(api('assumptions') + (wantSensitivity ? '?sensitivity=1' : '')).then(x => x.json());
    if (r.error) { A.innerHTML = `<p class="msg err">${h(r.error)}</p>`; return; }
    const open = r.items.filter(i => i.source !== 'engineer_confirmed' && i.source !== 'documented');
    document.getElementById('asOpen').textContent = `Assumptions and inputs · ${open.length} to confirm`;
    const items = showAll ? r.items : open, files = [...new Set(items.map(i => i.file))];
    const ranked = r.sensitivity?.rows || [];
    A.innerHTML = `${ranked.length ? `<div class="as-impact" id="asTop10"><h3>Top ${ranked.length} that change the answer</h3>
      <ol>${ranked.map(i => `<li><code>${h(i.path)}</code><b>${h(i.change)}</b>${i.check ? `<span class="n">${h(i.check)}</span>` : ''}</li>`).join('')}</ol>
      <p class="msg">${h(r.sensitivity.note || r.sensitivity.method || '')}</p></div>` : (wantSensitivity && r.sensitivity?.note ? `<p class="msg">${h(r.sensitivity.note)}</p>` : '')}
      <div class="as-sum">${Object.entries(r.summary).filter(([, n]) => n).map(([s, n]) => `<span><span class="src ${s}">${LABEL[s]}</span> ${n}</span>`).join('')}</div>
      <p class="msg">Each value the engines use, with where it came from. Confirm what is right, type a new value where it is not; every change is logged.
      <label><input type="checkbox" id="asAll" ${showAll ? 'checked' : ''}> show documented and confirmed values too</label></p>
      ${files.length ? '' : '<p>No values need confirming. Upload a motor list or vendor curve, or show all values.</p>'}
      ${files.map(f => { const rows = items.filter(i => i.file === f), pending = rows.filter(i => i.source !== 'engineer_confirmed' && i.source !== 'documented'); return `<details ${files.length < 4 ? 'open' : ''}><summary>${h(f)} · ${rows.length}</summary>
        ${pending.length ? `<div class="as-group-actions"><button class="btn" type="button" data-bulk="${h(f)}">Confirm all ${pending.length} in this group</button></div>` : ''}<table>${rows.map(i => `
        <tr data-id="${h(i.id)}" data-pending="${i.source !== 'engineer_confirmed' && i.source !== 'documented' ? '1' : '0'}"><td class="l">${h(i.label)}</td><td><input type="number" step="any" value="${h(i.value)}" aria-label="${h(i.label)}"> ${h(i.unit || '')}</td>
        <td><span class="src ${i.source}" title="${h(i.note || '')}">${LABEL[i.source]}</span></td>
        <td><button class="btn" type="button" data-act="ok">${i.source === 'engineer_confirmed' ? 'Confirmed' : 'Confirm'}</button></td></tr>
        ${i.note ? `<tr><td class="n" colspan="4">${h(i.note)}</td></tr>` : ''}`).join('')}</table></details>`; }).join('')}`;
    document.getElementById('asAll').onchange = e => { showAll = e.target.checked; loadA(); };
  }
  A.addEventListener('click', async e => {
    const bulk = e.target.closest('button[data-bulk]');
    if (bulk) {
      const box = bulk.closest('details'), rows = [...box.querySelectorAll('tr[data-id][data-pending="1"]')];
      const invalid = rows.map(tr => tr.querySelector('input')).find(inp => inp.value === '' || !Number.isFinite(Number(inp.value)));
      if (invalid) { invalid.setCustomValidity('Enter a number'); invalid.reportValidity(); return; }
      const values = rows.map(tr => ({id: tr.dataset.id, value: Number(tr.querySelector('input').value)}));
      if (!confirm(`Confirm all ${values.length} values in ${bulk.dataset.bulk} at their current values? Each value will be logged separately.`)) return;
      bulk.disabled = true;
      const r = await fetch(api('assumptions'), {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({items: values})})
        .then(x => x.json()).catch(() => ({error: 'the server did not answer'}));
      if (r.error) { bulk.disabled = false; bulk.textContent = 'Retry bulk confirmation'; bulk.title = r.error; return; }
      loadA(); return;
    }
    const b = e.target.closest('button[data-act]'), tr = e.target.closest('tr[data-id]');
    if (!b || !tr) return;
    const inp = tr.querySelector('input'), v = Number(inp.value);
    if (inp.value === '' || !Number.isFinite(v)) { inp.setCustomValidity('Enter a number'); inp.reportValidity(); return; }
    b.disabled = true;
    const r = await fetch(api('assumptions'), {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({id: tr.dataset.id, value: v})})
      .then(x => x.json()).catch(() => ({error: 'the server did not answer'}));
    if (r.error) { b.disabled = false; b.textContent = 'Retry'; b.title = r.error; return; }
    loadA();
  });

  async function loadI() {
    const r = await fetch(api('inputs')).then(x => x.json());
    I.innerHTML = `<p class="msg">Your own data replaces the assumed values. Each file is checked against its columns before it is stored with the project.</p>
      ${Object.entries(r.templates).map(([k, t]) => `<div class="tpl" data-k="${k}"><b>${h(t.title)}</b> <span class="msg">(${t.format})</span>
        <p>${h(t.use)}</p>${t.required.length ? `<p>Columns: <b>${t.required.map(h).join(', ')}</b>${t.optional.length ? `; optional ${t.optional.map(h).join(', ')}` : ''}</p>` : ''}
        ${t.example ? `<pre>${h(t.example)}</pre><a class="btn" download="${k}_template.csv" href="data:text/csv;charset=utf-8,${encodeURIComponent(t.example)}">Download template</a>` : ''}
        <input type="file" accept="${t.format === 'PDF' ? '.pdf' : '.csv'}" aria-label="${h(t.title)} file"> <button class="btn go" type="button">Upload ${h(t.title.toLowerCase())}</button>
        <div class="msg" role="status"></div></div>`).join('')}
      ${r.files.length ? `<p>Stored with this project: ${r.files.map(h).join(', ')}</p>` : ''}`;
  }
  I.addEventListener('click', async e => {
    const b = e.target.closest('button'), box = e.target.closest('.tpl');
    if (!b || !box) return;
    const f = box.querySelector('input[type=file]').files[0], msg = box.querySelector('.msg[role=status]');
    if (!f) { msg.className = 'msg err'; msg.textContent = 'Choose a file first.'; return; }
    msg.className = 'msg'; msg.textContent = 'Checking…';
    const r = await fetch(api('inputs') + '?kind=' + box.dataset.k, {method: 'POST', headers: {'Content-Type': 'application/octet-stream', 'X-Filename': f.name}, body: f})
      .then(x => x.json()).catch(() => ({error: 'the server did not answer'}));
    if (r.error) { msg.className = 'msg err'; msg.textContent = r.error; return; }
    msg.textContent = `Stored as ${r.file}${r.rows ? ` (${r.rows} rows)` : ''}; source: ${LABEL[r.source] || r.source}.`;
    loadA();
  });

  dlg.querySelector('.as-tabs').onclick = e => {
    const t = e.target.closest('[data-t]')?.dataset.t; if (!t) return;
    dlg.querySelectorAll('.as-tabs button').forEach(x => x.setAttribute('aria-selected', String(x.dataset.t === t)));
    A.hidden = t !== 'a'; I.hidden = t !== 'i';
    if (t === 'i') loadI();
  };
  document.getElementById('asOpen').onclick = () => { wantSensitivity = true; dlg.showModal(); loadA(); };
  document.getElementById('asClose').onclick = () => dlg.close();
  loadA().catch(() => {});
})();
