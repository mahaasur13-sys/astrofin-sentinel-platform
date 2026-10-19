/* Sentinel AI Chat — as in decisionos-landing — only for astrofin-sentinel-platform — Explain-Only — Arilus → Sentinel */
(function () {
  var cssId = 'sentinel-chat-css';
  if (!document.getElementById(cssId)) {
    var link = document.createElement('link');
    link.id = cssId;
    link.rel = 'stylesheet';
    link.href = 'components/ai_chat.css';
    document.head.appendChild(link);
  }

  // FAB
  var fab = document.createElement('button');
  fab.className = 'chat-fab';
  fab.id = 'chatFab';
  fab.title = 'Sentinel AI Assistant — Explain-Only';
  fab.innerHTML = '◆<span class="badge-dot"></span>';
  document.body.appendChild(fab);

  // Window
  var win = document.createElement('div');
  win.className = 'chat-window';
  win.id = 'chatWindow';
  win.innerHTML =
    '<div class="chat-header">' +
      '<div class="chat-header-left">' +
        '<span class="status-dot active"></span>' +
        '<span class="chat-title">Sentinel — your assistant</span>' +
        '<span class="chat-subtitle">BTC · EXPLAIN-ONLY · live ROMA + Platform data</span>' +
      '</div>' +
      '<div class="chat-header-actions">' +
        '<button class="chat-header-btn" title="API Key — hash-only 0/3400" id="chatKeyBtn">🔑</button>' +
        '<button class="chat-header-btn" id="chatCloseBtn">✕</button>' +
      '</div>' +
    '</div>' +
    '<div class="chat-body" id="chatBody">' +
      '<div class="msg msg-ai">' +
        '<div style="font-family:Orbitron,sans-serif;font-size:0.78rem;color:#00E5FF;margin-bottom:5px">Sentinel — your assistant — Explain-Only</div>' +
        'Ask me about anything on the platform: balance, usage, limits, jobs, workers, trading signal/regime, or how Sentinel works. I explain clearly.<br><br><strong>Connected to live ROMA + Platform data</strong> — balance, jobs, and trading signal are live; the 6-engine Decision/Coherence % isn\'t exposed live yet.<br><br>' +
        'I\'m explain-only: I help you understand and learn, but I don\'t give personalized financial advice, and I can\'t change settings or place trades.<br><br>' +
        'If a value isn\'t available, I\'ll say so plainly.<br><br>' +
        '<strong>Chart context: BTC</strong> (I\'m not limited to it — ask about anything).<br><br>' +
        '<em>Sentinel DecisionOS — 25 agents → 6 disciplines → synthesis agent → one signal weights 20/20/15/15/10/10 Σ100 — Each engine explains its lean — Reasons, not arrows. Live trading signal/regime comes from ROMA; the weighted Decision/Coherence % isn\'t exposed live yet. Transparent — Built to be checked, not trusted blindly — You see why — and you stay in control.</em><br><br>' +
        'Tap a quick action below, or just type your question.' +
        '<div class="msg-time">10:27:12 — Sentinel AI · Decision Intelligence — hash-only 0/3400 e91b51c4 2ca0815 — L1 append_only</div>' +
      '</div>' +
      '<div class="msg msg-user">' +
        'I\'m placing a manual limit buy order for BTC. What\'s the current market outlook, and are these price levels sensible?' +
        '<div class="msg-time">10:51:03 — Manual Order — BTC/USD — Limit 77,554.57 USD — Amount 0 BTC — Paper Trading</div>' +
      '</div>' +
      '<div class="msg msg-ai">' +
        '<div style="font-weight:600;margin-bottom:6px">Live data — connected via ROMA</div>' +
        '<div class="current-state">' +
          '<div style="text-transform:uppercase;letter-spacing:0.08em;font-size:0.6rem;color:#6B7280;margin-bottom:4px">Live ROMA + Platform — read-only</div>' +
          '<div>• Balance, usage, limits, jobs, workers — live from ROMA.</div>' +
          '<div>• Trading signal / regime — live from the Platform API.</div>' +
          '<div>• The 6-engine Decision/Coherence % isn\'t exposed live yet (agents report idle) — I won\'t invent it.</div>' +
        '</div>' +
        '<div class="msg-time">— Sentinel AI · Decision Intelligence — hash-only 0/3400 e91b51c4 2ca0815 — L1 append_only</div>' +
      '</div>' +
    '</div>' +
    '<div style="padding:8px 12px">' +
      '<div class="quick-actions">' +
        '<button class="qa-btn" data-action="portfolio">Explain My Portfolio</button>' +
        '<button class="qa-btn" data-action="settings">Explain My Settings</button>' +
        '<button class="qa-btn" data-action="strategy">Review My Strategy</button>' +
        '<button class="qa-btn" data-action="trade">Explain This Trade</button>' +
        '<button class="qa-btn" data-action="order">Explain An Order</button>' +
        '<button class="qa-btn" data-action="learn">Learn Sentinel AI</button>' +
        '<button class="qa-btn" data-action="help" style="grid-column:1 / -1">Platform Help</button>' +
      '</div>' +
    '</div>' +
    '<div class="chat-input-area">' +
      '<textarea class="chat-input" id="chatInput" placeholder="Ask Sentinel anything, or paste an order ID… — Explain-only"></textarea>' +
      '<button class="send-btn" id="sendBtn">➤</button>' +
    '</div>' +
    '<div class="explain-only">Explain-only — read-only live data — cannot place trades or change settings — Sentinel AI · Decision Intelligence — Your acceptance is recorded append-only (L1) — hash-only 0/3400 e91b51c4 2ca0815 — L1-L4 — Your decision remains yours — It explains. You decide.</div>';

  document.body.appendChild(win);

  var chatBody = win.querySelector('#chatBody');
  var chatInput = win.querySelector('#chatInput');
  var sendBtn = win.querySelector('#sendBtn');
  var closeBtn = win.querySelector('#chatCloseBtn');
  var keyBtn = win.querySelector('#chatKeyBtn');

  function openChat() { win.classList.add('open'); }
  function closeChat() { win.classList.remove('open'); }
  fab.addEventListener('click', openChat);
  closeBtn.addEventListener('click', closeChat);
  keyBtn.addEventListener('click', function () {
    toast('API Key — hash-only 0/3400 · mask first4***last4 · e91b51c4 2ca0815 · Sentinel AI · Decision Intelligence');
  });

  function toast(msg) {
    var t = document.createElement('div');
    t.textContent = msg;
    t.style.cssText = 'position:fixed;bottom:100px;right:28px;background:#0B1220;border:1px solid rgba(0,229,255,0.4);color:#E6EDF3;padding:11px 18px;border-radius:8px;font-size:12.5px;z-index:3000;font-family:system-ui;max-width:320px;';
    document.body.appendChild(t);
    setTimeout(function () { t.remove(); }, 2800);
  }

  function addMessage(text, isUser) {
    var msg = document.createElement('div');
    msg.className = 'msg ' + (isUser ? 'msg-user' : 'msg-ai');
    var time = new Date().toLocaleTimeString('en-GB', { hour12: false });
    msg.innerHTML = text + '<div class="msg-time">' + time + (isUser ? ' — Manual Order' : ' — Sentinel AI · Decision Intelligence — Explain-Only — L1 append_only') + '</div>';
    chatBody.appendChild(msg);
    chatBody.scrollTop = chatBody.scrollHeight;
    return msg;
  }

  // ---- DeepSeek integration (local proxy, key stays server-side) ----
  var PROXY_URL = 'http://127.0.0.1:8788/chat';
  var HISTORY = [];

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }
  function fmt(s) {
    var e = escapeHtml(s);
    e = e.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    e = e.replace(/\n/g, '<br>');
    return e;
  }
  function askDeepSeek(question) {
    var messages = HISTORY.concat([{ role: 'user', content: question }]);
    return fetch(PROXY_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: messages })
    }).then(function (r) {
      if (!r.ok) throw new Error('proxy ' + r.status);
      return r.json();
    }).then(function (data) {
      if (!data || typeof data.content !== 'string' || !data.content.trim()) {
        throw new Error('empty reply');
      }
      HISTORY.push({ role: 'user', content: question });
      HISTORY.push({ role: 'assistant', content: data.content });
      if (HISTORY.length > 12) HISTORY = HISTORY.slice(-12);
      return data.content;
    });
  }

  function getResponse(q) {
    var lower = q.toLowerCase();
    if (lower.indexOf('portfolio') >= 0) return '<strong>Explain My Portfolio — Paper — Explain-Only</strong><br>Portfolio Value $1 000 000 100% cash (Sentinel Paper · simulated) · Total P&amp;L +$0 · Win Rate 0.0% · Positions 0 · Trading conditions, engine leans and gate verdict are not connected to live data yet — static demo — live state not connected · hash-only 0/3400 · Explain-only cannot place trades.';
    if (lower.indexOf('settings') >= 0) return '<strong>Explain My Settings — Explain-Only</strong><br>Risk level and preferred exchange — AI sizes every paper trade from these · Sentinel Paper · Free account · No card required · Risk Manager Pro · Mandatory SL · TP1/TP2 · Position size 0.5% equity · Leverage auto · Explain-only cannot change settings · Your decision remains yours · L1 append_only.';
    if (lower.indexOf('strategy') >= 0) return '<strong>Review My Strategy — 6 engines — Explain-Only</strong><br>25 agents → 6 disciplines → synthesis → weights 20/20/15/15/10/10 Σ100 · Each engine explains its lean · Reasons, not arrows · Six explainable engines + transparent weights · You stay in control · Explains never auto-executes · It explains. You decide. · Decision / Coherence are not connected to live data yet — static demo — live state not connected · Explain-only cannot give financial advice.';
    if (lower.indexOf('order') >= 0) return '<strong>Explain An Order — job:{id} sha256[:24] — Explain-Only</strong><br>Order ID format job:{id} sha256[:24] · e3698b64-5370-49f7-a520-d117eb144319 · L3 idempotency PK 006 · L1 append_only INSERT-only + trigger 009 · L2 atomic_debit Advisory-lock + SUM(CREDIT−DEBIT) + bal ≥ amount · No debit at submit · debit only at finalize · L4 fail_closed 402/403/429/503 · Gate quota · cost · policy · Your decision remains yours.';
    if (lower.indexOf('learn') >= 0) return '<strong>Learn Sentinel AI — Decision Intelligence Platform — Explain-Only</strong><br>Reasons, not arrows. · Six engines. One read. Your call. · Quota. Cost. Policy. Then execution. · Trust by construction · It explains. You decide. · 25 agents Fundamental 20 Quant 20 Macro 15 Options Flow 15 Sentiment 10 Technical 10 Σ100 · L1-L4 · Sentinel Paper Simulated funds · hash-only 0/3400 e91b51c4 2ca0815 · 73 paths / 76 operations · 86 branches · 19 workflows · Your acceptance is recorded append-only (L1).';
    if (lower.indexOf('help') >= 0) return '<strong>Platform Help — Where to get API key? — 3 steps — Explain-Only</strong><br>1. Choose source: Dashboard (instant) · Email (1–5 min) · Telegram /get_key (instant) · Support (15–60 min)<br>2. Get the key: masked first4***last4 · len 64 · X-API-Key<br>3. Activate: curl POST /submit → 202 queued e3698b64 · No debit at submit · Your decision remains yours.';
    return '<strong>Current State — not connected — Explain-Only</strong><br>Live platform state is not connected yet, so there is no live Decision / Coherence / gate verdict to show.<br>How it will look when live: Decision 0–100 with direction and engine weights; Coherence 0–1 against a threshold; gate verdict ALLOWED / DENIED / DEFER with reason (Coherence rule · Entropy rule · PXQ Edge rule · quota ∧ cost ∧ policy) and audit IDs (decision_id, request_id, idempotency_key, hash).<br>Static demo — live state not connected · Explain-only — I cannot give personalized financial advice, and I cannot change settings or place trades.';
  }

  function handleQuestion(text) {
    if (!text.trim()) return;
    addMessage(text, true);
    chatInput.value = '';
    var thinking = addMessage('<em style="color:#6B7280">Sentinel is thinking…</em>', false);
    askDeepSeek(text).then(function (content) {
      thinking.remove();
      addMessage(fmt(content), false);
    }).catch(function () {
      thinking.remove();
      addMessage(
        '<div style="margin-bottom:4px;font-weight:600;color:#FBBF24">offline fallback — live data unavailable</div>' +
        getResponse(text) +
        '<div class="msg-time" style="color:#6B7280">(offline fallback — chat shim not running · start with `python3 chat_shim.py` in artifacts/landing)</div>',
        false
      );
    });
  }

  sendBtn.addEventListener('click', function () { handleQuestion(chatInput.value); });
  chatInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleQuestion(chatInput.value); }
  });

  win.querySelectorAll('.qa-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var map = {
        portfolio: 'Explain My Portfolio',
        settings: 'Explain My Settings',
        strategy: 'Review My Strategy',
        trade: 'Explain This Trade — I\'m placing a manual limit buy order for BTC. What\'s the current market outlook?',
        order: 'Explain An Order — paste an order ID',
        learn: 'Learn Sentinel AI',
        help: 'Platform Help'
      };
      handleQuestion(map[btn.getAttribute('data-action')]);
    });
  });

  window.SentinelChat = { open: openChat, close: closeChat, ask: handleQuestion };

  console.log('Sentinel AI Chat — as in decisionos-landing — only for astrofin-sentinel-platform — Explain-Only — mounted');
})();
