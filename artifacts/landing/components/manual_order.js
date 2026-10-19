/* Sentinel AI — Manual Order (paper).
   Honest, client-side wiring of the right-hand order form:
     - Entry = live BTC/USDT price (reused from trading_chart.js via `btc:price`,
       with a Binance REST fallback — no second WebSocket).
     - Direction = real agent signals from agent_sidecar.py /agents (127.0.0.1:8791).
     - SL price / TP1 / TP2 / Risk:Reward / EWMA vol = computed from entry + SL%.
     - Position size / Exposure / Margin / VaR / CVaR = computed once "Equity (paper $)"
       is entered (equity is unknown in this landing — no account system).
     - EXECUTE records a paper order to localStorage (append-only), never an exchange.
     - Hold resets the form.
   Nothing is fabricated: missing data renders "—" + a console reason.
*/
(function () {
  'use strict';

  var AGENTS_URL = 'http://127.0.0.1:8791/agents';
  var PRICE_URL = 'https://data-api.binance.vision/api/v3/ticker/price?symbol=BTCUSDT';
  var AGENTS_POLL_MS = 8000;
  var PRICE_FALLBACK_MS = 15000;
  var STALE_MS = 10000;
  var STORE_KEY = 'sentinel_manual_orders';

  var RISK_PCT = 0.005;          // 0.5% of equity at risk (matches the label)
  var DEFAULT_SL_PCT = 2;        // %
  var DEFAULT_LEVERAGE = 2;      // user input, default 2x
  var MAX_LEVERAGE = 10;
  var EWMA_LAMBDA = 0.94;

  var state = {
    dir: 'long',                 // long | short
    price: null,                 // latest close
    priceTs: 0,                  // Date.now() of last price (live path)
    agents: [],
    summary: null,
    equity: null,                // null until user types it
    slPct: DEFAULT_SL_PCT,
    leverage: DEFAULT_LEVERAGE,
    tp1Dirty: false,             // user overrode TP1
    tp2Dirty: false,
    ewma: null,
    size: null
  };

  var $ = function (id) { return document.getElementById(id); };

  var el = {
    osub: $('mo-osub'),
    osubText: $('mo-osub-text'),
    status: $('mo-status'),
    longAgents: $('mo-long-agents'),
    shortAgents: $('mo-short-agents'),
    entry: $('mo-entry'),
    equity: $('mo-equity'),
    size: $('mo-size'),
    slPct: $('mo-sl-pct'),
    slPrice: $('mo-sl-price'),
    tp1: $('mo-tp1'),
    tp2: $('mo-tp2'),
    leverage: $('mo-leverage'),
    rr: $('mo-rr'),
    metrics: $('mo-metrics')
  };

  function log() {
    var args = Array.prototype.slice.call(arguments);
    args.unshift('[manual_order]');
    if (window.console && console.log) console.log.apply(console, args);
  }

  function fmt(n, dp) {
    if (n == null || !isFinite(n)) return '—';
    return n.toLocaleString('en-US', { minimumFractionDigits: dp, maximumFractionDigits: dp });
  }
  function money(n, dp) {
    return (n == null || !isFinite(n)) ? '—' : ('$' + fmt(n, dp || 2));
  }

  // ---------------- price ----------------
  function onPrice(p, ts) {
    if (p == null || !isFinite(p)) return;
    state.price = p;
    state.priceTs = ts || Date.now();
    if (el.entry) el.entry.value = '$' + fmt(p, 2);
    // entry changed -> TP defaults re-derive from SL%
    state.tp1Dirty = false;
    state.tp2Dirty = false;
    recalcRisk();
    renderStatus();
  }

  window.addEventListener('btc:price', function (e) {
    if (e && e.detail && e.detail.price != null) onPrice(e.detail.price, Date.now());
  });

  function fallbackPrice() {
    // Only poll if the chart is not feeding us (missing or stale).
    if (state.price && Date.now() - state.priceTs < STALE_MS) return;
    fetch(PRICE_URL)
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) { if (d && d.price != null) onPrice(parseFloat(d.price), Date.now()); })
      .catch(function (err) { log('price fallback failed:', err && err.message); });
  }

  // ---------------- agents ----------------
  function fetchAgents() {
    if (document.hidden) return;
    fetch(AGENTS_URL)
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) {
        state.agents = (d && d.agents) ? d.agents : [];
        state.summary = (d && d.summary) ? d.summary : null;
        renderAgents();
        renderStatus();
      })
      .catch(function (err) {
        state.summary = null;
        log('agents unreachable:', err && err.message);
        renderAgents();
        renderStatus();
      });
  }

  function renderAgents() {
    var long = [], short = [];
    state.agents.forEach(function (a) {
      var s = (a.signal || '').toUpperCase();
      var name = a.agent;
      if (a.status !== 'ok') {
        name += ' ' + (a.status === 'no_data' ? 'no data' : 'error');
        long.push(name);
        short.push(name);
      } else if (s.indexOf('LONG') >= 0) {
        long.push(name + ' LONG ' + a.confidence);
        short.push(name + ' idle');
      } else if (s.indexOf('SHORT') >= 0) {
        short.push(name + ' SHORT ' + a.confidence);
        long.push(name + ' idle');
      } else {
        long.push(name + ' NEUTRAL ' + a.confidence);
        short.push(name + ' NEUTRAL ' + a.confidence);
      }
    });
    if (el.longAgents) el.longAgents.textContent = long.length ? long.join(' · ') : 'no data';
    if (el.shortAgents) el.shortAgents.textContent = short.length ? short.join(' · ') : 'no data';

    if (el.osubText) {
      var s = state.summary;
      var dec = s ? s.decision : '—';
      var act = s ? (s.active + ' of ' + s.total + ' active') : 'agents offline';
      var coh = (s && s.coherence != null) ? ('coherence ' + s.coherence) : 'coherence —';
      var vol = (state.ewma != null) ? ('vol ' + (state.ewma * 100).toFixed(2) + '%') : 'vol —';
      el.osubText.textContent = 'Symbol BTC/USDT · Decision ' + dec + ' · ' + act + ' · ' + coh + ' · ' + vol;
    }
  }

  // ---------------- risk math ----------------
  function ewmaVol() {
    var candles = (window.SentinelChart && window.SentinelChart.getCandles) ? window.SentinelChart.getCandles() : null;
    if (!candles || candles.length < 3) return null;
    var rets = [];
    for (var i = 1; i < candles.length; i++) {
      var p0 = candles[i - 1].close, p1 = candles[i].close;
      if (p0 > 0 && p1 > 0) rets.push(Math.log(p1 / p0));
    }
    if (rets.length < 2) return null;
    var v = rets[0] * rets[0];
    for (var j = 1; j < rets.length; j++) v = EWMA_LAMBDA * v + (1 - EWMA_LAMBDA) * rets[j] * rets[j];
    return Math.sqrt(v);
  }

  function riskEngine() {
    if (state.slPct == null || state.slPct <= 0) return 'blocked';
    if (state.slPct < 0.1) return 'warning';
    if (state.leverage > MAX_LEVERAGE) return 'warning';
    return 'ok';
  }

  function recalcRisk() {
    var entry = state.price;
    var sl = state.slPct / 100;
    var dir = state.dir;
    var slPrice = null, tp1auto = null, tp2auto = null, rr = null;

    if (entry && sl > 0) {
      slPrice = (dir === 'long') ? entry * (1 - sl) : entry * (1 + sl);
      tp1auto = (dir === 'long') ? entry * (1 + 2 * sl) : entry * (1 - 2 * sl);
      tp2auto = (dir === 'long') ? entry * (1 + 3 * sl) : entry * (1 - 3 * sl);
    }

    state.ewma = ewmaVol();

    var size = null, margin = null, var95 = null, cvar = null;
    if (state.equity != null && state.leverage > 0 && sl > 0) {
      size = state.equity * RISK_PCT / (sl * state.leverage);
      margin = size / state.leverage;
      if (state.ewma != null) {
        var95 = size * 1.65 * state.ewma;
        cvar = var95 * 1.4;
      }
    }
    state.size = size;

    // SL price
    if (el.slPrice) el.slPrice.textContent = slPrice ? money(slPrice, 2) : '—';

    // TP defaults (only overwrite if user hasn't manually edited)
    if (!state.tp1Dirty && el.tp1) el.tp1.value = tp1auto ? fmt(tp1auto, 2) : '';
    if (!state.tp2Dirty && el.tp2) el.tp2.value = tp2auto ? fmt(tp2auto, 2) : '';

    // Risk:Reward from current TP1 vs SL distance
    var tp1v = el.tp1 ? parseFloat(el.tp1.value) : NaN;
    if (entry && slPrice && isFinite(tp1v) && tp1v > 0 && Math.abs(entry - slPrice) > 0) {
      var reward = Math.abs(tp1v - entry);
      var risk = Math.abs(entry - slPrice);
      if (risk > 0) rr = reward / risk;
    }
    if (el.rr) el.rr.textContent = rr != null ? ('Risk/Reward 1:' + rr.toFixed(2)) : 'Risk/Reward —';

    // size
    if (el.size) {
      el.size.value = size != null ? money(size, 0) : '$— (equity unknown)';
    }

    // metrics line
    if (el.metrics) {
      var parts = [];
      parts.push('Exposure ' + (size != null ? money(size, 0) : '— (equity unknown)'));
      parts.push('Margin ' + (margin != null ? money(margin, 0) : '—'));
      parts.push('VaR 95% ' + (var95 != null ? money(var95, 2) : '—'));
      parts.push('CVaR ' + (cvar != null ? money(cvar, 2) : '—'));
      parts.push('EWMA vol ' + (state.ewma != null ? (state.ewma * 100).toFixed(2) + '%' : '—'));
      parts.push('rolling correlation —');   // no BTC vs SPX/DXY source in this landing
      parts.push('PCA factor exposures —');  // no factor model in this landing
      parts.push('Risk Engine ' + riskEngine());
      el.metrics.textContent = parts.join(' · ');
    }

    renderAgents(); // refresh osub vol
    renderStatus();
  }

  // ---------------- observability ----------------
  function renderStatus() {
    var s, color;
    if (!state.summary) { s = 'no agents'; color = 'var(--red)'; }
    else if (state.price == null) { s = 'no price'; color = '#FBBF24'; }
    else if (Date.now() - state.priceTs > STALE_MS) { s = 'stale'; color = '#FBBF24'; }
    else { s = 'live'; color = 'var(--green)'; }
    if (el.status) { el.status.textContent = 'MO: ' + s; el.status.style.color = color; }
  }

  // ---------------- actions ----------------
  function record(kind, data) {
    try {
      var arr = JSON.parse(localStorage.getItem(STORE_KEY) || '[]');
      arr.push({ ts: new Date().toISOString(), kind: kind, data: data });
      localStorage.setItem(STORE_KEY, JSON.stringify(arr));
      log(kind + ' recorded (append-only localStorage)', data);
      return true;
    } catch (e) {
      log('record failed:', e && e.message);
      return false;
    }
  }

  function currentOrder() {
    return {
      symbol: 'BTC/USDT',
      direction: state.dir.toUpperCase(),
      entry: state.price,
      size_notional: state.size,
      sl_pct: state.slPct,
      sl_price: (function () {
        var e = state.price, s = state.slPct / 100;
        if (!e || !s) return null;
        return state.dir === 'long' ? e * (1 - s) : e * (1 + s);
      })(),
      tp1: el.tp1 ? parseFloat(el.tp1.value) || null : null,
      tp2: el.tp2 ? parseFloat(el.tp2.value) || null : null,
      leverage: state.leverage,
      equity: state.equity
    };
  }

  function onExecute() {
    var o = currentOrder();
    record('EXECUTE (paper)', o);
    if (window.toast) {
      window.toast('Paper order recorded · ' + o.direction + ' · entry ' + (o.entry ? money(o.entry, 2) : '—') + ' · SL ' + o.sl_pct + '% · not sent to exchange');
    }
    log('EXECUTE is paper-only — no exchange order was placed.');
  }

  function onHold() {
    record('HOLD', { note: 'deliberate wait — form reset' });
    resetForm();
    if (window.toast) window.toast('Hold — deliberate wait · form reset');
  }

  function resetForm() {
    state.slPct = DEFAULT_SL_PCT;
    state.leverage = DEFAULT_LEVERAGE;
    state.tp1Dirty = false;
    state.tp2Dirty = false;
    if (el.slPct) el.slPct.value = String(DEFAULT_SL_PCT);
    if (el.leverage) el.leverage.value = String(DEFAULT_LEVERAGE);
    if (el.equity) state.equity = parseFloat(el.equity.value) > 0 ? parseFloat(el.equity.value) : null;
    recalcRisk();
  }

  // ---------------- wiring ----------------
  function bind() {
    var dirBtns = document.querySelectorAll('.dir-btn[data-dir]');
    dirBtns.forEach ? dirBtns.forEach(function (b) {
      b.addEventListener('click', function () {
        state.dir = b.getAttribute('data-dir');
        dirBtns.forEach(function (x) { x.classList.toggle('on', x === b); });
        state.tp1Dirty = false; state.tp2Dirty = false;
        recalcRisk();
      });
    }) : Array.prototype.forEach.call(dirBtns, function (b) {
      b.addEventListener('click', function () {
        state.dir = b.getAttribute('data-dir');
        Array.prototype.forEach.call(dirBtns, function (x) { x.classList.toggle('on', x === b); });
        state.tp1Dirty = false; state.tp2Dirty = false;
        recalcRisk();
      });
    });

    if (el.slPct) el.slPct.addEventListener('input', function () {
      state.slPct = parseFloat(el.slPct.value) || 0;
      state.tp1Dirty = false; state.tp2Dirty = false;
      recalcRisk();
    });
    if (el.leverage) el.leverage.addEventListener('input', function () {
      state.leverage = parseFloat(el.leverage.value) || 0;
      recalcRisk();
    });
    if (el.equity) el.equity.addEventListener('input', function () {
      var v = parseFloat(el.equity.value);
      state.equity = (v > 0) ? v : null;
      recalcRisk();
    });
    if (el.tp1) el.tp1.addEventListener('input', function () {
      state.tp1Dirty = true;
      recalcRisk();
    });
    if (el.tp2) el.tp2.addEventListener('input', function () {
      state.tp2Dirty = true;
      recalcRisk();
    });

    var ex = $('mo-execute');
    if (ex) ex.addEventListener('click', onExecute);
    var hold = $('mo-hold');
    if (hold) hold.addEventListener('click', onHold);
  }

  // ---------------- boot ----------------
  if (!el.entry) { log('fields missing — manual_order not initialized'); return; }

  // Seed price from the chart if already live (no need to wait for the next candle).
  if (window.SentinelChart && typeof window.SentinelChart.getLastPrice === 'function') {
    var lp = window.SentinelChart.getLastPrice();
    if (lp != null) onPrice(lp, Date.now());
  }

  bind();
  fetchAgents();
  renderStatus();

  // Static placeholders — honest labels (no live quota/cost/policy/ledger feed here).
  log('Check 1/2/3 + EnterpriseDecisionGate: static placeholder (no live quota/cost/policy feed in this landing).');
  log('acceptance footer hash/metrics: static (0/3400 tenants · 76 endpoints · 86 branches · 19 workflows · commit hashes) — not a live ledger.');

  setInterval(fetchAgents, AGENTS_POLL_MS);
  setInterval(fallbackPrice, PRICE_FALLBACK_MS);
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden) { fetchAgents(); fallbackPrice(); }
  });
})();
