// Landing hero: one plant decision, told in five steps from the stored salt MVR decision pack.
// Numbers come from runs/ws/salt_mvr/decision-20261031-193447/decision.json (limits, capacity, revisions) and
// runs/ws/salt_mvr/gates.json (TX-1 45 -> 133 % loaded); the drawings are that pack's Rev A and Rev B SVGs, cropped to the
// compressor area. Loops while visible; prefers-reduced-motion shows the final step.
(() => {
  const host = document.getElementById('heroDecision');
  if (!host) return;
  const CROP = '112 -304 300 169';   // 16:9 window on the 429 x 367 sheet: K-201, K-202, D-201 and the top of V-201
  const STEPS = [
    {who: 'Engineer', cls: 'ask', text: 'Can this plant make <b>20 % more</b>?', sheet: 'a', ring: 'K-201'},
    {who: 'DWSIM', cls: 'fail', text: 'Today\'s plant at +20 %: compressor K-201 at <b>120 %</b> of its rating', sheet: 'a', ring: 'K-201'},
    {who: 'Muse', cls: 'muse', text: 'Clean heater E-201 · add parallel compressor <b>K-202</b> · trim purge steam', sheet: 'b', ring: 'K-202'},
    {who: 'DWSIM', cls: 'pass', text: 'Process re-solved: <b>100 % → 120 %</b> ✓', sheet: 'b', ring: null},
    {who: 'pandapower', cls: 'fail', text: 'The change would overload the plant transformer: TX-1 <b>45 % → 133 %</b> ✕', sheet: 'b', ring: null},
  ];
  host.innerHTML = `
    <div class="hd-sheet" aria-hidden="true"><div class="hd-svg" data-sheet="a"></div><div class="hd-svg" data-sheet="b"></div>
      <span class="hd-tag" id="hdTag"></span></div>
    <ol class="hd-steps">${STEPS.map((s, i) => `<li class="hd-step ${s.cls}" data-i="${i}"><span class="hd-who">${s.who}</span><span class="hd-text">${s.text}</span></li>`).join('')}</ol>
    <div class="hd-verdict"><b>Draft blocked</b><span>An engineer must resolve the transformer before approval · TX-1 rating is illustrative</span></div>`;
  const svgs = {};
  Promise.all(['a', 'b'].map(k => fetch(`img/salt_rev_${k}.svg`).then(r => r.text()).then(t => {
    const box = host.querySelector(`.hd-svg[data-sheet="${k}"]`); box.innerHTML = t;
    const svg = box.querySelector('svg'); svg.setAttribute('viewBox', CROP); svg.removeAttribute('width'); svg.removeAttribute('height');
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet'); svgs[k] = svg;
  }))).then(start).catch(() => host.classList.add('hd-static'));

  function ring(sheet, tag) {
    host.querySelectorAll('.hd-ring').forEach(e => e.remove());
    const svg = svgs[sheet], el = tag && svg && (svg.getElementById(tag) || svg.querySelector(`[data-tag="${tag}"]`));
    if (!el) return;
    const b = el.getBBox(), r = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    Object.entries({x: b.x - 4, y: b.y - 4, width: b.width + 8, height: b.height + 8, rx: 4, class: 'hd-ring'}).forEach(([k, v]) => r.setAttribute(k, v));
    svg.append(r);
  }
  function show(i) {
    const s = STEPS[i];
    host.querySelectorAll('.hd-step').forEach((li, k) => { li.classList.toggle('on', k <= i); li.classList.toggle('now', k === i); });
    host.querySelectorAll('.hd-svg').forEach(b => b.classList.toggle('on', b.dataset.sheet === s.sheet));
    ring(s.sheet, s.ring);
    host.classList.toggle('blocked', i === STEPS.length - 1);
  }
  function start() {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) { show(STEPS.length - 1); return; }
    host.classList.add('hd-first');
    show(STEPS.length - 1); // Let a quick visitor read the outcome before replaying how the engines reached it.
    setTimeout(() => host.classList.remove('hd-first'), 1000);
    let i = 0, timer = null, visible = true, first = true;
    const tick = () => { show(i); const hold = i === STEPS.length - 1 ? 4200 : 2200; i = (i + 1) % STEPS.length; timer = setTimeout(() => visible && tick(), hold); };
    new IntersectionObserver(es => {
      visible = es.some(e => e.isIntersecting);
      if (visible && !timer) {
        if (first) { first = false; timer = setTimeout(tick, 3200); }
        else tick();
      }
      if (!visible) { clearTimeout(timer); timer = null; }
    }).observe(host);
  }
})();
