/* Sentinel AI — live order book (Binance depth) + honest metrics.
   Data: REST snapshot (data-api.binance.vision/api/v3/depth?limit=20) +
         WebSocket wss://stream.binance.com:9443/ws/btcusdt@depth20@100ms.
   Self-contained, no deps. Honesty: if no data -> "—" (never invent).
*/
(function () {
  'use strict';
  var SYMBOL = 'BTCUSDT';
  var REST_URL = 'https://data-api.binance.vision/api/v3/depth?symbol=' + SYMBOL + '&limit=20';
  var WS_URL = 'wss://stream.binance.com:9443/ws/btcusdt@depth20@100ms';
  var AGENTS_URL = 'http://127.0.0.1:8791/agents';

  var obWs = null;
  var reconnectDelay = 1000;
  var lastUpdate = 0;
  var staleTimer = null;
  var rafPending = false;

  var book = { asks: [], bids: [] };   // [{price, qty}], asks asc, bids desc

  function el(id) { return document.getElementById(id); }
  function set(id, txt) { var e = el(id); if (e) e.textContent = txt; }

  function fmtP(p) { return p ? '$' + Number(p).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—'; }
  function fmtQ(q) { return q ? Number(q).toFixed(4) + ' BTC' : '— BTC'; }

  function setConn(status, color) {
    set('ob-conn', status);
    var e = el('ob-conn'); if (e && color) e.style.color = color;
  }

  function sum(list) { var s = 0; for (var i = 0; i < list.length; i++) s += list[i].qty; return s; }

  function render() {
    rafPending = false;
    if (!book.asks.length || !book.bids.length) return;

    var ask0 = book.asks[0], ask1 = book.asks[1];
    var bid0 = book.bids[0], bid1 = book.bids[1];

    // top-2 ASK (nearest first) + BID (nearest first)
    if (ask0) { set('ob-ask-1-p', 'ASK ' + fmtP(ask0.price)); set('ob-ask-1-q', fmtQ(ask0.qty)); }
    if (ask1) { set('ob-ask-2-p', 'ASK ' + fmtP(ask1.price)); set('ob-ask-2-q', fmtQ(ask1.qty)); }
    if (bid0) { set('ob-bid-1-p', 'BID ' + fmtP(bid0.price)); set('ob-bid-1-q', fmtQ(bid0.qty)); }
    if (bid1) { set('ob-bid-2-p', 'BID ' + fmtP(bid1.price)); set('ob-bid-2-q', fmtQ(bid1.qty)); }

    // volume + spread
    var totalBid = sum(book.bids), totalAsk = sum(book.asks);
    var depth = totalBid + totalAsk;
    set('ob-vol', depth ? depth.toFixed(2) : '—');
    if (ask0 && bid0) {
      var spread = ask0.price - bid0.price;
      set('ob-spread', spread ? spread.toFixed(2) + ' USDT' : '—');
    }

    // depth status
    set('ob-st-depth', depth ? depth.toFixed(2) + ' BTC depth' : '— depth');

    // thinned (bid/ask ratio)
    var ratio = totalAsk > 0 ? totalBid / totalAsk : 0;
    if (totalBid && totalAsk) {
      if (ratio < 0.5) set('ob-st-thinned', 'bid-heavy (thinned ask)');
      else if (ratio > 2.0) set('ob-st-thinned', 'ask-heavy (thinned bid)');
      else set('ob-st-thinned', 'balanced');
    } else {
      set('ob-st-thinned', '— thinned');
    }

    // accumulation (avg level size)
    if (book.asks.length && book.bids.length) {
      var avgBid = totalBid / book.bids.length, avgAsk = totalAsk / book.asks.length;
      set('ob-st-accum', (avgBid > avgAsk * 1.3) ? 'BTC accumulation' : 'BTC no accumulation');
    } else {
      set('ob-st-accum', '— accumulation');
    }
  }

  function applyData(data) {
    if (!data || !Array.isArray(data.asks) || !Array.isArray(data.bids)) return;
    book.asks = data.asks.map(function (r) { return { price: +r[0], qty: +r[1] }; }).sort(function (a, b) { return a.price - b.price; });
    book.bids = data.bids.map(function (r) { return { price: +r[0], qty: +r[1] }; }).sort(function (a, b) { return b.price - a.price; });
    lastUpdate = Date.now();
    setConn('live', '#22c55e');
    if (!rafPending) { rafPending = true; requestAnimationFrame(render); }
  }

  function pollFundamental() {
    fetch(AGENTS_URL)
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) {
        var f = null;
        if (d && d.agents) {
          for (var i = 0; i < d.agents.length; i++) { if (d.agents[i].agent === 'fundamental') { f = d.agents[i]; break; } }
        }
        if (!f) { set('ob-st-fund', 'Fundamental idle'); return; }
        if (f.status === 'ok') {
          set('ob-st-fund', 'Fundamental ' + (f.signal || '—') + (typeof f.confidence === 'number' ? ' ' + f.confidence : ''));
        } else if (f.status === 'no_data') {
          set('ob-st-fund', 'Fundamental idle');
        } else {
          set('ob-st-fund', 'Fundamental unavailable');
        }
      })
      .catch(function () { set('ob-st-fund', 'Fundamental idle'); });
  }

  function fetchSnapshot() {
    fetch(REST_URL)
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) { applyData(d); })
      .catch(function () { setConn('stale', '#FBBF24'); });
  }

  function connect() {
    if (obWs) { try { obWs.close(); } catch (e) {} obWs = null; }
    setConn('connecting', '#FBBF24');
    try {
      obWs = new WebSocket(WS_URL);
      obWs.onopen = function () { reconnectDelay = 1000; fetchSnapshot(); };
      obWs.onmessage = function (ev) {
        try { applyData(JSON.parse(ev.data)); } catch (e) {}
      };
      obWs.onclose = function () { obWs = null; setConn('reconnecting', '#FBBF24'); scheduleReconnect(); };
      obWs.onerror = function () { try { obWs.close(); } catch (e) {} };
    } catch (e) { scheduleReconnect(); }
  }

  function scheduleReconnect() {
    setTimeout(function () { connect(); }, reconnectDelay);
    reconnectDelay = Math.min(reconnectDelay * 2, 30000);
  }

  function startStaleWatch() {
    clearInterval(staleTimer);
    staleTimer = setInterval(function () {
      if (obWs && lastUpdate && Date.now() - lastUpdate > 10000) {
        setConn('stale', '#FBBF24');
      }
    }, 2000);
  }

  // boot
  if (el('orderbook')) {
    connect();
    pollFundamental();
    setInterval(pollFundamental, 8000);
    startStaleWatch();
    document.addEventListener('visibilitychange', function () {
      if (!document.hidden) { fetchSnapshot(); if (!obWs) connect(); }
    });
    window.addEventListener('beforeunload', function () { if (obWs) { try { obWs.close(); } catch (e) {} } });
  }
})();
