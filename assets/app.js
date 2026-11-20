/* 搜索、标签筛选、差异开关、明暗主题、目录高亮。
   内容本身是静态 HTML，没有这个脚本页面依然可以完整阅读。 */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var root = document.documentElement;
  root.classList.remove('no-js');
  root.classList.add('js');

  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) {} return null; }
  var norm = function (s) { return s.normalize('NFKC').toLowerCase(); };

  /* ── 主题 ── */
  var mq = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : { matches: false };
  $('#themeBtn').addEventListener('click', function () {
    var cur = root.getAttribute('data-theme') || (mq.matches ? 'dark' : 'light');
    var next = cur === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next); store('eia-theme', next);
  });

  /* ── 差异开关 ── */
  var diffToggle = $('#diffToggle');
  diffToggle.checked = !root.classList.contains('nodiff');
  diffToggle.addEventListener('change', function () {
    root.classList.toggle('nodiff', !diffToggle.checked);
    store('eia-diff', diffToggle.checked ? 'on' : 'off');
  });

  /* ── 搜索 + 标签筛选 ── */
  var ents = $$('.ent').map(function (el) {
    return { el: el, text: norm(el.textContent), tiers: el.dataset.tiers === undefined ? null : (el.dataset.tiers ? el.dataset.tiers.split(' ') : []) };
  });
  var blocks = $$('.sec, .grp');
  var inputs = $$('[data-search]');
  var status = $('#status'), statusText = $('#statusText'), empty = $('#empty');
  var tierBtns = $$('[data-tier]');
  var state = { q: '', tiers: [] };
  var timer;

  function setStatusHeight() {
    root.style.setProperty('--status-h', status.hidden ? '0px' : status.offsetHeight + 'px');
  }

  function clearMarks(scope) {
    $$('mark.hl', scope).forEach(function (m) {
      var p = m.parentNode; p.replaceChild(document.createTextNode(m.textContent), m); p.normalize();
    });
  }
  function markTerms(el, terms) {
    var w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null), nodes = [], n;
    while ((n = w.nextNode())) nodes.push(n);
    nodes.forEach(function (node) {
      var raw = node.nodeValue, low = '', ok = true;
      for (var i = 0; i < raw.length; i++) { var c = norm(raw[i]); if (c.length !== 1) { ok = false; break; } low += c; }
      if (!ok) return;
      var ranges = [];
      terms.forEach(function (t) { var from = 0, k; while ((k = low.indexOf(t, from)) > -1) { ranges.push([k, k + t.length]); from = k + t.length; } });
      if (!ranges.length) return;
      ranges.sort(function (a, b) { return a[0] - b[0]; });
      var merged = [ranges[0]];
      ranges.slice(1).forEach(function (r) { var l = merged[merged.length - 1]; if (r[0] <= l[1]) l[1] = Math.max(l[1], r[1]); else merged.push(r); });
      var frag = document.createDocumentFragment(), pos = 0;
      merged.forEach(function (r) {
        if (r[0] > pos) frag.appendChild(document.createTextNode(raw.slice(pos, r[0])));
        var m = document.createElement('mark'); m.className = 'hl'; m.textContent = raw.slice(r[0], r[1]); frag.appendChild(m); pos = r[1];
      });
      if (pos < raw.length) frag.appendChild(document.createTextNode(raw.slice(pos)));
      node.parentNode.replaceChild(frag, node);
    });
  }

  function apply() {
    var terms = norm(state.q).split(/\s+/).filter(Boolean);
    var shown = 0, total = ents.length;
    clearMarks(document.getElementById('main'));
    ents.forEach(function (e) {
      var okQ = terms.every(function (t) { return e.text.indexOf(t) > -1; });
      var okT = !state.tiers.length || !e.tiers || state.tiers.some(function (t) { return e.tiers.indexOf(t) > -1; });
      var vis = okQ && okT;
      e.el.hidden = !vis;
      if (vis) { shown++; if (terms.length) markTerms(e.el, terms); }
    });
    var active = terms.length > 0 || state.tiers.length > 0;
    blocks.forEach(function (b) {
      var has = $$('.ent', b).some(function (el) { return !el.hidden; });
      b.hidden = active && !has && !!$('.ent', b);
    });
    empty.hidden = !(active && shown === 0);
    status.hidden = !active;
    if (active) {
      var tiered = ents.filter(function (e) { return e.tiers; });
      var shownT = tiered.filter(function (e) { return !e.el.hidden; }).length;
      var q = '“' + state.q.trim() + '”', t = '含' + state.tiers.join('、') + '标签';
      statusText.textContent = terms.length && state.tiers.length ? q + '，' + t + '：共 ' + shown + ' 条'
        : terms.length ? q + '：显示 ' + shown + ' / ' + total + ' 条'
        : t + '的行业项目：' + shownT + ' / ' + tiered.length + ' 项';
    }
    setStatusHeight();
    spyRefresh();
  }
  function schedule() { clearTimeout(timer); timer = setTimeout(apply, 120); }

  inputs.forEach(function (inp) {
    inp.addEventListener('input', function (e) {
      if (e.isComposing) return;
      state.q = inp.value; inputs.forEach(function (o) { if (o !== inp) o.value = inp.value; }); schedule();
    });
    inp.addEventListener('compositionend', function () {
      state.q = inp.value; inputs.forEach(function (o) { if (o !== inp) o.value = inp.value; }); schedule();
    });
    inp.addEventListener('keydown', function (e) { if (e.key === 'Escape') clearAll(); });
  });
  $$('.suggest [data-q]').forEach(function (b) {
    b.addEventListener('click', function () {
      state.q = b.dataset.q; inputs.forEach(function (i) { i.value = state.q; }); apply();
      $('.shell').scrollIntoView({ block: 'start' });
    });
  });
  tierBtns.forEach(function (b) {
    b.addEventListener('click', function () {
      var on = b.getAttribute('aria-pressed') !== 'true';
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
      state.tiers = tierBtns.filter(function (x) { return x.getAttribute('aria-pressed') === 'true'; }).map(function (x) { return x.dataset.tier; });
      apply();
    });
  });
  function clearAll() {
    state.q = ''; state.tiers = []; inputs.forEach(function (i) { i.value = ''; });
    tierBtns.forEach(function (b) { b.setAttribute('aria-pressed', 'false'); }); apply();
  }
  $('#clearBtn').addEventListener('click', clearAll);

  /* ── 顶栏：首屏搜索框移出视野后，顶栏出现紧凑搜索框 ── */
  var topbar = $('.topbar'), hero = $('#heroSearch');
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (es) { topbar.classList.toggle('show-search', !es[0].isIntersecting); }, { rootMargin: '-60px 0px 0px 0px' }).observe(hero);
  }
  document.addEventListener('keydown', function (e) {
    if (e.key !== '/' || /^(INPUT|TEXTAREA)$/.test(document.activeElement.tagName)) return;
    e.preventDefault();
    var shownTop = topbar.classList.contains('show-search');
    var target = shownTop ? $('.tsearch input') : $('.finder input'); target.focus(); target.select();
  });

  /* ── 目录当前位置 ──
     用 IntersectionObserver 观察各小节标题，滚动期间不跑任何脚本；
     章节标签栏只在“当前章节变化”时横向移动一次，绝不触碰页面本身的滚动。 */
  var links = $$('.side a, .pills a');
  var pillBar = $('.pills');
  var spy = [], above = {}, curId = null, footerSeen = false, spyIO = null, spyLine = 142, spyTimer;
  links.forEach(function (a) {
    var id = a.getAttribute('href').slice(1);
    if (spy.some(function (x) { return x.id === id; })) return;
    var sec = document.getElementById(id), h = sec && sec.querySelector('h2, h3');
    if (h) spy.push({ id: id, sec: sec, h: h });
  });
  function spyRefresh() {
    var cur = null;
    spy.forEach(function (x) { if (above[x.id] && !x.sec.closest('[hidden]')) cur = x.id; });
    if (footerSeen) cur = 's5';
    if (cur === curId) return;
    curId = cur;
    var inGroup = !!cur && cur.charAt(0) === 'g';
    links.forEach(function (a) {
      var id = a.getAttribute('href').slice(1), inPills = !!a.closest('.pills');
      a.setAttribute('aria-current', (id === cur || (inPills && id === 's4' && inGroup)) ? 'true' : 'false');
    });
    var act = pillBar && pillBar.offsetParent !== null && $('a[aria-current="true"]', pillBar);
    if (act) pillBar.scrollTo({ left: act.offsetLeft - (pillBar.clientWidth - act.offsetWidth) / 2, behavior: 'smooth' });
  }
  /* 兜底：整页跳转（点目录、深链）时观察器可能收不到通知，滚动停下后按实际位置量一次 */
  function spyMeasure() {
    spy.forEach(function (x) { above[x.id] = !x.sec.closest('[hidden]') && x.h.getBoundingClientRect().bottom <= spyLine; });
    footerSeen = $('.foot').getBoundingClientRect().top < window.innerHeight;
    spyRefresh();
  }
  window.addEventListener('scroll', function () { clearTimeout(spyTimer); spyTimer = setTimeout(spyMeasure, 120); }, { passive: true });
  function buildSpy() {
    if (!('IntersectionObserver' in window)) return;
    if (spyIO) spyIO.disconnect();
    var line = spyLine = (parseFloat(getComputedStyle(root).getPropertyValue('--top')) || 52) + 90;
    spyIO = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.target.classList.contains('foot')) { footerSeen = e.isIntersecting; return; }
        var x = spy.filter(function (y) { return y.h === e.target; })[0]; if (!x) return;
        above[x.id] = !e.isIntersecting && e.boundingClientRect.top < line;
      });
      spyRefresh();
    }, { rootMargin: '-' + line + 'px 0px 0px 0px' });
    spy.forEach(function (x) { spyIO.observe(x.h); });
    spyIO.observe($('.foot'));
  }
  buildSpy(); spyMeasure();
  if (window.matchMedia) window.matchMedia('(max-width: 1099px)').addEventListener('change', function () { curId = undefined; buildSpy(); });

  /* ── 深链：#n157 ── */
  function goHash() {
    var id = decodeURIComponent(location.hash.slice(1)); if (!id) return;
    var el = document.getElementById(id); if (!el) return;
    if (el.closest('[hidden]') || el.hidden) { clearAll(); }
    el.scrollIntoView({ block: 'start' });
    if (el.classList.contains('row')) { el.classList.remove('flash'); void el.offsetWidth; el.classList.add('flash'); }
  }
  window.addEventListener('hashchange', goHash);
  if (location.hash) setTimeout(goHash, 60);
  window.addEventListener('resize', setStatusHeight);
})();
