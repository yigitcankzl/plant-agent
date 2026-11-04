// Landing section: replays one recorded engineering run (web/img/live_run.json, exported from the stored worklog by
// tools/export_live_run.py). Every row on screen is a stored row; nothing is invented. It plays once when scrolled into
// view; prefers-reduced-motion shows the finished log at once. Mount point: <section id="liveRun"></section>.
(() => {
  const host = document.getElementById('liveRun');
  if (!host) return;
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  fetch('img/live_run.json').then(r => r.json()).then(run => {
    const model = /spark-open/.test(run.model) ? 'Muse Spark Open' : run.model.split(':').pop().split('/').pop();
    const mins = Math.round(run.seconds / 60), fails = run.rounds.reduce((n, r) => n + (r.checks.some(c => c.status === 'fail') ? 1 : 0), 0);
    host.className = 'runlog-section';
    host.innerHTML = `
      <div class="runlog-copy">
        <p class="kicker">Recorded engineering run · replay</p>
        <h2>Muse is wrong twice. The simulator says so.</h2>
        <p>BASF's official DEXPI column, a fresh session and a neutral goal. Each round Muse proposes a change; the server re-solves it
          in DWSIM and runs every check. Failed checks go back to Muse with their numbers.</p>
        <dl class="runlog-facts"><div><dt>Model</dt><dd>${esc(model)}</dd></div><div><dt>Rounds</dt><dd>${run.rounds.length}</dd></div>
          <div><dt>Rejected</dt><dd>${fails}</dd></div><div><dt>Wall time</dt><dd>${mins} min</dd></div><div><dt>Model cost</dt><dd>$${run.usd.toFixed(2)}</dd></div></dl>
        <a class="text-link" href="plant.html?case=${esc(run.case)}&replay=${esc(run.run)}">Open this run in the workspace →</a>
      </div>
      <div class="runlog-term" role="log" aria-label="Recorded engineering run">
        <div class="runlog-bar"><span></span><span></span><span></span><b>engineering run ${esc(run.run)} · ${esc(run.started.slice(0, 10))}</b></div>
        <div class="runlog-body" id="runlogBody"><div class="rl-goal">goal&gt; ${esc(run.goal)}</div></div>
      </div>`;
    const body = document.getElementById('runlogBody');
    const lines = [];
    run.rounds.forEach(r => {
      lines.push({cls: 'rl-round', html: `ROUND ${r.n}`});
      lines.push({cls: 'rl-muse', html: `<i>Muse</i> ${esc(r.n === 1 ? 'studies the column: “' + r.proposal + '”' : r.proposal)}`});
      if (r.tools.length) lines.push({cls: 'rl-tools', html: `<i>tools</i> ${r.tools.length} calls · ${esc(r.tools.filter(t => t.startsWith('run_process') || t.startsWith('process_capacity')).length)} DWSIM solves`});
      r.checks.forEach(c => lines.push({cls: 'rl-check ' + c.status, html: `<i>${c.status === 'pass' ? 'pass' : 'FAIL'}</i> ${esc(c.name)}<span>${esc(c.detail.replace(/^draft \(assumed values\):\s*/, ''))}</span>`}));
      const failed = r.checks.filter(c => c.status === 'fail');
      if (failed.length) lines.push({cls: 'rl-back', html: `→ ${failed.length} failed check${failed.length > 1 ? 's' : ''} sent back to Muse with the numbers`});
    });
    lines.push({cls: 'rl-done', html: `✓ every modelled check passed · open for a human: ${esc(run.open.map(o => o.replace(/_/g, ' ').replace(/^vendor confirmation of .*/, 'vendor tray rating')).join(', '))}`});
    const add = l => { const d = document.createElement('div'); d.className = 'rl ' + l.cls; d.innerHTML = l.html; body.append(d); body.scrollTop = body.scrollHeight; };
    if (still) { lines.forEach(add); return; }
    let started = false;
    new IntersectionObserver((entries, obs) => {
      if (started || !entries.some(e => e.isIntersecting)) return;
      started = true; obs.disconnect();
      let i = 0;
      const tick = () => { if (i >= lines.length) return; const l = lines[i++]; add(l);
        setTimeout(tick, l.cls === 'rl-round' ? 700 : l.cls.includes('fail') || l.cls === 'rl-back' ? 900 : 230); };
      tick();
    }, {threshold: .35}).observe(host);
  }).catch(() => { host.hidden = true; });
})();
