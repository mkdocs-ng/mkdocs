/*!
 * Sumi theme runtime. Vanilla JavaScript, no dependencies.
 * Heavy runtimes (Mermaid, KaTeX) are loaded only on pages that use them;
 * Mermaid is an ES module split per diagram type and loads near the viewport.
 */
(function () {
  'use strict';

  var S = window.sumi || {};
  var T = S.t || {};
  var doc = document;
  var root = doc.documentElement;
  var $ = function (sel, el) { return (el || doc).querySelector(sel); };
  var $$ = function (sel, el) { return Array.prototype.slice.call((el || doc).querySelectorAll(sel)); };
  var isMac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);
  var store = {
    get: function (k) { try { return localStorage.getItem('sumi.' + k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem('sumi.' + k, v); } catch (e) {} }
  };
  function t(key, vars) {
    var s = T[key] || key;
    if (vars) Object.keys(vars).forEach(function (k) { s = s.replace('{' + k + '}', vars[k]); });
    return s;
  }
  function url(path) {
    if (/^(https?:)?\/\//.test(path) || path.charAt(0) === '/') return path;
    var base = S.base || '.';
    return (base === '.' ? '' : base + '/') + path;
  }
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function svg(name) {
    var paths = {
      file: '<path d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"/><path d="M14 2v5a1 1 0 0 0 1 1h5"/>',
      hash: '<line x1="4" x2="20" y1="9" y2="9"/><line x1="4" x2="20" y1="15" y2="15"/><line x1="10" x2="8" y1="3" y2="21"/><line x1="16" x2="14" y1="3" y2="21"/>',
      cmd: '<path d="m9 18 6-6-6-6"/>',
      copy: '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
      check: '<path d="M20 6 9 17l-5-5"/>',
      x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
      'maximize-2': '<path d="M15 3h6v6"/><path d="m21 3-7 7"/><path d="m3 21 7-7"/><path d="M9 21H3v-6"/>',
      link: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>'
    };
    return '<svg class="sumi-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (paths[name] || paths.cmd) + '</svg>';
  }
  var toastTimer;
  function toast(msg) {
    var el = $('.sumi-toast');
    if (!el) return;
    el.textContent = msg;
    el.classList.add('is-on');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { el.classList.remove('is-on'); }, 1600);
  }
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    return new Promise(function (resolve, reject) {
      var ta = doc.createElement('textarea');
      ta.value = text; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.opacity = '0';
      doc.body.appendChild(ta); ta.select();
      try { doc.execCommand('copy') ? resolve() : reject(); } catch (e) { reject(e); }
      doc.body.removeChild(ta);
    });
  }
  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = doc.createElement('script');
      s.src = src; s.async = true; s.onload = resolve; s.onerror = reject;
      doc.head.appendChild(s);
    });
  }
  function typing(e) {
    var el = e.target;
    return el && (el.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName)) || e.isComposing;
  }

  /* ── Theme ─────────────────────────────────────────────────────────── */
  var listeners = [];
  function setTheme(mode, persist) {
    root.dataset.theme = mode;
    // Material's attribute, for plugin CSS written against [data-md-color-scheme="slate"].
    root.dataset.mdColorScheme = mode === 'dark' ? 'slate' : 'default';
    if (persist) store.set('palette', mode);
    syncThemeColor();
    listeners.forEach(function (fn) { fn(mode); });
    doc.dispatchEvent(new CustomEvent('sumi:theme', { detail: { theme: mode } }));
  }
  // The browser chrome takes the page background, including a site's own --sumi-bg.
  function syncThemeColor() {
    var meta = $('meta[name="theme-color"]');
    var bg = getComputedStyle(root).getPropertyValue('--sumi-bg').trim();
    if (meta && bg) meta.content = bg;
  }
  window.addEventListener('load', syncThemeColor);
  function toggleTheme() { setTheme(root.dataset.theme === 'dark' ? 'light' : 'dark', true); }
  $$('[data-sumi-theme]').forEach(function (b) { b.addEventListener('click', toggleTheme); });
  if (window.matchMedia) {
    matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (e) {
      if (!store.get('palette') && (root.dataset.palette === 'auto' || !root.dataset.palette)) setTheme(e.matches ? 'dark' : 'light');
    });
  }

  /* ── Keyboard hints ────────────────────────────────────────────────── */
  $$('[data-mod]').forEach(function (k) { k.textContent = isMac ? '⌘ K' : 'Ctrl K'; });

  /* ── Announcement ──────────────────────────────────────────────────── */
  var ann = $('.sumi-announce');
  if (ann) {
    var key = 'announce.' + (ann.dataset.key || '');
    if (store.get(key)) ann.hidden = true;
    $('.sumi-announce-close', ann).addEventListener('click', function () { ann.hidden = true; store.set(key, '1'); });
  }

  /* ── Menus ─────────────────────────────────────────────────────────── */
  function closeMenus(except) {
    $$('.sumi-menu.is-open').forEach(function (m) {
      if (m !== except) { m.classList.remove('is-open'); $('button', m).setAttribute('aria-expanded', 'false'); }
    });
  }
  doc.addEventListener('click', function (e) {
    var btn = e.target.closest('.sumi-menu > button');
    if (btn) {
      var menu = btn.parentElement;
      var open = !menu.classList.contains('is-open');
      closeMenus(menu);
      menu.classList.toggle('is-open', open);
      btn.setAttribute('aria-expanded', String(open));
      return;
    }
    if (!e.target.closest('.sumi-menu-list')) closeMenus();
  });

  /* ── Mobile sidebar ────────────────────────────────────────────────── */
  var side = $('#sumi-sidebar');
  var menuBtn = $('.sumi-menu-btn');
  var scrim;
  function setDrawer(open) {
    if (!side) return;
    // An announcement bar pushes the header down until the page scrolls, so
    // start the drawer and its scrim where the header ends.
    var head = $('.sumi-header');
    var top = head ? Math.max(0, Math.round(head.getBoundingClientRect().bottom)) + 'px' : '';
    if (open) side.style.top = top;
    side.classList.toggle('is-open', open);
    doc.body.classList.toggle('sumi-locked', open);
    if (menuBtn) menuBtn.setAttribute('aria-expanded', String(open));
    if (open) {
      scrim = doc.createElement('div');
      scrim.className = 'sumi-scrim';
      scrim.style.top = top;
      scrim.addEventListener('click', function () { setDrawer(false); });
      doc.body.appendChild(scrim);
    } else if (scrim) { scrim.remove(); scrim = null; }
  }
  // Templates that replace the page layout (404, print) have no drawer.
  if (menuBtn && !side) { menuBtn.remove(); menuBtn = null; }
  if (menuBtn) menuBtn.setAttribute('aria-controls', 'sumi-sidebar');
  if (menuBtn) menuBtn.addEventListener('click', function () { setDrawer(!side.classList.contains('is-open')); });
  if (side) {
    var current = $('.is-current', side);
    if (current) {
      var box = $('.sumi-sidebar-inner', side);
      var r = current.getBoundingClientRect(), b = box.getBoundingClientRect();
      if (r.bottom > b.bottom - 40) box.scrollTop += r.top - b.top - b.height / 3;
    }
  }

  /* ── Scrollable code and tables: reachable by keyboard ─────────────── */
  // A box that scrolls sideways needs focus so keyboard users can scroll it.
  function focusScrollable() {
    $$('.sumi-prose pre, .sumi-prose div.sumi-table, .sumi-prose .sumi-math.math-display').forEach(function (el) {
      var scrolls = el.scrollWidth > el.clientWidth + 1;
      if (scrolls && !el.hasAttribute('tabindex')) { el.setAttribute('tabindex', '0'); el.dataset.sumiFocus = ''; }
      else if (!scrolls && el.hasAttribute('data-sumi-focus')) { el.removeAttribute('tabindex'); el.removeAttribute('data-sumi-focus'); }
    });
  }
  window.addEventListener('load', focusScrollable);
  var focusTimer;
  window.addEventListener('resize', function () { clearTimeout(focusTimer); focusTimer = setTimeout(focusScrollable, 200); });

  /* ── Code blocks: copy button and language label ───────────────────── */
  $$('.sumi-prose pre').forEach(function (pre) {
    if (pre.classList.contains('mermaid') || pre.closest('.linenos')) return;
    var host = pre.closest('.highlight, .codehilite') || pre;
    if (host.querySelector(':scope > .sumi-copy')) return;
    var code = $('code', pre) || pre;
    var btn = doc.createElement('button');
    btn.type = 'button'; btn.className = 'sumi-copy'; btn.setAttribute('aria-label', t('copy_code')); btn.title = t('copy_code');
    btn.innerHTML = svg('copy');
    btn.addEventListener('click', function () {
      var text = code.innerText.replace(/\n$/, '');
      var lines = text.split('\n');
      // Skip shell prompts and console output marked by Pygments.
      var prompts = $$('.gp', code).length;
      if (prompts) {
        text = $$('.gp', code).map(function (p) {
          var out = '', n = p.nextSibling;
          while (n && !(n.nodeType === 1 && (n.classList.contains('gp') || n.classList.contains('go')))) {
            out += n.textContent; n = n.nextSibling;
          }
          return out.replace(/\n$/, '');
        }).join('\n');
      } else { text = lines.join('\n'); }
      copyText(text).then(function () {
        btn.classList.add('is-done'); btn.innerHTML = svg('check');
        setTimeout(function () { btn.classList.remove('is-done'); btn.innerHTML = svg('copy'); }, 1400);
      });
    });
    host.appendChild(btn);
    var lang = (code.className.match(/language-([\w+#-]+)/) || host.className.match(/language-([\w+#-]+)/) || [])[1];
    if (lang && host !== pre && !host.closest('.sumi-code') && !host.closest('.sumi-tab')) {
      var label = doc.createElement('span');
      label.className = 'sumi-code-lang'; label.textContent = lang;
      host.appendChild(label);
    }
  });

  /* ── Tabs ──────────────────────────────────────────────────────────── */
  var tabSets = [];
  function selectTab(set, label, focus) {
    var tabs = $$(':scope > .sumi-tab', set);
    var idx = tabs.findIndex(function (tb) { return tb.dataset.label === label; });
    if (idx < 0) return false;
    tabs.forEach(function (tb, i) { tb.classList.toggle('is-active', i === idx); });
    $$('.sumi-tablist button', set).forEach(function (b, i) {
      b.setAttribute('aria-selected', String(i === idx)); b.tabIndex = i === idx ? 0 : -1;
      if (i === idx && focus) b.focus();
    });
    return true;
  }
  $$('.sumi-tabs').forEach(function (set, n) {
    var tabs = $$(':scope > .sumi-tab', set);
    var list = doc.createElement('div');
    list.className = 'sumi-tablist'; list.setAttribute('role', 'tablist');
    tabs.forEach(function (tb, i) {
      var b = doc.createElement('button');
      b.type = 'button'; b.setAttribute('role', 'tab'); b.textContent = tb.dataset.label;
      b.id = 'sumi-tabbtn-' + n + '-' + i; tb.setAttribute('role', 'tabpanel'); tb.setAttribute('aria-labelledby', b.id);
      b.addEventListener('click', function () {
        var y = b.getBoundingClientRect().top;
        tabSets.forEach(function (s) { selectTab(s, tb.dataset.label); });
        store.set('tab', tb.dataset.label);
        window.scrollBy(0, b.getBoundingClientRect().top - y);
      });
      b.addEventListener('keydown', function (e) {
        var d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
        if (!d) return;
        var next = tabs[(i + d + tabs.length) % tabs.length];
        selectTab(set, next.dataset.label, true);
      });
      list.appendChild(b);
    });
    set.insertBefore(list, set.firstChild);
    set.dataset.ready = '';
    tabSets.push(set);
    if (!selectTab(set, store.get('tab'))) selectTab(set, tabs[0] && tabs[0].dataset.label);
  });

  /* ── Table of contents scroll spy ──────────────────────────────────── */
  var tocLinks = $$('.sumi-toc a');
  var headings = [];
  var seen = {};
  tocLinks.forEach(function (a) {
    var id = decodeURIComponent((a.getAttribute('href') || '').slice(1));
    var h = id && doc.getElementById(id);
    if (h && !seen[id]) { headings.push(h); seen[id] = true; }
  });
  function spy() {
    var y = (parseInt(getComputedStyle(root).getPropertyValue('--sumi-header-h'), 10) || 60) + 24;
    var active = null;
    for (var i = 0; i < headings.length; i++) {
      if (headings[i].getBoundingClientRect().top - y <= 1) active = headings[i]; else break;
    }
    if (!active && headings.length) active = null;
    if ((window.innerHeight + window.scrollY) >= doc.body.scrollHeight - 4 && headings.length) active = headings[headings.length - 1];
    tocLinks.forEach(function (a) {
      var on = !!active && a.getAttribute('href') === '#' + encodeURIComponent(active.id).replace(/%20/g, '%20');
      if (!on && active) on = decodeURIComponent(a.getAttribute('href').slice(1)) === active.id;
      a.classList.toggle('is-active', on);
    });
  }
  if (headings.length) {
    var ticking = false;
    window.addEventListener('scroll', function () {
      if (!ticking) { requestAnimationFrame(function () { spy(); ticking = false; }); ticking = true; }
    }, { passive: true });
    spy();
  }
  $$('.sumi-toc-inline .sumi-toc a').forEach(function (a) {
    a.addEventListener('click', function () { a.closest('details').open = false; });
  });
  // A {.wide} table reaches into the table-of-contents column. While one passes
  // beside the sticky table of contents, the table of contents steps aside.
  var rail = $('.sumi-rail');
  var wideTables = $$('.sumi-table--wide');
  if (rail && wideTables.length) {
    var railInner = $('.sumi-rail-inner', rail) || rail;
    var railTicking = false;
    var railCheck = function () {
      railTicking = false;
      var covered = false;
      var box = rail.getBoundingClientRect();
      if (box.width) {
        var inner = railInner.getBoundingClientRect();
        var top = Math.max(box.top, inner.top), bottom = Math.min(box.bottom, inner.bottom);
        covered = wideTables.some(function (w) {
          var r = w.getBoundingClientRect();
          return r.left < box.right && r.right > box.left && r.top < bottom && r.bottom > top;
        });
      }
      rail.classList.toggle('is-covered', covered);
    };
    var railSchedule = function () {
      if (!railTicking) { railTicking = true; requestAnimationFrame(railCheck); }
    };
    window.addEventListener('scroll', railSchedule, { passive: true });
    window.addEventListener('resize', railSchedule);
    railCheck();
  }
  var topLink = $('.sumi-rail-top');
  if (topLink) topLink.addEventListener('click', function (e) { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); history.replaceState(null, '', location.pathname); });

  /* ── Page actions ──────────────────────────────────────────────────── */
  var mdCache = null;
  function getMarkdown() {
    if (!S.markdown) return Promise.reject();
    if (mdCache) return Promise.resolve(mdCache);
    return fetch(S.markdown).then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
      .then(function (txt) { mdCache = txt; return txt; });
  }
  function copyMarkdown(btn) {
    // Safari needs the clipboard write to start inside the click: hand it a promise.
    var done = function () {
      toast(t('copied'));
      if (btn) {
        btn.classList.add('is-done');
        setTimeout(function () { btn.classList.remove('is-done'); }, 1400);
      }
    };
    if (window.ClipboardItem && navigator.clipboard && navigator.clipboard.write && window.isSecureContext) {
      var item = new ClipboardItem({ 'text/plain': getMarkdown().then(function (s) { return new Blob([s], { type: 'text/plain' }); }) });
      return navigator.clipboard.write([item]).then(done, function () { getMarkdown().then(copyText).then(done); });
    }
    return getMarkdown().then(copyText).then(done);
  }
  $$('[data-sumi-copy-page]').forEach(function (b) { b.addEventListener('click', function () { copyMarkdown(b); }); });
  $$('[data-sumi-print]').forEach(function (b) { b.addEventListener('click', function () { closeMenus(); window.print(); }); });
  $$('[data-assistant]').forEach(function (a) {
    var md = S.markdown ? new URL(S.markdown, location.href).href : location.href;
    var prompt = 'Read ' + md + ' so I can ask questions about it.';
    a.href = a.dataset.assistant === 'claude'
      ? 'https://claude.ai/new?q=' + encodeURIComponent(prompt)
      : 'https://chatgpt.com/?hints=search&q=' + encodeURIComponent(prompt);
    a.target = '_blank';
  });
  window.addEventListener('beforeprint', function () {
    $$('.sumi-prose details').forEach(function (d) { if (!d.open) { d.dataset.wasClosed = ''; d.open = true; } });
  });
  window.addEventListener('afterprint', function () {
    $$('.sumi-prose details[data-was-closed]').forEach(function (d) { d.open = false; delete d.dataset.wasClosed; });
  });

  /* ── Image zoom ────────────────────────────────────────────────────── */
  var zoom = $('.sumi-zoom');
  if (zoom) {
    $$('.sumi-prose img').forEach(function (img) {
      if (img.closest('a') || img.closest('.sumi-cards') || img.classList.contains('no-zoom')) return;
      img.classList.add('sumi-zoomable');
      img.addEventListener('click', function () {
        var z = $('img', zoom) || zoom.appendChild(doc.createElement('img'));
        z.src = img.currentSrc || img.src; z.alt = img.alt;
        zoom.showModal();
      });
    });
    zoom.addEventListener('click', function () { zoom.close(); });
  }

  /* ── Mermaid (lazy) ────────────────────────────────────────────────── */
  // The ES module build is split per diagram type, so a page with one
  // flowchart fetches the core and the flowchart code only. Nothing loads
  // until a diagram comes near the viewport, and diagrams render one by one.
  var features = S.features || [];
  if (features.indexOf('mermaid') >= 0) {
    var diagrams = $$('pre.mermaid');
    var mermaidReady = null;
    var queue = Promise.resolve();
    var mermaidConfig = function () {
      var dark = root.dataset.theme === 'dark';
      var css = getComputedStyle(root);
      var v = function (name) { return css.getPropertyValue(name).trim(); };
      return {
        startOnLoad: false, securityLevel: 'strict', theme: 'base',
        fontFamily: v('--sumi-font'),
        themeVariables: {
          darkMode: dark, fontSize: '14px',
          background: v('--sumi-bg-elev'),
          primaryColor: v('--sumi-bg-soft'),
          primaryBorderColor: v('--sumi-line-2'),
          primaryTextColor: v('--sumi-fg'),
          lineColor: v('--sumi-fg-3'),
          secondaryColor: v('--sumi-bg-sunken'),
          tertiaryColor: v('--sumi-bg-elev'),
          noteBkgColor: dark ? '#3a3220' : '#fbf3dc', noteTextColor: v('--sumi-fg')
        }
      };
    };
    var loadMermaid = function () {
      if (!mermaidReady) {
        var src = new URL(url('assets/sumi/vendor/mermaid/mermaid.esm.min.js'), location.href).href;
        mermaidReady = import(src).then(function (m) {
          window.mermaid = m.default;
          return m.default;
        });
      }
      return mermaidReady;
    };
    var renderOne = function (d) {
      queue = queue.then(function () {
        return loadMermaid().then(function (mermaid) {
          mermaid.initialize(mermaidConfig());
          d.removeAttribute('data-processed');
          d.innerHTML = esc(d.dataset.source);
          return mermaid.run({ nodes: [d] });
        }).then(function () {
          d.dataset.rendered = '';
          diagramTools(d);
        }).catch(function () { d.classList.add('is-failed'); });
      });
      return queue;
    };
    diagrams.forEach(function (d) { d.dataset.source = d.textContent; });
    if ('IntersectionObserver' in window) {
      var seen = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (!e.isIntersecting) return;
          seen.unobserve(e.target);
          renderOne(e.target);
        });
      }, { rootMargin: '400px 0px' });
      diagrams.forEach(function (d) { seen.observe(d); });
    } else {
      diagrams.forEach(renderOne);
    }
    // Redraw diagrams that are already drawn when the colour scheme changes.
    listeners.push(function () {
      diagrams.forEach(function (d) { if (d.hasAttribute('data-rendered')) renderOne(d); });
    });
    window.addEventListener('beforeprint', function () {
      diagrams.forEach(function (d) { if (!d.hasAttribute('data-rendered')) renderOne(d); });
    });
  }

  // Expand, copy source and download buttons for a drawn diagram.
  function diagramTools(d) {
    var fig = d.closest('.sumi-diagram');
    if (!fig || $('.sumi-diagram-tools', fig)) return;
    var bar = doc.createElement('div');
    bar.className = 'sumi-diagram-tools';
    var btn = function (label, icon, fn) {
      var b = doc.createElement('button');
      b.type = 'button'; b.className = 'sumi-icon-btn';
      b.setAttribute('aria-label', label); b.title = label;
      b.innerHTML = icon;
      b.addEventListener('click', fn);
      bar.appendChild(b);
    };
    var icon = function (paths) {
      return '<svg class="sumi-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + paths + '</svg>';
    };
    btn(t('diagram_expand'), icon('<path d="M15 3h6v6"/><path d="M9 21H3v-6"/><path d="m21 3-7 7"/><path d="m3 21 7-7"/>'), function () {
      var view = $('.sumi-diagram-view');
      if (!view) return;
      var box = $('.sumi-diagram-view-body', view);
      box.innerHTML = '';
      var svgEl = $('svg', d);
      if (!svgEl) return;
      var clone = svgEl.cloneNode(true);
      clone.removeAttribute('style'); clone.removeAttribute('width'); clone.removeAttribute('height');
      var canvas = doc.createElement('div');
      canvas.className = 'sumi-diagram-view-canvas';
      canvas.appendChild(clone);
      box.appendChild(canvas);
      resetZoom();
      view.showModal();
    });
    btn(t('diagram_source'), svg('copy'), function () {
      copyText(d.dataset.source.trim()).then(function () { toast(t('copied')); }, function () {});
    });
    btn(t('diagram_download'), icon('<path d="M12 15V3"/><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/>'), function () {
      var svgEl = $('svg', d);
      if (!svgEl) return;
      var blob = new Blob(['<?xml version="1.0" encoding="UTF-8"?>\n' + new XMLSerializer().serializeToString(svgEl)], { type: 'image/svg+xml' });
      var a = doc.createElement('a');
      a.href = URL.createObjectURL(blob); a.download = 'diagram.svg';
      doc.body.appendChild(a); a.click(); a.remove();
      setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
    });
    fig.appendChild(bar);
  }
  var diagramView = $('.sumi-diagram-view');
  var resetZoom = function () {};
  if (diagramView) {
    diagramView.addEventListener('click', function (e) {
      if (e.target === diagramView || e.target.closest('[data-close]')) diagramView.close();
    });
    // Pan and zoom: drag, wheel, pinch, double-click, the buttons, or + - 0.
    var viewBody = $('.sumi-diagram-view-body', diagramView);
    var zoom = { x: 0, y: 0, s: 1 };
    var applyZoom = function () {
      var c = $('.sumi-diagram-view-canvas', diagramView);
      if (c) c.style.transform = 'translate(' + zoom.x + 'px, ' + zoom.y + 'px) scale(' + zoom.s + ')';
    };
    var zoomAt = function (px, py, f) {
      var s = Math.min(8, Math.max(0.5, zoom.s * f));
      zoom.x = px - (px - zoom.x) * s / zoom.s;
      zoom.y = py - (py - zoom.y) * s / zoom.s;
      zoom.s = s;
      applyZoom();
    };
    var zoomCenter = function (f) { zoomAt(viewBody.clientWidth / 2, viewBody.clientHeight / 2, f); };
    resetZoom = function () { zoom = { x: 0, y: 0, s: 1 }; applyZoom(); };
    var local = function (cx, cy) { var r = viewBody.getBoundingClientRect(); return [cx - r.left, cy - r.top]; };
    viewBody.addEventListener('wheel', function (e) {
      e.preventDefault();
      var p = local(e.clientX, e.clientY);
      zoomAt(p[0], p[1], Math.exp(-e.deltaY * (e.deltaMode ? 0.05 : 0.002)));
    }, { passive: false });
    var pts = {}, pinch = null;
    viewBody.addEventListener('pointerdown', function (e) {
      if (e.pointerType === 'mouse' && e.button !== 0) return;
      viewBody.setPointerCapture(e.pointerId);
      pts[e.pointerId] = [e.clientX, e.clientY];
      pinch = null;
      viewBody.classList.add('is-dragging');
    });
    viewBody.addEventListener('pointermove', function (e) {
      var prev = pts[e.pointerId];
      if (!prev) return;
      pts[e.pointerId] = [e.clientX, e.clientY];
      var ids = Object.keys(pts);
      if (ids.length === 1) {
        zoom.x += e.clientX - prev[0]; zoom.y += e.clientY - prev[1];
        applyZoom();
        return;
      }
      var a = pts[ids[0]], b = pts[ids[1]];
      var dist = Math.hypot(a[0] - b[0], a[1] - b[1]);
      var mid = local((a[0] + b[0]) / 2, (a[1] + b[1]) / 2);
      if (pinch && pinch.d) {
        zoom.x += mid[0] - pinch.m[0]; zoom.y += mid[1] - pinch.m[1];
        zoomAt(mid[0], mid[1], dist / pinch.d);
      }
      pinch = { d: dist, m: mid };
    });
    var lift = function (e) {
      var left = {};
      Object.keys(pts).forEach(function (k) { if (String(k) !== String(e.pointerId)) left[k] = pts[k]; });
      pts = left;
      pinch = null;
      if (!Object.keys(pts).length) viewBody.classList.toggle('is-dragging', false);
    };
    viewBody.addEventListener('pointerup', lift);
    viewBody.addEventListener('pointercancel', lift);
    viewBody.addEventListener('dblclick', function (e) { var p = local(e.clientX, e.clientY); zoomAt(p[0], p[1], 2); });
    $$('[data-zoom]', diagramView).forEach(function (b) {
      b.addEventListener('click', function () {
        if (b.dataset.zoom === 'in') zoomCenter(1.5);
        else if (b.dataset.zoom === 'out') zoomCenter(1 / 1.5);
        else resetZoom();
      });
    });
    diagramView.addEventListener('keydown', function (e) {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === '+' || e.key === '=') zoomCenter(1.5);
      else if (e.key === '-' || e.key === '_') zoomCenter(1 / 1.5);
      else if (e.key === '0') resetZoom();
      else return;
      e.preventDefault();
    });
  }

  // Run fn(el) once el comes within 400px of the viewport.
  function whenNear(els, fn) {
    if (!('IntersectionObserver' in window)) { els.forEach(fn); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        io.unobserve(e.target);
        fn(e.target);
      });
    }, { rootMargin: '400px 0px' });
    els.forEach(function (el) { io.observe(el); });
  }
  function readJSON(el) {
    try { return JSON.parse(el.textContent); } catch (e) { return null; }
  }

  /* ── ECharts (lazy) ────────────────────────────────────────────────── */
  if (features.indexOf('echarts') >= 0) {
    var charts = [];
    var echartsReady = null;
    var drawChart = function (fig) {
      var box = $('.sumi-chart-canvas', fig);
      var option = readJSON($('.sumi-chart-option', fig));
      if (!box || !option) return;
      if (fig._chart) fig._chart.dispose();
      var css = getComputedStyle(root);
      var dark = root.dataset.theme === 'dark';
      var chart = window.echarts.init(box, dark ? 'dark' : null, { renderer: 'svg' });
      // The accent first, then Sumi's other named accents.
      var palette = dark
        ? ['#86b4ea', '#e7b45a', '#9ccc6e', '#dc93d4', '#6fd0c6', '#ef7258', '#bdb6aa']
        : ['#2f5d93', '#9a6512', '#4b6b2f', '#7a3b74', '#1f6f6a', '#c4432b', '#75716a'];
      var accent = css.getPropertyValue('--sumi-accent').trim();
      if (accent) palette = [accent].concat(palette.filter(function (c) { return c.toLowerCase() !== accent.toLowerCase(); }));
      chart.setOption(Object.assign({
        color: palette,
        backgroundColor: 'transparent',
        textStyle: { fontFamily: css.getPropertyValue('--sumi-font').trim() }
      }, option));
      fig._chart = chart;
      fig.dataset.rendered = '';
    };
    whenNear($$('.sumi-chart'), function (fig) {
      echartsReady = echartsReady || loadScript(url('assets/sumi/vendor/echarts/echarts.min.js'));
      echartsReady.then(function () { drawChart(fig); charts.push(fig); }).catch(function () {});
    });
    listeners.push(function () { charts.forEach(drawChart); });
    if ('ResizeObserver' in window) {
      var ro = new ResizeObserver(function () { charts.forEach(function (f) { if (f._chart) f._chart.resize(); }); });
      $$('.sumi-chart').forEach(function (f) { ro.observe(f); });
    }
  }

  /* ── Markmap (lazy) ────────────────────────────────────────────────── */
  if (features.indexOf('markmap') >= 0) {
    var markmapReady = null;
    whenNear($$('.sumi-markmap'), function (fig) {
      var data = readJSON($('.sumi-markmap-data', fig));
      if (!data) return;
      markmapReady = markmapReady || loadScript(url('assets/sumi/vendor/markmap/d3.min.js')).then(function () {
        return loadScript(url('assets/sumi/vendor/markmap/markmap-view.js'));
      });
      markmapReady.then(function () {
        var ns = 'http://www.w3.org/2000/svg';
        var svgEl = doc.createElementNS(ns, 'svg');
        svgEl.setAttribute('class', 'sumi-markmap-svg');
        fig.insertBefore(svgEl, fig.firstChild);
        window.markmap.Markmap.create(svgEl, { duration: 250, maxWidth: 260, initialExpandLevel: -1 }, data);
        fig.dataset.rendered = '';
      }).catch(function () {});
    });
  }

  /* ── KaTeX (lazy) ──────────────────────────────────────────────────── */
  if (features.indexOf('math') >= 0) {
    loadScript(url('assets/sumi/vendor/katex/katex.min.js')).then(function () {
      $$('.sumi-math, .arithmatex').forEach(function (el) {
        var tex = el.textContent.trim();
        var display = el.classList.contains('math-display') || el.tagName === 'DIV';
        tex = tex.replace(/^\\\(|\\\)$/g, '').replace(/^\\\[|\\\]$/g, '').replace(/^\$\$?|\$\$?$/g, '');
        try {
          window.katex.render(tex, el, { displayMode: display, throwOnError: false, output: 'htmlAndMathml' });
          el.dataset.rendered = '';
        } catch (e) {}
      });
    }).catch(function () {});
  }

  /* ── Versions (mike) ───────────────────────────────────────────────── */
  if (S.versions === 'mike') {
    var vmenu = $('.sumi-version-menu');
    var siteRoot = new URL(url('../'), location.href);
    fetch(new URL('versions.json', siteRoot)).then(function (r) { return r.json(); }).then(function (versions) {
      var here = new URL(url('.'), location.href).pathname.replace(siteRoot.pathname, '').split('/')[0];
      var cur = versions.find(function (v) { return v.version === here || (v.aliases || []).indexOf(here) >= 0; });
      if (!cur || !vmenu) return;
      $('.sumi-version-current', vmenu).textContent = cur.title || cur.version;
      var list = $('.sumi-menu-list', vmenu);
      var rel = location.href.slice(new URL(url('.'), location.href).href.length);
      versions.forEach(function (v) {
        var li = doc.createElement('li');
        li.setAttribute('role', 'none');
        li.innerHTML = '<a role="menuitem" href="' + esc(new URL(v.version + '/' + rel, siteRoot).href) + '"' +
          (v === cur ? ' aria-current="true"' : '') + '>' + esc(v.title || v.version) + '</a>';
        list.appendChild(li);
      });
      vmenu.hidden = false;
      var latest = versions[0];
      if (cur !== latest && (latest.aliases || []).indexOf(here) < 0) {
        var banner = $('.sumi-version-banner');
        banner.innerHTML = esc(t('old_version')) + ' <a href="' + esc(new URL((latest.aliases && latest.aliases[0] || latest.version) + '/', siteRoot).href) + '">' + esc(t('go_latest')) + '</a>';
        banner.hidden = false;
      }
      S.versionList = versions;
    }).catch(function () {});
  }

  /* ── Command palette ───────────────────────────────────────────────── */
  var pal = $('.sumi-palette');
  var input = pal && $('input', pal);
  var results = pal && $('.sumi-palette-results', pal);
  var index = null, loading = null, items = [], sel = 0;
  var CJK = /[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]/;

  function loadIndex() {
    if (index || loading) return loading;
    if (!S.search) { index = []; return Promise.resolve(index); }
    loading = fetch(S.search).then(function (r) { return r.json(); }).then(function (data) {
      var titles = {}, headings = {}, firstSection = {};
      (data.docs || []).forEach(function (d) {
        var hash = d.location.indexOf('#');
        if (hash < 0) { titles[d.location] = d.title; return; }
        var pageLoc = d.location.slice(0, hash);
        (headings[pageLoc] = headings[pageLoc] || []).push(d.title);
        if (!(pageLoc in firstSection)) firstSection[pageLoc] = d.location;
      });
      var esc_re = function (s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); };
      index = [];
      (data.docs || []).forEach(function (d) {
        var hash = d.location.indexOf('#');
        var pageLoc = hash < 0 ? d.location : d.location.slice(0, hash);
        // The first heading of a page usually repeats the page itself: keep one result.
        if (hash >= 0 && firstSection[pageLoc] === d.location && d.title === titles[pageLoc]) return;
        // Drop real tags only: text like `a < b && c > d` stays.
        var text = (d.text || '').replace(/<\/?[a-zA-Z][^<>]*>/g, ' ').replace(/\s+/g, ' ').trim();
        // A page's full text keeps the heading permalinks ("Title # …"): drop them.
        if (hash < 0 && headings[pageLoc]) headings[pageLoc].forEach(function (h) {
          text = text.replace(new RegExp('(^|\\s)(' + esc_re(h) + ') [#¶§¤] ', 'g'), '$1$2 ');
        });
        index.push({
          title: d.title || '', page: titles[pageLoc] || '', loc: d.location, text: text,
          lt: (d.title || '').toLowerCase(), lx: text.toLowerCase(), section: hash >= 0
        });
      });
      return index;
    }).catch(function () { index = []; return index; });
    return loading;
  }
  function terms(q) {
    var out = [];
    q.toLowerCase().split(/\s+/).forEach(function (w) {
      if (!w) return;
      if (CJK.test(w)) {
        // Split mixed runs: CJK sequences are matched as substrings.
        (w.match(/[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]+|[^\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]+/g) || []).forEach(function (p) { out.push(p); });
      } else out.push(w);
    });
    return out;
  }
  // Mark every term in one pass over the raw text, then escape each piece: marking
  // escaped HTML term by term matched inside "&quot;" and inside earlier <mark>s.
  function highlight(text, ts) {
    var words = ts.filter(Boolean).sort(function (a, b) { return b.length - a.length; })
      .map(function (w) { return w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); });
    if (!words.length) return esc(text);
    return String(text).split(new RegExp('(' + words.join('|') + ')', 'ig')).map(function (part, i) {
      return i % 2 ? '<mark>' + esc(part) + '</mark>' : esc(part);
    }).join('');
  }
  function snippet(text, ts) {
    var lx = text.toLowerCase(), pos = -1;
    for (var i = 0; i < ts.length && pos < 0; i++) pos = lx.indexOf(ts[i]);
    if (pos < 0) return text.slice(0, 140);
    var start = Math.max(0, pos - 50);
    return (start ? '…' : '') + text.slice(start, start + 160) + (start + 160 < text.length ? '…' : '');
  }
  function searchDocs(q) {
    var ts = terms(q);
    if (!ts.length) return [];
    var scored = [];
    (index || []).forEach(function (d) {
      var score = 0;
      for (var i = 0; i < ts.length; i++) {
        var w = ts[i], inTitle = d.lt.indexOf(w), inText = d.lx.indexOf(w);
        if (inTitle < 0 && inText < 0 && d.page.toLowerCase().indexOf(w) < 0) return;
        if (inTitle === 0) score += 14; else if (inTitle > 0) score += 9;
        if (inText >= 0) score += 2 + Math.min(3, d.lx.split(w).length - 2) * 0.5;
      }
      if (d.lt === q.toLowerCase()) score += 10;
      if (!d.section) score += 1.5;
      scored.push({ d: d, s: score });
    });
    scored.sort(function (a, b) { return b.s - a.s; });
    return scored.slice(0, 40).map(function (x) {
      var d = x.d;
      return {
        kind: 'doc', icon: d.section ? 'hash' : 'file', href: url(d.loc),
        title: highlight(d.title || d.page, ts),
        path: d.section ? esc(d.page) : '',
        snippet: d.text ? highlight(snippet(d.text, ts), ts) : ''
      };
    });
  }
  function navMatches(q) {
    var ts = terms(q);
    return (S.nav || []).filter(function (n) {
      var hay = (n.t + ' ' + n.s).toLowerCase();
      return ts.every(function (w) { return hay.indexOf(w) >= 0; });
    }).slice(0, 30).map(function (n) {
      return { kind: 'doc', icon: n.x ? 'link' : 'file', href: n.x ? n.u : url(n.u), title: highlight(n.t, ts), path: esc(n.s) };
    });
  }
  function commands() {
    var list = [
      { title: t('cmd_toggle_theme'), run: toggleTheme, keys: 'theme dark light 主题 深色' }
    ];
    if (S.markdown) {
      list.push({ title: t('cmd_copy_markdown'), run: function () { copyMarkdown(); }, keys: 'copy markdown md 复制' });
      list.push({ title: t('cmd_view_markdown'), run: function () { window.open(S.markdown, '_blank'); }, keys: 'markdown source 源码' });
    }
    if (S.edit) list.push({ title: t('cmd_edit'), run: function () { location.href = S.edit; }, keys: 'edit github 编辑' });
    list.push({ title: t('cmd_print'), run: function () { window.print(); }, keys: 'print pdf 打印' });
    list.push({ title: t('cmd_top'), run: function () { window.scrollTo({ top: 0 }); }, keys: 'top 顶部' });
    list.push({ title: t('cmd_home'), run: function () { location.href = url('./'); }, keys: 'home 首页' });
    (S.alternate || []).forEach(function (a) {
      list.push({ title: t('cmd_language', { name: a.name }), run: function () { location.href = url(a.link.replace(/^\//, '')); }, keys: 'language lang 语言 ' + a.lang });
    });
    (S.versionList || []).forEach(function (v) {
      list.push({ title: t('cmd_version', { name: v.title || v.version }), run: function () { location.href = new URL('../' + v.version + '/', new URL(url('./'), location.href)).href; }, keys: 'version 版本' });
    });
    if (openCompare) list.push({ title: t('compare_open'), run: function () { openCompare(); }, keys: 'bilingual compare translation side 双语 对照 翻译' });
    if (doc.querySelector('link[href$="llms.txt"]')) list.push({ title: t('cmd_llms'), run: function () { location.href = url('llms.txt'); }, keys: 'llms ai agent' });
    return list;
  }
  function render(q) {
    var cmdOnly = q.charAt(0) === '>';
    var query = cmdOnly ? q.slice(1).trim() : q.trim();
    var docs = [];
    if (!cmdOnly && query) docs = index && index.length ? searchDocs(query) : navMatches(query);
    if (!cmdOnly && !query) docs = (S.nav || []).slice(0, 8).map(function (n) {
      return { kind: 'doc', icon: n.x ? 'link' : 'file', href: n.x ? n.u : url(n.u), title: esc(n.t), path: esc(n.s) };
    });
    var lq = query.toLowerCase();
    var cmds = commands().filter(function (c) {
      return !lq || (c.title + ' ' + c.keys).toLowerCase().indexOf(lq) >= 0;
    }).map(function (c) { return { kind: 'cmd', icon: 'cmd', title: highlight(c.title, lq ? [lq] : []), run: c.run }; });
    if (!cmdOnly && query && docs.length) cmds = cmds.slice(0, 3);
    items = docs.concat(cmds);
    var html = '';
    if (docs.length) html += '<div class="sumi-palette-group">' + esc(t('pages')) + '</div>';
    items.forEach(function (it, i) {
      if (i === docs.length && cmds.length) html += '<div class="sumi-palette-group">' + esc(t('commands')) + '</div>';
      html += '<div class="sumi-palette-item" role="option" id="sumi-opt-' + i + '" data-i="' + i + '">' + svg(it.icon) +
        '<span class="sumi-palette-text"><span class="sumi-palette-title">' + it.title + '</span>' +
        (it.path ? '<span class="sumi-palette-path">' + it.path + '</span>' : '') +
        (it.snippet ? '<span class="sumi-palette-snippet">' + it.snippet + '</span>' : '') + '</span></div>';
    });
    if (!items.length) html = '<div class="sumi-palette-empty">' + esc(t('search_no_results')) + ' “' + esc(query) + '”</div>';
    results.innerHTML = html;
    sel = 0; mark();
  }
  function mark() {
    $$('.sumi-palette-item', results).forEach(function (el, i) {
      el.setAttribute('aria-selected', String(i === sel));
      if (i === sel) { el.scrollIntoView({ block: 'nearest' }); input.setAttribute('aria-activedescendant', el.id); }
    });
  }
  function choose(i, newTab) {
    var it = items[i];
    if (!it) return;
    if (it.kind === 'cmd') { pal.close(); it.run(); return; }
    if (newTab) window.open(it.href, '_blank'); else { pal.close(); location.href = it.href; }
  }
  function openPalette(prefix) {
    if (!pal || pal.open) return;
    closeMenus();
    pal.showModal();
    input.value = prefix || '';
    render(input.value);
    input.focus();
    var p = loadIndex();
    if (p) p.then(function () { if (pal.open) render(input.value); });
  }
  if (pal) {
    $$('[data-sumi-palette]').forEach(function (b) { b.addEventListener('click', function () { openPalette(); }); });
    input.addEventListener('input', function () { render(input.value); });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { e.preventDefault(); pal.close(); return; }
      if (e.key === 'ArrowDown') { e.preventDefault(); sel = Math.min(items.length - 1, sel + 1); mark(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); sel = Math.max(0, sel - 1); mark(); }
      else if (e.key === 'Enter') { e.preventDefault(); choose(sel, e.metaKey || e.ctrlKey); }
    });
    results.addEventListener('click', function (e) {
      var el = e.target.closest('.sumi-palette-item');
      if (el) choose(+el.dataset.i, e.metaKey || e.ctrlKey);
    });
    results.addEventListener('mousemove', function (e) {
      var el = e.target.closest('.sumi-palette-item');
      if (el && +el.dataset.i !== sel) { sel = +el.dataset.i; mark(); }
    });
    pal.addEventListener('click', function (e) { if (e.target === pal) pal.close(); });
  }

  /* ── Bilingual view ────────────────────────────────────────────────── */
  // Two existing pages side by side, this one and its translation, each in
  // its own frame. Headings share their ids across languages, so scrolling
  // one pane brings the other to the same section.
  var inPane = root.classList.contains('sumi-pane');
  var openCompare = null;
  if (inPane) {
    S.keyboard = false;
    // Links to other pages open in the main window; anchors stay in the pane.
    doc.addEventListener('click', function (e) {
      var a = e.target.closest && e.target.closest('a[href]');
      if (!a || a.target) return;
      var u = new URL(a.href, location.href);
      if (u.origin === location.origin && u.pathname === location.pathname && u.search === location.search) return;
      a.target = '_top';
    }, true);
    doc.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape') return;
      try { var host = parent.document.querySelector('.sumi-compare[open]'); if (host) host.close(); } catch (err) {}
    });
  }
  var cmp = !inPane && (S.translations || []).length ? $('.sumi-compare') : null;
  if (cmp) {
    var frames = $$('iframe', cmp);
    var langSel = $('.sumi-compare-lang', cmp);
    var syncBox = $('.sumi-compare-sync input', cmp);
    var approx = $('.sumi-compare-approx', cmp);
    var target = 0, started = false, owner = 0, map = null, expect = [null, null], pending = 0;
    if (store.get('compare-sync') === '0') syncBox.checked = false;
    var win = function (n) { return frames[n].contentWindow; };
    var maxY = function (w) { return Math.max(0, w.document.documentElement.scrollHeight - w.innerHeight); };
    // Sync maps one side's scroll position to the other's. Its fixed points are
    // places both pages share: headings with the same id and, in a section
    // whose blocks line up one to one, every paragraph, list, code block and
    // table. Each is matched where the eye reads, a third of the way down.
    var kind = function (el) { return el.tagName + '.' + (el.classList[0] || ''); };
    var sig = function (els) { return els.map(kind).join(); };
    var prose = function (el) { return !/^(P|UL|OL|DL|BLOCKQUOTE)\./.test(kind(el)); };
    var sections = function (w) {
      var c = w.document.querySelector('.sumi-content'), out = [], cur = { id: '', items: [] };
      Array.prototype.forEach.call(c ? c.children : [], function (el) {
        if (!el.offsetHeight) return;
        if (/^H[1-6]$/.test(el.tagName)) {
          out.push(cur);
          cur = { id: el.tagName === 'H1' ? ':h1' : el.id || null, head: el, items: [] };
        } else cur.items.push(el);
      });
      out.push(cur);
      return out;
    };
    var makeMap = function (a, b) {
      var sa = sections(a), sb = sections(b), at = {}, pairs = [], last = -1, shared = 0;
      sb.forEach(function (s, j) { if (s.id !== null) at[s.id] = j; });
      sa.forEach(function (s) {
        var j = s.id === null ? undefined : at[s.id], x = s.items, y;
        if (j === undefined || j <= last) return;
        last = j; shared++;
        y = sb[j].items;
        if (s.head) pairs.push([s.head, sb[j].head]);
        // A paragraph split or merged in translation: match the other blocks only.
        if (sig(x) !== sig(y)) { x = x.filter(prose); y = y.filter(prose); }
        if (sig(x) === sig(y)) x.forEach(function (el, k) { pairs.push([el, y[k]]); });
      });
      var ma = maxY(a), mb = maxY(b), la = a.innerHeight / 3, lb = b.innerHeight / 3, k = [[0, 0]];
      pairs.forEach(function (p) {
        var x = p[0].getBoundingClientRect().top + a.scrollY - la;
        var y = p[1].getBoundingClientRect().top + b.scrollY - lb;
        var q = k[k.length - 1];
        if (x > q[0] && y > q[1] && x < ma && y < mb) k.push([x, y]);
      });
      k.push([ma, mb]);
      // Between fixed points the curve is a monotone cubic, so the follower
      // changes speed gradually instead of at each paragraph.
      var slopes = function (from) {
        var to = 1 - from, d = [], m = [], i;
        for (i = 0; i + 1 < k.length; i++) d[i] = k[i + 1][from] > k[i][from] ? (k[i + 1][to] - k[i][to]) / (k[i + 1][from] - k[i][from]) : 0;
        for (i = 0; i < k.length; i++) m[i] = i === 0 ? d[0] : i === k.length - 1 ? d[i - 1] : d[i - 1] + d[i] ? 2 * d[i - 1] * d[i] / (d[i - 1] + d[i]) : 0;
        return m;
      };
      return { k: k, m: [slopes(0), slopes(1)], approx: shared < Math.max(sa.length, sb.length) };
    };
    var project = function (mp, v, from) {
      var k = mp.k, m = mp.m[from], to = 1 - from, i = 1;
      while (i < k.length - 1 && k[i][from] <= v) i++;
      var p = k[i - 1], q = k[i], h = q[from] - p[from];
      if (!(h > 0)) return p[to];
      var s = Math.min(1, Math.max(0, (v - p[from]) / h)), s2 = s * s, s3 = s2 * s;
      return (2 * s3 - 3 * s2 + 1) * p[to] + (s3 - 2 * s2 + s) * h * m[i - 1] + (3 * s2 - 2 * s3) * q[to] + (s3 - s2) * h * m[i];
    };
    var scrollPane = function (n, y) {
      var w = win(n);
      y = Math.round(Math.min(maxY(w), Math.max(0, y)));
      if (Math.abs(w.scrollY - y) < 1) return;
      expect[n] = y;
      w.scrollTo({ top: y, behavior: 'instant' });
    };
    var ready = function (n) {
      try { return !!frames[n].contentDocument.querySelector('.sumi-content'); } catch (e) { return false; }
    };
    // The side being read leads; the other follows in the same frame.
    var follow = function () {
      if (map && syncBox.checked) scrollPane(1 - owner, project(map, win(owner).scrollY, owner));
    };
    var measure = function () {
      map = ready(0) && ready(1) ? makeMap(win(0), win(1)) : null;
      if (approx) approx.hidden = !(map && map.approx);
      follow();
    };
    var remeasure = function () { cancelAnimationFrame(pending); pending = requestAnimationFrame(measure); };
    frames.forEach(function (f, n) {
      f.addEventListener('load', function () {
        var pane = f.parentNode, err = $('.sumi-compare-error', pane);
        if (err) pane.removeChild(err);
        if (!ready(n)) {
          map = null;
          if (f.getAttribute('src')) {
            err = doc.createElement('div');
            err.className = 'sumi-compare-error';
            err.textContent = t('compare_failed');
            pane.appendChild(err);
          }
          return;
        }
        var w = f.contentWindow, d = w.document, ticking = false;
        var lead = function () { owner = n; expect[n] = null; };
        ['wheel', 'touchstart', 'pointerdown', 'keydown'].forEach(function (type) {
          d.addEventListener(type, lead, { capture: true, passive: true });
        });
        w.addEventListener('scroll', function () {
          // Ignore the scroll this side made because it was following.
          if (expect[n] !== null && Math.abs(w.scrollY - expect[n]) < 2) { expect[n] = null; return; }
          lead();
          if (ticking) return;
          ticking = true;
          requestAnimationFrame(function () { ticking = false; follow(); });
        }, { passive: true });
        // Late images, fonts, opened details and tabs move the fixed points.
        if ('ResizeObserver' in window) new ResizeObserver(remeasure).observe(d.querySelector('.sumi-content'));
        d.addEventListener('load', remeasure, true);
        d.addEventListener('toggle', remeasure, true);
        if (d.fonts) d.fonts.ready.then(remeasure);
        // First open: start where the reader is on this page.
        if (n === 0) scrollPane(0, project(makeMap(window, w), window.scrollY, 0));
        measure();
      });
    });
    var load = function (n, href) {
      map = null;
      // Replace the frame's page instead of adding a history entry.
      if (frames[n].getAttribute('src') && frames[n].contentWindow) frames[n].contentWindow.location.replace(href);
      else frames[n].src = href;
    };
    var setTarget = function (i) {
      target = i;
      owner = 0;
      var tr = S.translations[i];
      $$('.sumi-compare-target-name', cmp).forEach(function (el) { el.textContent = tr.name; });
      frames[1].title = tr.name;
      frames[1].lang = tr.lang;
      load(1, tr.href);
    };
    var show = function (n) {
      cmp.dataset.show = String(n);
      $$('.sumi-compare-switch button', cmp).forEach(function (b) { b.setAttribute('aria-pressed', String(+b.dataset.pane === n)); });
    };
    openCompare = function (restoring) {
      if (cmp.open) return;
      closeMenus();
      cmp.showModal();
      if (restoring !== true) history.pushState({ sumiCompare: true }, '');
      if (!started) {
        started = true;
        load(0, location.pathname + location.search);
        setTarget(target);
      }
    };
    $$('[data-sumi-compare]').forEach(function (b) { b.addEventListener('click', function () { openCompare(); }); });
    $('[data-close]', cmp).addEventListener('click', function () { cmp.close(); });
    $$('.sumi-compare-switch button', cmp).forEach(function (b) { b.addEventListener('click', function () { show(+b.dataset.pane); }); });
    if (langSel) langSel.addEventListener('change', function () { setTarget(+langSel.value); });
    syncBox.addEventListener('change', function () {
      store.set('compare-sync', syncBox.checked ? '1' : '0');
      follow();
    });
    // Back closes the reader, and closing it takes its history entry away.
    cmp.addEventListener('close', function () { if (history.state && history.state.sumiCompare) history.back(); });
    window.addEventListener('popstate', function () {
      if (history.state && history.state.sumiCompare) openCompare(true);
      else if (cmp.open) cmp.close();
    });
    if (history.state && history.state.sumiCompare) openCompare(true);
  }

  /* ── Page feedback ─────────────────────────────────────────────────── */
  // Sent to whichever analytics is on the page, and as a `sumi:feedback` event.
  $$('.sumi-feedback').forEach(function (form) {
    if (inPane) return;
    form.hidden = false;
    var note = $('.sumi-feedback-note', form);
    $$('.sumi-feedback-btn', form).forEach(function (b) {
      b.addEventListener('click', function () {
        var value = isNaN(+b.dataset.value) ? b.dataset.value : +b.dataset.value;
        var page = location.pathname;
        try {
          if (typeof window.gtag === 'function') window.gtag('event', 'feedback', { event_category: 'feedback', event_label: page, value: value });
          if (typeof window.plausible === 'function') window.plausible('Feedback', { props: { page: page, rating: String(value) } });
          if (window.umami && typeof window.umami.track === 'function') window.umami.track('feedback', { page: page, rating: value });
        } catch (err) {}
        doc.dispatchEvent(new CustomEvent('sumi:feedback', { detail: { page: page, value: value } }));
        $$('.sumi-feedback-btn', form).forEach(function (x) { x.disabled = true; x.setAttribute('aria-pressed', String(x === b)); });
        // The note is the site author's HTML; {title} and {url} are filled in, as in Material.
        note.innerHTML = (b.dataset.note || '')
          .replace(/\{title\}/g, encodeURIComponent(doc.title))
          .replace(/\{url\}/g, encodeURIComponent(location.href));
        form.classList.add('is-done');
      });
    });
  });

  /* ── Comments (Giscus, lazy) ───────────────────────────────────────── */
  var giscus = inPane ? null : $('.sumi-giscus');
  if (giscus) {
    var giscusTheme = function () { return root.dataset.theme === 'dark' ? giscus.dataset.themeDark : giscus.dataset.themeLight; };
    whenNear([giscus], function () {
      var s = doc.createElement('script');
      s.src = 'https://giscus.app/client.js';
      s.async = true; s.crossOrigin = 'anonymous';
      ['repo', 'repoId', 'category', 'categoryId', 'mapping', 'strict', 'reactionsEnabled', 'inputPosition', 'lang'].forEach(function (k) {
        if (giscus.dataset[k]) s.dataset[k] = giscus.dataset[k];
      });
      s.dataset.emitMetadata = '0';
      s.dataset.loading = 'lazy';
      s.dataset.theme = giscusTheme();
      giscus.appendChild(s);
    });
    listeners.push(function () {
      var f = $('iframe.giscus-frame', giscus);
      if (f && f.contentWindow) f.contentWindow.postMessage({ giscus: { setConfig: { theme: giscusTheme() } } }, 'https://giscus.app');
    });
  }

  /* ── Table reader ──────────────────────────────────────────────────── */
  // A table wider than the column, or one marked {.expand}, can open full screen.
  var tableView = null;
  var openTable = function (wrap) {
    if (!tableView) {
      tableView = doc.createElement('dialog');
      tableView.className = 'sumi-table-view';
      tableView.setAttribute('aria-label', t('table_expand'));
      tableView.innerHTML = '<button type="button" class="sumi-icon-btn sumi-table-view-close" data-close aria-label="' + t('close') + '" title="' + t('close') + '">' + svg('x') + '</button><div class="sumi-table-view-body sumi-prose"></div>';
      doc.body.appendChild(tableView);
      tableView.addEventListener('click', function (e) {
        if (e.target === tableView || e.target.closest('[data-close]')) tableView.close();
      });
    }
    var body = $('.sumi-table-view-body', tableView);
    body.innerHTML = '';
    var copy = wrap.cloneNode(true);
    copy.classList.remove('sumi-table--wide');
    body.appendChild(copy);
    tableView.showModal();
  };
  var tableTools = function (wrap) {
    var next = wrap.nextElementSibling;
    var has = next && next.classList.contains('sumi-table-tools');
    var want = wrap.classList.contains('sumi-table--expand') || wrap.scrollWidth > wrap.clientWidth + 2;
    if (has || !want) return;
    var bar = doc.createElement('div');
    bar.className = 'sumi-table-tools';
    var b = doc.createElement('button');
    b.type = 'button'; b.className = 'sumi-table-expand';
    b.innerHTML = svg('maximize-2') + '<span>' + t('table_expand') + '</span>';
    b.addEventListener('click', function () { openTable(wrap); });
    bar.appendChild(b);
    wrap.parentNode.insertBefore(bar, wrap.nextSibling);
  };
  var tables = inPane ? [] : $$('.sumi-content .sumi-table');
  if (tables.length) {
    tables.forEach(tableTools);
    if ('ResizeObserver' in window) {
      var tro = new ResizeObserver(function (entries) { entries.forEach(function (en) { tableTools(en.target); }); });
      tables.forEach(function (w) { tro.observe(w); });
    }
  }

  /* ── Help dialog ───────────────────────────────────────────────────── */
  var help = $('.sumi-help');
  function openHelp() { if (help && !help.open) help.showModal(); }
  $$('[data-sumi-help]').forEach(function (b) { b.addEventListener('click', openHelp); });
  if (help) {
    $('[data-close]', help).addEventListener('click', function () { help.close(); });
    help.addEventListener('click', function (e) { if (e.target === help) help.close(); });
  }

  /* ── Keyboard ──────────────────────────────────────────────────────── */
  doc.addEventListener('keydown', function (e) {
    if ((e.metaKey || e.ctrlKey) && !e.altKey && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      if (pal && pal.open) pal.close(); else openPalette();
      return;
    }
    if (e.key === 'Escape') { closeMenus(); setDrawer(false); return; }
    if (S.keyboard === false || typing(e) || e.metaKey || e.ctrlKey || e.altKey) return;
    if ($('dialog[open]')) return;
    switch (e.key) {
      case '/': e.preventDefault(); openPalette(); break;
      case '>': e.preventDefault(); openPalette('>'); break;
      case 't': toggleTheme(); break;
      case '[': if (S.prev) location.href = S.prev; break;
      case ']': if (S.next) location.href = S.next; break;
      case '?': openHelp(); break;
      case 'b': if (openCompare) openCompare(); break;
      case 'j': case 'k': {
        if (!headings.length) break;
        var y = (parseInt(getComputedStyle(root).getPropertyValue('--sumi-header-h'), 10) || 60) + 30;
        var target = null;
        if (e.key === 'j') target = headings.find(function (h) { return h.getBoundingClientRect().top > y + 2; });
        else for (var i = headings.length - 1; i >= 0; i--) if (headings[i].getBoundingClientRect().top < y - 2) { target = headings[i]; break; }
        if (target) { target.scrollIntoView({ behavior: 'smooth' }); history.replaceState(null, '', '#' + target.id); }
        break;
      }
    }
  });
})();
