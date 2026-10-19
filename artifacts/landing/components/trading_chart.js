/* Sentinel AI — trading chart: candlestick + volume + SMA20/50 + RSI14 + HUD.
   Data: Binance kline WebSocket + REST history (data-api.binance.vision — CORS-enabled).
   Timeframes: 1m / 5m / 1h / 4h / 1D (switchable, mapped to Binance intervals).
   Self-contained: lightweight-charts loaded locally. Honesty: no synthetic candles.
*/
(function () {
  'use strict';
  if (typeof LightweightCharts === 'undefined') return;

  var SYMBOL = 'BTCUSDT';
  var AGENTS_URL = 'http://127.0.0.1:8791/agents';
  var INTERVAL_MAP = { '1m': '1m', '5m': '5m', '1h': '1h', '4h': '4h', '1D': '1d' };
  var currentInterval = '1h';                 // single source of truth (matches the "on" button)

  var candles = [];                            // [{time, open, high, low, close, volume}]
  var activeWs = null;
  var activeAbort = null;
  var reconnectDelay = 1000;
  var debounceTimer = null;
  var updCount = 0, updWindowStart = Date.now();
  var lastCandleTime = null;

  var $c = document.getElementById('chart-container');
  var $r = document.getElementById('rsi-container');
  if (!$c) return;

  var chart = LightweightCharts.createChart($c, {
    layout: { background: { color: '#000000' }, textColor: '#8B949E', fontSize: 11 },
    grid: { vertLines: { color: 'rgba(0,229,255,0.05)' }, horzLines: { color: 'rgba(0,229,255,0.05)' } },
    rightPriceScale: { borderColor: 'rgba(0,229,255,0.15)' },
    timeScale: { borderColor: 'rgba(0,229,255,0.15)', timeVisible: true, secondsVisible: false, rightOffset: 5, barSpacing: 8, fixLeftEdge: false, fixRightEdge: false },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
  });
  var candleSeries = chart.addCandlestickSeries({
    upColor: '#22c55e', downColor: '#ef4444', borderVisible: false,
    wickUpColor: '#22c55e', wickDownColor: '#ef4444',
  });
  var volumeSeries = chart.addHistogramSeries({ priceScaleId: 'volume', priceFormat: { type: 'volume' } });
  chart.priceScale('volume').applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });
  chart.priceScale('right').applyOptions({ scaleMargins: { top: 0.08, bottom: 0.08 } });
  var sma20Series = chart.addLineSeries({ color: '#00E5FF', lineWidth: 1, priceLineVisible: false });
  var sma50Series = chart.addLineSeries({ color: '#a855f7', lineWidth: 1, priceLineVisible: false });

  var rsiChart = null, rsiSeries = null;
  if ($r) {
    rsiChart = LightweightCharts.createChart($r, {
      layout: { background: { color: '#000000' }, textColor: '#8B949E', fontSize: 10 },
      grid: { vertLines: { color: 'rgba(0,229,255,0.05)' }, horzLines: { color: 'rgba(0,229,255,0.05)' } },
      rightPriceScale: { borderColor: 'rgba(0,229,255,0.15)' },
      timeScale: { visible: false },
    });
    rsiSeries = rsiChart.addLineSeries({ color: '#fbbf24', lineWidth: 1, priceLineVisible: false });
    rsiSeries.createPriceLine({ price: 70, color: '#ef4444', lineStyle: LightweightCharts.LineStyle.Dashed, lineWidth: 1, title: '' });
    rsiSeries.createPriceLine({ price: 30, color: '#22c55e', lineStyle: LightweightCharts.LineStyle.Dashed, lineWidth: 1, title: '' });
    rsiChart.priceScale('right').applyOptions({ scaleMargins: { top: 0.1, bottom: 0.1 } });
  }

  function el(id) { return document.getElementById(id); }
  function hud(id, txt, color) { var e = el(id); if (e) { e.textContent = txt; if (color) e.style.color = color; } }

  function apiInterval(ui) { return INTERVAL_MAP[ui] || ui.toLowerCase(); }
  function wsUrl(i) { return 'wss://stream.binance.com:9443/ws/btcusdt@kline_' + apiInterval(i); }
  function restUrl(i) { return 'https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=' + apiInterval(i) + '&limit=500'; }

  function setConn(status, color) {
    hud('hud-conn', status, color);
    var last = candles.length ? candles[candles.length - 1].close : null;
    var px = document.querySelector('.chart-px');
    if (px) { px.textContent = (status === 'live' && last) ? ('$' + last.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' · live') : status; px.style.color = color; }
    if (last) {
      var cur = document.querySelector('.pos-metric .v.pos');
      if (cur) cur.textContent = '$' + last.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
  }

  function fmtTime(t) { return t ? new Date(t * 1000).toISOString().slice(11, 19) + 'Z' : '—'; }

  function sma(n) {
    if (candles.length < n) return null;
    var s = 0; for (var i = candles.length - n; i < candles.length; i++) s += candles[i].close;
    return s / n;
  }
  function rsi(period) {
    period = period || 14;
    if (candles.length < period + 1) return null;
    var g = 0, l = 0;
    for (var i = candles.length - period; i < candles.length; i++) {
      var d = candles[i].close - candles[i - 1].close;
      if (d >= 0) g += d; else l -= d;
    }
    if (l === 0) return 100;
    return 100 - (100 / (1 + (g / period) / (l / period)));
  }

  function recomputeIndicators() {
    if (!candles.length) return;
    var t = candles[candles.length - 1].time;
    var s20 = sma(20), s50 = sma(50), r = rsi(14);
    if (s20 !== null) sma20Series.update({ time: t, value: s20 });
    if (s50 !== null) sma50Series.update({ time: t, value: s50 });
    if (r !== null && rsiSeries) rsiSeries.update({ time: t, value: r });
  }

  function ups() {
    var now = Date.now();
    if (now - updWindowStart >= 1000) { updCount = 0; updWindowStart = now; }
    updCount++;
    hud('hud-ups', updCount + '/s');
  }

  function onCandle(c) {
    var last = candles.length ? candles[candles.length - 1] : null;
    var volColor = c.close >= c.open ? 'rgba(34,197,94,0.5)' : 'rgba(239,68,68,0.5)';
    if (last && last.time === c.time) {
      candles[candles.length - 1] = c;
      candleSeries.update(c);
      volumeSeries.update({ time: c.time, value: c.volume, color: volColor });
    } else {
      candles.push(c);
      if (candles.length > 1000) candles.shift();
      candleSeries.update(c);
      volumeSeries.update({ time: c.time, value: c.volume, color: volColor });
    }
    lastCandleTime = c.time;
    hud('hud-time', fmtTime(c.time));
    setConn('live', '#22c55e');
    ups();
    recomputeIndicators();
    publishPrice();
  }

  function applyHistory(rows) {
    candles = [];
    var data = [], vol = [];
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i];
      var c = { time: Math.floor(r[0] / 1000), open: +r[1], high: +r[2], low: +r[3], close: +r[4], volume: +r[5] };
      candles.push(c);
      data.push(c);
      vol.push({ time: c.time, value: c.volume, color: c.close >= c.open ? 'rgba(34,197,94,0.5)' : 'rgba(239,68,68,0.5)' });
    }
    candleSeries.setData(data);
    volumeSeries.setData(vol);

    var s20 = [], s50 = [];
    for (var j = 0; j < data.length; j++) {
      var a20 = 0, a50 = 0;
      if (j >= 19) { for (var k = j - 19; k <= j; k++) a20 += data[k].close; s20.push({ time: data[j].time, value: a20 / 20 }); }
      if (j >= 49) { for (var m = j - 49; m <= j; m++) a50 += data[m].close; s50.push({ time: data[j].time, value: a50 / 50 }); }
    }
    sma20Series.setData(s20);
    sma50Series.setData(s50);

    if (rsiSeries) {
      var rdata = [];
      for (var q = 14; q < data.length; q++) {
        var g = 0, l = 0;
        for (var w = q - 13; w <= q; w++) { var d = data[w].close - data[w - 1].close; if (d >= 0) g += d; else l -= d; }
        var rv = l === 0 ? 100 : 100 - (100 / (1 + (g / 14) / (l / 14)));
        rdata.push({ time: data[q].time, value: rv });
      }
      rsiSeries.setData(rdata);
    }

    if (data.length) { lastCandleTime = data[data.length - 1].time; hud('hud-time', fmtTime(lastCandleTime)); }
    chart.timeScale().fitContent();
    if (rsiChart) rsiChart.timeScale().fitContent();
    // Show the most recent ~120 candles (tighter price range, non-squished candles).
    // User can scroll back for the full history.
    if (data.length > 120) {
      chart.timeScale().setVisibleLogicalRange({ from: data.length - 120, to: data.length + 1 });
      if (rsiChart) rsiChart.timeScale().setVisibleLogicalRange({ from: data.length - 120, to: data.length + 1 });
    }
    publishPrice();
  }

  // Publish the latest price to other modules without opening a second WebSocket.
  function publishPrice() {
    var last = candles.length ? candles[candles.length - 1].close : null;
    if (last == null) return;
    try {
      window.dispatchEvent(new CustomEvent('btc:price', {
        detail: { price: last, time: candles[candles.length - 1].time, interval: currentInterval }
      }));
    } catch (e) {}
  }

  // Read-only surface for manual_order.js and others (no WS duplication).
  window.SentinelChart = {
    getLastPrice: function () { return candles.length ? candles[candles.length - 1].close : null; },
    getCandles: function () { return candles; },
    getInterval: function () { return currentInterval; }
  };

  function loadHistory(interval) {
    if (activeAbort) { try { activeAbort.abort(); } catch (e) {} }
    activeAbort = new AbortController();
    candles = [];
    hud('hud-conn', 'loading ' + interval, '#FBBF24');
    var card = document.querySelector('.chart-card');
    if (card) card.style.opacity = '0.5';
    fetch(restUrl(interval), { signal: activeAbort.signal })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (rows) { applyHistory(rows); })
      .catch(function (err) { if (err && err.name !== 'AbortError') hud('hud-conn', 'no history (CORS?)', '#ef4444'); })
      .finally(function () { if (card) card.style.opacity = ''; });
  }

  function subscribeKlines(interval) {
    if (activeWs) { try { activeWs.close(); } catch (e) {} activeWs = null; }
    try {
      activeWs = new WebSocket(wsUrl(interval));
      activeWs.onopen = function () { reconnectDelay = 1000; setConn('live', '#22c55e'); };
      activeWs.onmessage = function (ev) {
        try {
          var m = JSON.parse(ev.data);
          if (m && m.k) {
            var k = m.k;
            var t0 = performance.now();
            onCandle({ time: Math.floor(k.t / 1000), open: +k.o, high: +k.h, low: +k.l, close: +k.c, volume: +k.v });
            hud('hud-lat', Math.round(performance.now() - t0));
          }
        } catch (e) {}
      };
      activeWs.onclose = function () { activeWs = null; setConn('reconnecting', '#FBBF24'); scheduleReconnect(interval); };
      activeWs.onerror = function () { try { activeWs.close(); } catch (e) {} };
    } catch (e) { scheduleReconnect(interval); }
  }

  function scheduleReconnect(interval) {
    setTimeout(function () { loadHistory(interval); subscribeKlines(interval); }, reconnectDelay);
    reconnectDelay = Math.min(reconnectDelay * 2, 30000);
  }

  function setIntervalTf(interval) {
    if (interval === currentInterval) return;
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(function () {
      currentInterval = interval;
      document.querySelectorAll('.chart-tf button').forEach(function (b) {
        b.classList.toggle('on', b.textContent.trim() === interval);
      });
      hud('hud-interval', interval);
      reconnectDelay = 1000;
      loadHistory(interval);
      subscribeKlines(interval);
    }, 250);
  }

  function pollAgents() {
    if (document.hidden) return;
    fetch(AGENTS_URL)
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) {
        if (!d || !d.summary) return;
        hud('hud-agents', d.summary.active + ' of ' + d.summary.total);
        hud('hud-decision', d.summary.decision + (d.summary.coherence !== null ? ' · ' + d.summary.coherence : ''));
        var markers = [];
        d.agents.forEach(function (a) {
          if (a.status === 'ok' && a.confidence >= 50 && candles.length) {
            var sig = (a.signal || '').toUpperCase();
            if (sig.indexOf('LONG') >= 0 || sig.indexOf('BUY') >= 0) {
              markers.push({ time: candles[candles.length - 1].time, position: 'belowBar', color: '#22c55e', shape: 'arrowUp', text: a.agent.slice(0, 4) });
            } else if (sig.indexOf('SHORT') >= 0 || sig.indexOf('SELL') >= 0) {
              markers.push({ time: candles[candles.length - 1].time, position: 'aboveBar', color: '#ef4444', shape: 'arrowDown', text: a.agent.slice(0, 4) });
            }
          }
        });
        candleSeries.setMarkers(markers);
      })
      .catch(function () { hud('hud-agents', 'offline', '#ef4444'); });
  }

  // Delegated click handling (capture phase — robust against re-renders / z-index / overlay quirks)
  document.addEventListener('click', function (e) {
    var t = e.target;
    if (!t || typeof t.closest !== 'function') return;
    var tf = t.closest('.chart-tf button');
    if (tf) { setIntervalTf(tf.getAttribute('data-interval') || tf.textContent.trim()); return; }
    if (t.closest('#chart-fullscreen')) { toggleFullscreen(); }
  }, true);

  // ---- fullscreen ----
  var $fsBtn = document.getElementById('chart-fullscreen');
  var $chartCard = document.querySelector('.chart-card');
  var fsMode = 'off';   // off | native | pseudo

  function setFsIcon(mode) {
    fsMode = mode;
    if (!$fsBtn) return;
    var active = mode !== 'off';
    var ex = $fsBtn.querySelector('.fs-expand');
    var co = $fsBtn.querySelector('.fs-compress');
    if (ex) ex.style.display = active ? 'none' : 'inline';
    if (co) co.style.display = active ? 'inline' : 'none';
    $fsBtn.setAttribute('aria-pressed', String(active));
    $fsBtn.title = active ? 'Exit fullscreen' : 'Fullscreen (F)';
    hud('hud-full', mode === 'native' ? 'on' : (mode === 'pseudo' ? 'pseudo' : 'off'),
        mode === 'off' ? undefined : '#22c55e');
  }

  function resizeChart() {
    requestAnimationFrame(function () {
      var c = document.getElementById('chart-container');
      if (c && chart) { chart.applyOptions({ width: c.clientWidth, height: c.clientHeight }); chart.timeScale().fitContent(); }
      var r = document.getElementById('rsi-container');
      if (r && rsiChart) { rsiChart.applyOptions({ width: r.clientWidth, height: r.clientHeight }); rsiChart.timeScale().fitContent(); }
    });
  }

  function nativeFsEnabled() {
    return !!(document.fullscreenEnabled && document.documentElement && document.documentElement.requestFullscreen);
  }

  function enterPseudo() {
    if (!$chartCard) return;
    $chartCard.classList.add('pseudo-fullscreen');
    setFsIcon('pseudo');
    resizeChart();
  }

  function enterFs() {
    if (!$chartCard) return;
    if (nativeFsEnabled()) {
      try {
        var p = $chartCard.requestFullscreen({ navigationUI: 'hide' });
        if (p && p.catch) p.catch(function () { enterPseudo(); });
      } catch (e) { enterPseudo(); }
    } else {
      enterPseudo();
    }
  }

  function exitFs() {
    if (fsMode === 'native' && document.fullscreenElement) {
      document.exitFullscreen().catch(function () {});
    } else {
      if ($chartCard) $chartCard.classList.remove('pseudo-fullscreen');
      setFsIcon('off');
      resizeChart();
    }
  }

  function toggleFullscreen() {
    if (fsMode !== 'off') exitFs(); else enterFs();
  }

  function onFullscreenChange() {
    if (document.fullscreenElement === $chartCard) {
      setFsIcon('native');
      resizeChart();
    } else if (fsMode === 'native') {
      setFsIcon('off');
      resizeChart();
    }
  }

  if ($fsBtn) {
    document.addEventListener('fullscreenchange', onFullscreenChange);
  }

  document.addEventListener('keydown', function (e) {
    if (e.key === 'f' || e.key === 'F') {
      var tag = (document.activeElement && document.activeElement.tagName) || '';
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;
      e.preventDefault();
      toggleFullscreen();
    }
    if (e.key === 'Escape' && fsMode === 'pseudo') {
      if ($chartCard) $chartCard.classList.remove('pseudo-fullscreen');
      setFsIcon('off');
      resizeChart();
    }
  });

  if (typeof ResizeObserver !== 'undefined') {
    var ro = new ResizeObserver(function () { resizeChart(); });
    var cc = document.getElementById('chart-container');
    var rc = document.getElementById('rsi-container');
    if (cc) ro.observe(cc);
    if (rc) ro.observe(rc);
  }

  // boot
  hud('hud-interval', currentInterval);
  setConn('connecting', '#FBBF24');
  loadHistory(currentInterval);
  subscribeKlines(currentInterval);
  setInterval(pollAgents, 8000);
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden) { pollAgents(); loadHistory(currentInterval); subscribeKlines(currentInterval); }
  });
})();
