/* ===== Decision AI Chat Widget — Shared JS ===== */
(() => {
  const $ = (id) => document.getElementById(id);
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
  const apiKeyOverlay = $('api-key-overlay');
  const apiKeyInput = $('api-key-input');
  const apiKeyEye = $('api-key-eye');
  const apiKeySave = $('api-key-save');
  const apiKeyDelete = $('api-key-delete');

  const HISTORY_KEY = 'decisionos_chat_history_v1';
  const NAME_KEY = 'decisionos_chat_user_name';
  const API_KEY_KEY = 'decisionos_api_key';

  let history = loadHistory();
  let isGenerating = false;
  let abortController = null;
  let currentBotEl = null;

  function loadHistory() {
    try {
      const stored = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
      if (!Array.isArray(stored)) return [];
      return stored.filter(item => item && (item.role === 'user' || item.role === 'assistant') && typeof item.content === 'string').slice(-100);
    } catch { return []; }
  }
  function saveHistory() { localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(-100))); }
  function getName() { return localStorage.getItem(NAME_KEY) || ''; }
  function setName(n) { localStorage.setItem(NAME_KEY, n); }
  function getApiKey() { return localStorage.getItem(API_KEY_KEY) || ''; }

  function updateApiBadge() {
    const has = !!getApiKey();
    apiBadge.className = 'chat-api-badge' + (has ? ' active' : '');
    apiBadge.innerHTML = '<span class="dot"></span> ' + (has ? 'api' : 'demo');
  }

  function scrollToBottom() { messagesEl.scrollTop = messagesEl.scrollHeight; }

  function appendMessage(text, role, save) {
    const el = document.createElement('div');
    el.className = 'chat-message ' + (role === 'user' ? 'user' : 'bot');
    el.textContent = text;
    messagesEl.appendChild(el);
    if (save !== false) {
      history.push({ role: role === 'user' ? 'user' : 'assistant', content: text });
      saveHistory();
    }
    scrollToBottom();
    return el;
  }

  function renderHistory() {
    messagesEl.replaceChildren();
    if (history.length === 0) {
      const name = getName();
      appendMessage(name ? `Привет, ${name}! Я AI-ассистент DecisionOS. Чем помочь?` : 'Привет! Я AI-ассистент DecisionOS. Как к вам обращаться?', 'assistant', false);
    } else {
      history.forEach(item => appendMessage(item.content, item.role === 'user' ? 'user' : 'assistant', false));
    }
  }

  function askName() {
    if (getName()) return;
    const entered = window.prompt('Как к вам обращаться?');
    if (entered && entered.trim()) setName(entered.trim().slice(0, 80));
  }

  function autoResize() {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 130) + 'px';
  }

  function setGenerating(v) {
    isGenerating = v;
    sendBtn.disabled = v || !input.value.trim();
    stopBtn.classList.toggle('hidden', !v);
  }

  function getDemoResponse(msg) {
    const lower = msg.toLowerCase();
    if (lower.includes('policy') || lower.includes('полиси')) return 'DecisionOS Policy Engine — это 15+ actions для контроля доступа: crypto:invoice:create, crypto:invoice:read, crypto:webhook:receive, crypto:payment:activate_tier, wallet:create, wallet:rotate, support:ticket:create, support:ticket:assign и другие. Каждый action проверяется через Decision Gate: Quota ∧ Cost ∧ Policy.';
    if (lower.includes('gate') || lower.includes('decision gate')) return 'Decision Gate — тройной guard: Quota OK ∧ Cost OK ∧ Policy OK. Все три условия должны быть выполнены для ExecutionAllowed = true. Это основа архитектуры безопасности DecisionOS.';
    if (lower.includes('crypto') || lower.includes('крипто')) return 'Crypto Payments поддерживает Monero (XMR) через NOWPayments с view-only wallets. Суб-адреса создаются под каждый инвойс. Никогда не храним spend keys. Тиры: Start (5 инвойсов/мес), Pro (20), Enterprise (100).';
    if (lower.includes('test') || lower.includes('тест')) return 'Все 32 теста зелёные: 10/10 crypto_payments, 10/10 wallets, 12/12 support_chat. Coverage: 100%.';
    if (lower.includes('api') || lower.includes('эндпоинт')) return 'DecisionOS v1.0.0: 10 REST + 1 WebSocket. Crypto: POST /v1/crypto/invoices, GET .../{id}, POST .../webhooks/{provider}. Wallets: POST /v1/crypto/wallets, .../addresses, .../monero/subaddress, .../rotate. Support: CRUD /v1/support/tickets + WS /ws/support/{ticket_id}.';
    return 'Я AI-ассистент DecisionOS. Могу рассказать о Policy Engine, Decision Gate, Crypto Payments, архитектуре, тестах и эндпоинтах. Есть demo-режим и поддержка API-ключей (🔑).';
  }

  async function sendMessage() {
    const msg = input.value.trim();
    if (!msg || isGenerating) return;
    appendMessage(msg, 'user');
    input.value = ''; autoResize();
    setGenerating(true);
    abortController = new AbortController();
    currentBotEl = document.createElement('div');
    currentBotEl.className = 'chat-message bot typing';
    currentBotEl.textContent = 'печатает...';
    messagesEl.appendChild(currentBotEl);
    scrollToBottom();

    const apiKey = getApiKey();
    if (apiKey) {
      try {
        const resp = await fetch('https://api.openai.com/v1/chat/completions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + apiKey },
          body: JSON.stringify({ model: 'gpt-4o-mini', messages: [{ role: 'system', content: 'You are Decision AI, assistant for DecisionOS platform.' }, ...history.map(h => ({ role: h.role, content: h.content }))], stream: true }),
          signal: abortController.signal
        });
        if (!resp.ok) throw new Error('API error ' + resp.status);
        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let answer = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n').filter(l => l.startsWith('data: '));
          for (const line of lines) {
            const data = line.slice(6);
            if (data === '[DONE]') continue;
            try { answer += JSON.parse(data).choices[0]?.delta?.content || ''; } catch {}
          }
          currentBotEl.classList.remove('typing');
          currentBotEl.textContent = answer;
          scrollToBottom();
        }
        if (answer.trim()) { history.push({ role: 'assistant', content: answer.trim() }); saveHistory(); }
      } catch (err) {
        if (err.name === 'AbortError') {
          currentBotEl.classList.remove('typing');
          currentBotEl.textContent = (currentBotEl.textContent + ' [прервано]').trim();
        } else {
          currentBotEl.remove();
          appendMessage('Ошибка: ' + err.message, 'assistant');
        }
      }
    } else {
      await new Promise(r => setTimeout(r, 600 + Math.random() * 800));
      currentBotEl.classList.remove('typing');
      const answer = getDemoResponse(msg);
      currentBotEl.textContent = answer;
      history.push({ role: 'assistant', content: answer });
      saveHistory();
    }
    currentBotEl = null;
    abortController = null;
    setGenerating(false);
    scrollToBottom();
  }

  function openChat() { askName(); renderHistory(); panel.classList.remove('hidden'); toggleBtn.setAttribute('aria-expanded', 'true'); input.focus(); }
  function closeChat() { panel.classList.add('hidden'); toggleBtn.setAttribute('aria-expanded', 'false'); }

  toggleBtn.addEventListener('click', () => panel.classList.contains('hidden') ? openChat() : closeChat());
  closeBtn.addEventListener('click', closeChat);
  clearBtn.addEventListener('click', () => {
    if (isGenerating) abortController?.abort();
    history = []; localStorage.removeItem(HISTORY_KEY); askName(); renderHistory();
  });
  sendBtn.addEventListener('click', sendMessage);
  stopBtn.addEventListener('click', () => { abortController?.abort(); });
  input.addEventListener('input', () => { autoResize(); sendBtn.disabled = isGenerating || !input.value.trim(); });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });

  function openApiKeyModal() {
    apiKeyInput.value = getApiKey();
    apiKeyInput.type = 'password';
    apiKeyEye.textContent = '👁';
    apiKeyOverlay.classList.add('open');
    apiKeyInput.focus();
  }
  function closeApiKeyModal() { apiKeyOverlay.classList.remove('open'); }
  apiKeyBtn.addEventListener('click', openApiKeyModal);
  apiKeyEye.addEventListener('click', () => {
    const isPass = apiKeyInput.type === 'password';
    apiKeyInput.type = isPass ? 'text' : 'password';
    apiKeyEye.textContent = isPass ? '🙈' : '👁';
  });
  apiKeySave.addEventListener('click', () => {
    const val = apiKeyInput.value.trim();
    if (!val) return;
    localStorage.setItem(API_KEY_KEY, val);
    updateApiBadge();
    closeApiKeyModal();
  });
  apiKeyDelete.addEventListener('click', () => {
    localStorage.removeItem(API_KEY_KEY);
    apiKeyInput.value = '';
    updateApiBadge();
    closeApiKeyModal();
  });
  apiKeyOverlay.querySelector('.btn-cancel').addEventListener('click', closeApiKeyModal);
  apiKeyOverlay.addEventListener('click', (e) => { if (e.target === apiKeyOverlay) closeApiKeyModal(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && apiKeyOverlay.classList.contains('open')) closeApiKeyModal(); });
  updateApiBadge();
})();
