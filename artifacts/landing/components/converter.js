// Sentinel Crypto Converter — self-hosted, live BTC/USD data from Binance.
// Replaces the third-party crypto-converter-widget whose source (api.coincap.io)
// is unreachable from this machine (DNS: Could not resolve host), which is why
// the old widget rendered "—" (no data).
(function () {
  'use strict';

  var RATE_URL = 'https://data-api.binance.vision/api/v3/ticker/24hr?symbol=BTCUSDT';
  var POLL_MS = 15000;

  var el = {
    status: document.getElementById('cc-status'),
    price: document.getElementById('cc-price'),
    change: document.getElementById('cc-change'),
    volume: document.getElementById('cc-volume'),
    highlow: document.getElementById('cc-highlow'),
    amount: document.getElementById('cc-amount'),
    from: document.getElementById('cc-from'),
    result: document.getElementById('cc-result')
  };

  var last = null; // last Binance 24hr ticker object

  function fmtUSD(n, dp) {
    if (n == null || !isFinite(n)) return '—';
    return '$' + n.toLocaleString('en-US', { minimumFractionDigits: dp, maximumFractionDigits: dp });
  }

  function fmtNum(n) {
    if (n == null || !isFinite(n)) return '—';
    return n.toLocaleString('en-US', { maximumFractionDigits: 2 });
  }

  function renderConversion(price) {
    var raw = parseFloat(el.amount.value);
    var amount = isFinite(raw) && raw >= 0 ? raw : 0;
    if (price == null || !isFinite(price)) {
      el.result.textContent = '= —';
      return;
    }
    var out;
    if (el.from.value === 'BTC') {
      out = amount * price;
      el.result.textContent = '= ' + fmtUSD(out, 2);
    } else {
      out = amount / price;
      el.result.textContent = '= ' + out.toLocaleString('en-US', { maximumFractionDigits: 8 }) + ' BTC';
    }
  }

  function render() {
    if (!last) return;
    var price = parseFloat(last.lastPrice);
    var pct = parseFloat(last.priceChangePercent);
    var vol = parseFloat(last.volume);       // base-asset volume (BTC)
    var high = parseFloat(last.highPrice);
    var low = parseFloat(last.lowPrice);

    el.price.textContent = fmtUSD(price, 2);
    el.change.textContent = '24h change ' + (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%';
    el.change.style.color = pct >= 0 ? 'var(--green)' : 'var(--red)';
    el.volume.textContent = fmtNum(vol) + ' BTC';
    el.highlow.textContent = 'H ' + fmtUSD(high, 2) + ' / L ' + fmtUSD(low, 2);
    el.status.textContent = '· live (Binance)';
    el.status.style.color = 'var(--green)';

    renderConversion(price);
  }

  function tick() {
    fetch(RATE_URL)
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (d) {
        if (!d || d.lastPrice == null) throw new Error('empty payload');
        last = d;
        render();
      })
      .catch(function (err) {
        el.status.textContent = '· no data (' + (err && err.message ? err.message : 'unreachable') + ')';
        el.status.style.color = 'var(--red)';
      });
  }

  el.amount.addEventListener('input', function () {
    renderConversion(last ? parseFloat(last.lastPrice) : null);
  });
  el.from.addEventListener('change', function () {
    renderConversion(last ? parseFloat(last.lastPrice) : null);
  });

  tick();
  setInterval(tick, POLL_MS);
})();
