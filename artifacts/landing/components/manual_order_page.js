/* Sentinel AI — Manual Order page (manual_order.html).
   Self-contained live wiring for the order panel:
     - last price / 24h vol / change  <- Binance ticker/24hr (REST)
     - best bid/ask + depth           <- Binance depth limit=20 (REST)
     - EWMA volatility                <- Binance klines 1h (REST), lambda 0.94
     - agents / decision / coherence  <- agent_sidecar.py /agents (127.0.0.1:8791)
   Honest: missing data -> "—", never fabricated. Paper only (no exchange order).
*/
(function () {
  'use strict';

  var AGENTS_URL = 'http://127.0.0.1:8791/agents';
  var TICKER_URL = 'https://data-api.binance.vision/api/v3/ticker/24hr?symbol=BTCUSDT';
  var DEPTH_URL = 'https://data-api.binance.vision/api/v3/depth?symbol=BTCUSDT&limit=20';
  var KLINES_URL = 'https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=120';
  var AGENTS_POLL_MS = 8000;
  var MARKET_POLL_MS = 5000;
  var KLINES_INTERVAL_MS = 90000;
  var EWMA_LAMBDA = 0.94;
  var STALE_MS = 15000;

  var state = {
    side: 'buy',
    type: 'limit',
    lastPrice: null,
    volume: null,
    changePct: null,
    bestBid: null,
    bestAsk: null,
    depthBtc: null,
    bidVol: null,
    askVol: null,
    ewma: null,
    agents: [],
    summary: null,
    equity: 1000000,          // paper "Available" already shown in the UI
    riskPct: 0.005,           // 0.5% equity -> $5,000 suggested max buy
    lastMarketTs: 0,
    lastAgentsTs: 0
  };

  function $id(id) { return document.getElementById(id); }
  function setText(id, txt) { var e = $id(id); if (e) e.textContent = txt; }
  function setVal(id, txt) { var e = $id(id); if (e) e.value = txt; }
  function log() {
    var a = Array.prototype.slice.call(arguments);
    a.unshift('[manual_order_page]');
    if (window.console && console.log) console.log.apply(console, a);
  }
  function num(n, dp) {
    if (n == null || !isFinite(n)) return '—';
    return n.toLocaleString('en-US', { minimumFractionDigits: dp || 2, maximumFractionDigits: dp || 2 });
  }
  function usd(n) { return (n == null || !isFinite(n)) ? '—' : ('$' + num(n, 2)); }
  function btc(n) { return (n == null || !isFinite(n)) ? '—' : (n.toLocaleString('en-US', { maximumFractionDigits: 8 }) + ' BTC'); }
  function cap(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : s; }

  // ---------------- data fetches ----------------
  function fetchTicker() {
    fetch(TICKER_URL)
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) {
        if (d.lastPrice == null) throw new Error('empty');
        state.lastPrice = parseFloat(d.lastPrice);
        state.volume = parseFloat(d.volume);
        state.changePct = parseFloat(d.priceChangePercent);
        state.lastMarketTs = Date.now();
        renderMarket();
      })
      .catch(function (err) { log('ticker failed:', err && err.message); renderStatus(); });
  }

  function fetchDepth() {
    fetch(DEPTH_URL)
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) {
        if (!d.bids || !d.bids.length || !d.asks || !d.asks.length) throw new Error('empty');
        state.bestBid = parseFloat(d.bids[0][0]);
        state.bestAsk = parseFloat(d.asks[0][0]);
        var bidVol = 0, askVol = 0;
        for (var i = 0; i < d.bids.length; i++) bidVol += parseFloat(d.bids[i][1]);
        for (var j = 0; j < d.asks.length; j++) askVol += parseFloat(d.asks[j][1]);
        state.bidVol = bidVol;
        state.askVol = askVol;
        state.depthBtc = bidVol + askVol;
        renderMarket();
      })
      .catch(function (err) { log('depth failed:', err && err.message); renderStatus(); });
  }

  var klinesInflight = false;
  function fetchKlines() {
    if (klinesInflight) return;                 // skip if previous request still in flight
    klinesInflight = true;
    fetch(KLINES_URL)
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (rows) {
        if (!rows || rows.length < 3) throw new Error('empty');
        var rets = [];
        for (var i = 1; i < rows.length; i++) {
          var p0 = parseFloat(rows[i - 1][4]), p1 = parseFloat(rows[i][4]);
          if (p0 > 0 && p1 > 0) rets.push(Math.log(p1 / p0));
        }
        if (rets.length < 2) throw new Error('no returns');
        var v = rets[0] * rets[0];
        for (var j = 1; j < rets.length; j++) v = EWMA_LAMBDA * v + (1 - EWMA_LAMBDA) * rets[j] * rets[j];
        state.ewma = Math.sqrt(v);
        log('klines updated · EWMA vol ' + (state.ewma * 100).toFixed(2) + '%');
        renderMarket();
      })
      .catch(function (err) { log('klines failed:', err && err.message); })
      .finally(function () { klinesInflight = false; });
  }

  function fetchAgents() {
    if (document.hidden) return;
    fetch(AGENTS_URL)
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) {
        state.agents = (d && d.agents) ? d.agents : [];
        state.summary = (d && d.summary) ? d.summary : null;
        state.lastAgentsTs = Date.now();
        renderAgents();
      })
      .catch(function (err) {
        state.summary = null;
        log('agents failed:', err && err.message);
        renderAgents();
      });
  }

  // ---------------- helpers ----------------
  function effectivePrice() {
    if (state.type === 'market') return state.lastPrice;
    var lp = parseFloat($id('limitPrice').value);
    return (isFinite(lp) && lp > 0) ? lp : null;   // limit requires an explicit price
  }
  function amount() { var v = parseFloat($id('amount').value); return (isFinite(v) && v >= 0) ? v : 0; }
  function spreadUsd() { return (state.bestBid != null && state.bestAsk != null) ? (state.bestAsk - state.bestBid) : null; }

  function vsMarketLabel() {
    if (state.type !== 'limit') return 'market';
    var lp = parseFloat($id('limitPrice').value);
    if (!isFinite(lp) || lp <= 0) return '—';
    if (state.bestBid == null || state.bestAsk == null) return '—';
    if (state.side === 'buy') {
      if (lp >= state.bestAsk) return 'aggressive (taker)';
      if (lp <= state.bestBid) return 'passive (maker)';
      return 'inside spread';
    }
    if (lp <= state.bestBid) return 'aggressive (taker)';
    if (lp >= state.bestAsk) return 'passive (maker)';
    return 'inside spread';
  }

  function depthLabel() {
    if (state.bidVol == null || state.askVol == null || state.askVol === 0) return '—';
    var ratio = state.bidVol / state.askVol;
    if (ratio < 0.5) return 'bid thinned';   // bid volume much smaller than ask -> bids thin
    if (ratio > 2) return 'ask thinned';     // ask volume much smaller than bid -> asks thin
    return 'balanced';
  }

  function agentLabel(key) {
    var a = null;
    for (var i = 0; i < state.agents.length; i++) if (state.agents[i].agent === key) { a = state.agents[i]; break; }
    if (!a) return '—';
    if (a.status !== 'ok') return a.agent + ' ' + (a.status === 'no_data' ? 'no data' : 'error');
    return a.agent + ' ' + (a.signal || '—') + (a.confidence != null ? ' ' + a.confidence : '');
  }

  // ---------------- rendering ----------------
  function renderMarket() {
    setText('mo-px', state.lastPrice ? '$' + num(state.lastPrice, 2) : '—');

    var ba = (state.bestBid != null && state.bestAsk != null) ? (num(state.bestBid, 2) + ' / ' + num(state.bestAsk, 2)) : '— / —';
    setText('mo-ctx-bidask', ba);
    setText('mo-ctx-depth', state.depthBtc != null ? (depthLabel() + ' · ' + num(state.depthBtc, 2) + ' BTC') : 'thinned —');
    setText('mo-ctx-volatility', state.ewma != null ? (state.ewma * 100).toFixed(2) + '%' : '—');
    setText('mo-ctx-vsmarket', vsMarketLabel());

    // limit price hint line
    setText('mo-limit-hint', 'Best bid/ask ' + ba + ' · Your price vs market ' + vsMarketLabel() + ' · editable levels · Move/Drag · focus cyan');

    // lm-note
    setText('mo-lm-note', (state.type === 'limit' ? 'Fills at your price or better' : 'Fills at market price') +
      ' · Best bid/ask ' + ba + ' · Your price vs market ' + vsMarketLabel() +
      ' · Depth ' + (state.depthBtc != null ? num(state.depthBtc, 2) + ' BTC' : '—') +
      ' · vol ' + (state.volume != null ? num(state.volume, 2) + ' BTC' : '—') +
      ' · Quant ' + agentLabel('quant'));

    renderCtx();
    recalc();
    renderExactOrder();
    renderStatus();
  }

  function renderCtx() {
    var s = state.summary;
    var dec = s ? s.decision : '—';
    var coh = (s && s.coherence != null) ? s.coherence : '—';
    var act = s ? (s.active + ' of ' + s.total + ' active') : 'agents offline';
    var spread = spreadUsd();
    setText('mo-ctx',
      'Market data live · spread ' + (spread != null ? num(spread, 2) + ' USD' : '—') +
      ' · tick 0.01 · step 0.00001 · platform defaults — paper account has no exchange limits' +
      ' · Decision ' + dec + ' · Coherence ' + coh + ' · ' + act);
  }

  function renderAgents() {
    var s = state.summary;
    var dec = s ? s.decision : '—';
    var coh = (s && s.coherence != null) ? s.coherence : '—';
    var act = s ? (s.active + ' of ' + s.total + ' active') : '0 of 6 active — agents offline';

    setText('mo-pill-decision', 'Decision ' + dec + ' · Coherence ' + coh);
    setText('mo-pill-active', act);
    setText('mo-ctx-decision', dec + ' · ' + act);
    setText('mo-ctx-coherence', coh);
    setText('mo-ctx-agreement', act);
    setText('mo-ctx-active', state.agents.filter(function (a) { return a.status === 'ok'; }).map(function (a) { return a.agent; }).join(' · ') || '—');
    setText('mo-ctx-sigdecision', dec);
    setText('mo-ctx-fundamental', agentLabel('fundamental'));
    setText('mo-ctx-technical', agentLabel('technical'));
    setText('mo-ctx-quant', agentLabel('quant'));

    var long = [], short = [];
    state.agents.forEach(function (a) {
      var sig = (a.signal || '').toUpperCase();
      var name = a.agent + (a.confidence != null && a.status === 'ok' ? ' ' + a.confidence : '');
      if (a.status !== 'ok') { name = a.agent + ' ' + (a.status === 'no_data' ? 'no data' : 'error'); long.push(name); short.push(name); return; }
      if (sig.indexOf('LONG') >= 0) { long.push(name + ' LONG'); short.push(a.agent + ' idle'); }
      else if (sig.indexOf('SHORT') >= 0) { short.push(name + ' SHORT'); long.push(a.agent + ' idle'); }
      else { long.push(name + ' NEUTRAL'); short.push(name + ' NEUTRAL'); }
    });
    setText('mo-buy-agents', long.length ? long.join(' · ') : 'no data');
    setText('mo-sell-agents', short.length ? short.join(' · ') : 'no data');

    var ok = state.agents.filter(function (a) { return a.status === 'ok'; });
    var list = ok.map(function (a) { return cap(a.agent) + ' ' + (a.signal || '—') + (a.confidence != null ? ' ' + a.confidence : ''); }).join(' · ');
    setText('mo-review-ai',
      'Enter an amount to get an advisory review of this trade. · Sentinel AI — Decision ' + dec + ' · Coherence ' + coh + ' · ' + act +
      (list ? ' · ' + list : '') +
      ' · Each engine explains its lean · Reasons, not arrows · Sentinel explains, never auto-executes · It explains. You decide.');

    renderCtx();
    renderExactOrder();
    renderStatus();
  }

  function renderStatus() {
    var s, color;
    if (!state.summary) { s = 'no agents'; color = 'var(--red)'; }
    else if (state.lastPrice == null || state.bestBid == null) { s = 'no orderbook/price'; color = '#FBBF24'; }
    else if (Date.now() - state.lastMarketTs > STALE_MS) { s = 'stale'; color = '#FBBF24'; }
    else { s = 'live'; color = 'var(--green)'; }
    var e = $id('mo-status');
    if (e) { e.textContent = 'MO: ' + s + ' · price ' + (state.lastPrice != null ? num(state.lastPrice, 2) : '—') + ' · bid/ask ' + (state.bestBid != null ? (num(state.bestBid, 2) + '/' + num(state.bestAsk, 2)) : '—/—'); e.style.color = color; }
  }

  function renderExactOrder() {
    var sideTxt = (state.side === 'sell') ? 'SELL BTC/USD — SHORT' : 'BUY BTC/USD — LONG';
    setText('eo-side', sideTxt + ' · ' + agentLabel('fundamental') + ' · ' + agentLabel('quant'));

    var ba = (state.bestBid != null && state.bestAsk != null) ? (num(state.bestBid, 2) + ' / ' + num(state.bestAsk, 2)) : '— / —';
    var typeTxt = (state.type === 'market') ? 'MARKET — Fills at market price' : 'LIMIT — Fills at your price or better';
    setText('eo-type', typeTxt + ' · Best bid/ask ' + ba);

    var lp = parseFloat($id('limitPrice').value);
    var lpTxt = (isFinite(lp) && lp > 0) ? (num(lp, 2) + ' USD') : '— USD';
    setText('eo-limit-line', lpTxt + ' · step 0.01 · Your price vs market ' + vsMarketLabel() +
      ' · Depth ' + depthLabel() + ' · vol ' + (state.depthBtc != null ? num(state.depthBtc, 2) + ' BTC' : '—'));
  }

  function recalc() {
    var amt = amount();
    var price = effectivePrice();
    var total = (amt > 0 && price) ? amt * price : 0;
    setVal('total', total ? total.toFixed(2) : '0.00');

    // risk metrics
    var rr = null; // no SL/TP fields on this page -> honest "—"
    var var95 = (total && state.ewma != null) ? total * 1.65 * state.ewma : null;
    var cvar = (var95 != null) ? var95 * 1.4 : null;
    setText('mo-risk-hint', 'Risk/Reward ' + (rr != null ? '1:' + rr.toFixed(2) : '—') + ' · Exposure ' + (total ? usd(total) : '—') + ' · 0.5% equity');
    setText('mo-risk-line', 'Risk/Reward ' + (rr != null ? '1:' + rr.toFixed(2) : '—') +
      ' · Exposure ' + (total ? usd(total) : '—') +
      ' · VaR 95% ' + (var95 != null ? usd(var95) : '—') +
      ' · CVaR ' + (cvar != null ? usd(cvar) : '—') +
      ' · EWMA ' + (state.ewma != null ? (state.ewma * 100).toFixed(2) + '%' : '—') +
      ' · Risk Engine ok');

    // info row — max buy is a capacity estimate at market price
    var maxBuyUsd = state.equity * state.riskPct; // $5,000
    var maxBuyBtc = (state.lastPrice && state.lastPrice > 0) ? maxBuyUsd / state.lastPrice : null;
    setText('mo-available', num(state.equity, 2) + ' USD — Paper · Simulated funds · no real money at risk');
    setText('mo-maxbuy', (maxBuyBtc != null ? btc(maxBuyBtc) : '— BTC') + ' · 0.5% equity · $' + num(maxBuyUsd, 0) + ' suggested · Risk Manager Pro');
    setText('mo-maxbuy-row', (maxBuyBtc != null ? btc(maxBuyBtc) : '— BTC'));
    setText('mo-minimum', '0.00001 BTC (Binance BTCUSDT minQty/stepSize) · Editable · Move/Drag');

    // exact order summary
    updateReview(total, amt, price);
  }

  function updateReview(total, amt, price) {
    var enabled = amt > 0 && price > 0;
    var btn = $id('reviewBtn');
    if (btn) btn.disabled = !enabled;
    setText('exactQty', enabled ? amt.toFixed(8) + ' BTC' : '— · Enter amount');
    setText('exactTotal', enabled ? total.toFixed(2) + ' USD' : '— · Risk/Reward —');
    setText('reviewHint', enabled ?
      ('Review ' + state.side.toUpperCase() + ' BTC Order — ' + amt.toFixed(8) + ' BTC @ ' + num(price, 2) + ' USD — Controlled action — paper only · quota ∧ cost ∧ policy → runs job') :
      'Enter a price and amount to continue · Controlled action vs Deliberate wait · You decide');
  }

  // ---------------- public overrides (called by inline onclick/oninput) ----------------
  window.setSide = function (side) {
    state.side = side;
    var buy = $id('bsBuy'), sell = $id('bsSell');
    if (buy) buy.classList.toggle('on', side === 'buy');
    if (sell) sell.classList.toggle('on', side === 'sell');
    recalc();
    renderMarket();
  };
  window.setType = function (type) {
    state.type = type;
    var l = $id('lmLimit'), m = $id('lmMarket');
    if (l) l.classList.toggle('on', type === 'limit');
    if (m) m.classList.toggle('on', type === 'market');
    var lp = $id('limitPrice');
    if (lp) lp.disabled = (type === 'market');
    renderMarket();
  };
  window.calcFromPrice = function () { recalc(); };
  window.calcFromAmount = function () { recalc(); };
  window.calcFromTotal = function () {
    var t = parseFloat($id('total').value) || 0;
    var p = effectivePrice();
    if (p > 0 && t > 0) setVal('amount', (t / p).toFixed(8));
    recalc();
  };
  window.setPercent = function (p) {
    var price = effectivePrice();
    var fellBack = false;
    if ((!price || price <= 0) && state.type === 'limit' && state.lastPrice) {
      // Limit with no typed price -> fall back to live lastPrice (variant A).
      price = state.lastPrice;
      setVal('limitPrice', price.toFixed(2));   // show what it computed from (plain number, no locale commas)
      fellBack = true;
    }
    if (!price || price <= 0) { log('setPercent: no price'); return; }
    var maxBuyUsd = state.equity * state.riskPct;
    var totalUsd = maxBuyUsd * p / 100;
    setVal('amount', (totalUsd / price).toFixed(8));
    setVal('total', totalUsd.toFixed(2));
    if (fellBack) log('setPercent: fallback to lastPrice ' + num(price, 2));
    recalc();
  };
  window.reviewOrder = function () {
    var amt = amount();
    var price = effectivePrice();
    if (!(amt > 0 && price > 0)) return;
    var rec = { side: state.side, type: state.type, amount: amt, price: price, total: amt * price, ts: new Date().toISOString() };
    try {
      var arr = JSON.parse(localStorage.getItem('sentinel_ai_manual_order_review') || '[]');
      if (!Array.isArray(arr)) arr = [];
      arr.push(rec);
      localStorage.setItem('sentinel_ai_manual_order_review', JSON.stringify(arr));
    } catch (e) {}
    log('Review order (paper, no execution):', rec);
    if (window.toast) window.toast('Paper review recorded · ' + state.side.toUpperCase() + ' ' + num(amt, 8) + ' BTC @ ' + num(price, 2) + ' USD · no exchange order · Your decision remains yours');
  };

  // ---------------- boot ----------------
  if (!$id('limitPrice') || !$id('amount')) { log('fields missing — not initialized'); return; }

  setText('mo-static-note', 'L1–L4 badges are static architecture labels (no live ledger feed in this landing).');

  fetchTicker();
  fetchDepth();
  fetchKlines();
  fetchAgents();
  renderStatus();

  // Static placeholders — honest Console markers.
  log('L1..L4 badges: static labels (no live ledger endpoint in this landing).');
  log('exact order gate: static labels (balance/sha256/job strings are architecture placeholders, no live ledger endpoint).');

  var askBtn = $id('eo-ask');
  if (askBtn) askBtn.addEventListener('click', function () {
    if (window.SentinelChat && window.SentinelChat.open) { window.SentinelChat.open(); }
    else { log('Sentinel chat not loaded'); if (window.toast) window.toast('Sentinel chat not loaded'); }
  });

  setInterval(fetchTicker, MARKET_POLL_MS);
  setInterval(fetchDepth, MARKET_POLL_MS);
  setInterval(fetchKlines, KLINES_INTERVAL_MS);
  setInterval(fetchAgents, AGENTS_POLL_MS);
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden) { fetchTicker(); fetchDepth(); fetchAgents(); }
  });
})();
