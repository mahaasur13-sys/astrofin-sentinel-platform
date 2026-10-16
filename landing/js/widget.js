/* ===== Decision AI Chat Widget — Enterprise v2.0 =====
   ROMA Execution Bridge (DeepSeek V4 Pro) streaming chat.
   Серверный DEEPSEEK_API_KEY в Secrets.
   X-API-Key из localStorage (ключ: roma_api_key).
   Авто-ретрай до 3 попыток. */
(() => {
  const $ = id => document.getElementById(id);
  const toggleBtn = $('chat-toggle');
  const panel = $('chat-panel');
  const closeBtn = $('chat-close');
  const clearBtn = $('chat-clear');
  const messagesEl = $('chat-messages');
  const input = $('chat-input');
  const sendBtn = $('chat-send');
  const stopBtn = $('chat-stop');
  const apiBadge = $('chat-api-badge');
  const apiKeyBtn = $('chat-api-key-btn');
  const keyIndicator = $('key-status-indicator');
  const apiOverlay = $('api-key-overlay');
  const apiInput = $('api-key-input');
  const apiEye = $('api-key-eye');
  const apiSave = $('api-key-save');
  const apiDelete = $('api-key-delete');
  const toast = $('toast');

  const ROMA_URL = '/api/chat/stream';
  const HIST = 'decisionos_chat_history_v3';
  const NAME_KEY = 'decisionos_chat_name';
  const API_KEY = 'roma_api_key';
  const MAX_RETRIES = 3;

  let history = loadHistory();
  let generating = false;
  let abortCtrl = null;
  let botEl = null;
  let lastFailedMsg = null;
  let toastTimer = null;

  function loadHistory() {
    try {
      const s = JSON.parse(localStorage.getItem(HIST) || '[]');
      return Array.isArray(s) ? s.filter(i => i && (i.role === 'user' || i.role === 'assistant') && typeof i.content === 'string').slice(-100) : [];
    } catch { return []; }
  }
  function saveHistory() { localStorage.setItem(HIST, JSON.stringify(history.slice(-100))); }
  function getName() { return localStorage.getItem(NAME_KEY) || ''; }
  function setName(n) { localStorage.setItem(NAME_KEY, n); }
  function getApiKey() { return localStorage.getItem(API_KEY) || ''; }
  function scrollDown() { messagesEl.scrollTop = messagesEl.scrollHeight; }
  function autoResize() { input.style.height = 'auto'; input.style.height = Math.min(input.scrollHeight, 130) + 'px'; }
  function setGen(v) { generating = v; sendBtn.disabled = v || !input.value.trim(); stopBtn.classList.toggle('hidden', !v); }

  function updateApiBadge(online) {
    apiBadge.classList.toggle('active', online);
    apiBadge.classList.toggle('error', !online);
    const dot = apiBadge.querySelector('.dot');
    if (dot) dot.style.background = online ? '#3fb950' : '#f85149';
  }

  function updateKeyIndicator() {
    const has = !!getApiKey();
    keyIndicator.classList.toggle('active', has);
    apiKeyBtn.setAttribute('aria-label', has ? 'API Key установлен' : 'API Key не установлен');
    apiKeyBtn.title = has ? 'API Key установлен' : 'Добавить API Key';
  }

  function showToast(text, isErr) {
    if (toastTimer) clearTimeout(toastTimer);
    toast.textContent = text;
    toast.className = 'toast' + (isErr ? ' error' : '') + ' show';
    toastTimer = setTimeout(() => { toast.className = 'toast'; }, 3000);
  }

  function appendMsg(text, role, save) {
    const el = document.createElement('div');
    el.className = 'chat-message ' + (role === 'user' ? 'user' : 'bot');
    el.textContent = text;
    messagesEl.appendChild(el);
    if (save !== false) { history.push({ role: role === 'user' ? 'user' : 'assistant', content: text }); saveHistory(); }
    scrollDown();
    return el;
  }

  function renderHistory() {
    messagesEl.replaceChildren();
    if (history.length === 0) {
      const n = getName();
      appendMsg(n ? 'Привет, ' + n + '! Я Decision AI. Спрашивай о платформе.' : 'Привет! Я Decision AI — ассистент DecisionOS.', 'assistant', false);
    } else {
      history.forEach(i => appendMsg(i.content, i.role === 'user' ? 'user' : 'assistant', false));
    }
  }

  function askName() {
    if (getName()) return;
    const e = window.prompt('Как к вам обращаться?');
    if (e && e.trim()) setName(e.trim().slice(0, 80));
  }

  /* ── Retry logic ── */
  async function fetchRetry(url, opts, retries) {
    let lastErr;
    for (let i = 0; i <= retries; i++) {
      try {
        const signal = abortCtrl ? abortCtrl.signal : undefined;
        return await fetch(url, { ...opts, signal });
      } catch (e) {
        if (e.name === 'AbortError') throw e;
        lastErr = e;
        if (i < retries) {
          const d = Math.min(1000 * Math.pow(2, i), 8000);
          if (botEl) botEl.textContent = '🔄 Повтор ' + (i + 2) + '/' + (retries + 1) + ' через ' + (d / 1000) + 'с…';
          await new Promise(r => setTimeout(r, d));
        }
      }
    }
    throw lastErr;
  }

  /* ── Send ── */
  async function sendMessage(msgOverride) {
    const msg = msgOverride || input.value.trim();
    if (!msg || generating) return;
    lastFailedMsg = null;
    appendMsg(msg, 'user');
    input.value = ''; autoResize();
    setGen(true);
    abortCtrl = new AbortController();
    botEl = document.createElement('div');
    botEl.className = 'chat-message bot typing';
    botEl.textContent = 'печатает';
    messagesEl.appendChild(botEl);
    scrollDown();

    try {
      const headers = { 'Content-Type': 'application/json', Accept: 'text/plain' };
      const key = getApiKey();
      if (key) headers['X-API-Key'] = key;

      const resp = await fetchRetry(ROMA_URL, {
        method: 'POST', headers,
        body: JSON.stringify({ message: msg, history: history.slice(-10), name: getName() || null }),
      }, MAX_RETRIES);

      updateApiBadge(true);
      if (!resp.ok) { let d = 'Ошибка ' + resp.status; try { d = (await resp.json()).detail || d; } catch {} throw new Error(d); }
      if (!resp.body) throw new Error('Нет потока данных');

      const reader = resp.body.getReader(), dec = new TextDecoder();
      let answer = '', first = true;
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = dec.decode(value, { stream: true });
        if (first) { botEl.classList.remove('typing'); botEl.textContent = ''; first = false; }
        answer += chunk; botEl.textContent = answer; scrollDown();
      }
      const final = answer.trim();
      if (final) { history.push({ role: 'assistant', content: final }); saveHistory(); }
    } catch (e) {
      updateApiBadge(false);
      if (e.name === 'AbortError') {
        const p = botEl ? botEl.textContent.trim() : '';
        if (botEl) { botEl.classList.remove('typing'); botEl.textContent = p ? p + ' [прервано]' : '[прервано]'; }
        if (p) { history.push({ role: 'assistant', content: p + ' [прервано]' }); saveHistory(); }
      } else {
        if (botEl) botEl.remove(); botEl = null;
        lastFailedMsg = msg;
        const errEl = appendMsg('⚠️ ' + (e.message || 'Сетевая ошибка'), 'assistant', false);
        errEl.classList.add('error-msg');
        const btn = document.createElement('button');
        btn.textContent = '🔄 Повторить';
        btn.className = 'chat-retry-btn';
        btn.onclick = () => { btn.remove(); sendMessage(msg); };
        errEl.appendChild(btn);
      }
    }
    botEl = null; abortCtrl = null;
    setGen(false); scrollDown();
  }

  /* ── Panel open/close ── */
  function openChat() { askName(); renderHistory(); panel.classList.remove('hidden'); toggleBtn.setAttribute('aria-expanded', 'true'); input.focus(); }
  function closeChat() { panel.classList.add('hidden'); toggleBtn.setAttribute('aria-expanded', 'false'); }
  toggleBtn.addEventListener('click', () => panel.classList.contains('hidden') ? openChat() : closeChat());
  closeBtn.addEventListener('click', closeChat);
  clearBtn.addEventListener('click', () => { if (generating && abortCtrl) abortCtrl.abort(); history = []; localStorage.removeItem(HIST); askName(); renderHistory(); });
  sendBtn.addEventListener('click', () => sendMessage());
  stopBtn.addEventListener('click', () => { if (abortCtrl) abortCtrl.abort(); });
  input.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });
  input.addEventListener('input', autoResize);

  /* ── API Key Modal ── */
  function openModal() {
    const cur = getApiKey();
    apiInput.value = cur ? '••••••••••••••••' : '';
    apiInput.type = 'password';
    apiInput.dataset.realValue = cur;
    apiEye.textContent = '👁';
    apiOverlay.classList.add('open');
    apiInput.focus();
    updateKeyIndicator();
  }
  function closeModal() { apiOverlay.classList.remove('open'); }

  apiKeyBtn.addEventListener('click', openModal);
  apiEye.addEventListener('click', () => {
    const isPass = apiInput.type === 'password';
    if (isPass && apiInput.dataset.realValue) { apiInput.type = 'text'; apiInput.value = apiInput.dataset.realValue; apiEye.textContent = '🙈'; }
    else { apiInput.type = 'password'; apiInput.value = apiInput.dataset.realValue ? '••••••••••••••••' : ''; apiEye.textContent = '👁'; }
  });

  apiSave.addEventListener('click', () => {
    const isMasked = apiInput.value === '••••••••••••••••';
    let val = isMasked ? (apiInput.dataset.realValue || '') : apiInput.value.trim();
    if (!val) { showToast('Введите API-ключ', true); return; }
    localStorage.setItem(API_KEY, val);
    showToast('✅ API Key сохранён');
    closeModal();
    updateKeyIndicator();
    updateApiBadge(true);
  });

  apiDelete.addEventListener('click', () => {
    localStorage.removeItem(API_KEY);
    apiInput.value = ''; apiInput.dataset.realValue = '';
    showToast('🗑 API Key удалён');
    updateKeyIndicator();
  });

  apiOverlay.querySelector('.modal-cancel').addEventListener('click', closeModal);
  apiOverlay.addEventListener('click', e => { if (e.target === apiOverlay) closeModal(); });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && apiOverlay.classList.contains('open')) closeModal();
  });

  updateApiBadge(true);
  updateKeyIndicator();
})();
