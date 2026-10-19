/* Sentinel AI — shared /agents poller (single source of truth).
   One poller, no overlapping requests: the next fetch never starts while the
   previous is in flight. Each snapshot is broadcast via
   CustomEvent('agents:snapshot') and also renders the header pill and the
   chart-insight directly. trading_chart.js and manual_order.js consume the
   event — they no longer poll /agents themselves.
*/
(function () {
  'use strict';

  var AGENTS_URL = 'http://127.0.0.1:8791/agents';
  var POLL_MS = 8000;
  var inFlight = false;
  var lastSnapshot = null;

  function fmtTs(ts) {
    if (!ts) return '—';
    var m = /T(\d{2}:\d{2}:\d{2})/.exec(ts);
    return m ? (m[1] + 'Z') : ts;
  }

  function agentLabel(a) {
    if (a.status === 'ok') {
      return a.agent + ' ' + (a.signal || '').toUpperCase() + ' ' + (a.confidence != null ? a.confidence : '—');
    }
    return a.agent + ' ' + (a.status === 'no_data' ? 'idle' : 'error');
  }

  function render(snap) {
    var s = snap.summary;
    var ts = fmtTs(snap.ts);

    var pill = document.getElementById('header-decision');
    if (pill) {
      pill.textContent = s
        ? 'Decision ' + s.decision + ' · Coherence ' + (s.coherence != null ? s.coherence : '—') + ' · ' + s.active + ' of ' + s.total + ' active · ' + ts
        : 'Decision — · agents offline';
    }

    var insight = document.getElementById('chart-insight');
    if (insight) {
      if (snap.agents && snap.agents.length) {
        var parts = snap.agents.map(agentLabel);
        parts.push('Decision ' + (s ? s.decision : '—') + ' · Coherence ' + (s && s.coherence != null ? s.coherence : '—') + ' · ' + (s ? (s.active + ' of ' + s.total + ' active') : 'agents offline') + ' · ' + ts);
        insight.textContent = parts.join(' · ');
      } else {
        insight.textContent = 'agents offline · ' + ts;
      }
    }
  }

  function emit(snap) {
    lastSnapshot = snap;
    render(snap);
    try {
      window.dispatchEvent(new CustomEvent('agents:snapshot', { detail: snap }));
    } catch (e) { /* noop */ }
  }

  function poll() {
    if (document.hidden) return;
    if (inFlight) return;            // no overlap — skip while previous is pending
    inFlight = true;
    fetch(AGENTS_URL)
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) {
        emit({
          ts: (d && d.ts) ? d.ts : null,
          summary: (d && d.summary) ? d.summary : null,
          agents: (d && d.agents) ? d.agents : []
        });
      })
      .catch(function () {
        emit({ ts: null, summary: null, agents: [] });
      })
      .then(function () { inFlight = false; });
  }

  window.AgentsShared = {
    getLastSnapshot: function () { return lastSnapshot; },
    poll: poll
  };

  poll();
  setInterval(poll, POLL_MS);
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden) poll();
  });
})();
