/* ============================================================
   ROMA CORE JS — Shared JavaScript
   DecisionOS v2.0 · ROMA Execution Bridge
   ============================================================ */

/* ===== ORBITAL PARTICLES (4 layers, accelerated, 60fps) ===== */
(function() {
  const canvas = document.getElementById('orbital-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let w, h, particles = [];
  const COLORS = ['#06d6d6', '#a855f7', '#22c55e', '#06b6d4', '#c084fc'];

  function resize() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
  }

  function createParticles() {
    particles = [];
    for (let i = 0; i < 28; i++)
      particles.push({ layer:1, x:Math.random()*w, y:Math.random()*h, r:0.6+Math.random()*1.2, orbitR:40+Math.random()*120, angle:Math.random()*Math.PI*2, speed:0.018+Math.random()*0.022, color:COLORS[Math.floor(Math.random()*COLORS.length)], alpha:0.35+Math.random()*0.4 });
    for (let i = 0; i < 18; i++)
      particles.push({ layer:2, x:Math.random()*w, y:Math.random()*h, r:1.2+Math.random()*1.8, orbitR:60+Math.random()*160, angle:Math.random()*Math.PI*2, speed:0.010+Math.random()*0.014, color:COLORS[Math.floor(Math.random()*COLORS.length)], alpha:0.25+Math.random()*0.35 });
    for (let i = 0; i < 10; i++)
      particles.push({ layer:3, x:Math.random()*w, y:Math.random()*h, r:2+Math.random()*3, orbitR:80+Math.random()*200, angle:Math.random()*Math.PI*2, speed:0.005+Math.random()*0.008, color:COLORS[Math.floor(Math.random()*COLORS.length)], alpha:0.15+Math.random()*0.25 });
    for (let i = 0; i < 8; i++)
      particles.push({ layer:4, x:Math.random()*w, y:Math.random()*h, r:0.8, orbitR:50+Math.random()*140, angle:Math.random()*Math.PI*2, speed:0.012+Math.random()*0.016, color:COLORS[Math.floor(Math.random()*3)], alpha:0.12+Math.random()*0.18, isLine:true });
  }

  function draw() {
    ctx.clearRect(0, 0, w, h);
    particles.forEach(p => {
      p.angle += p.speed;
      const cx = p.x + Math.cos(p.angle) * p.orbitR * 0.6;
      const cy = p.y + Math.sin(p.angle) * p.orbitR * 0.35;
      if (p.isLine) {
        ctx.beginPath();
        ctx.ellipse(p.x, p.y, p.orbitR*0.7, p.orbitR*0.35, 0, 0, Math.PI*2);
        ctx.strokeStyle = p.color; ctx.globalAlpha = p.alpha*0.5; ctx.lineWidth = 0.6; ctx.stroke();
      }
      ctx.beginPath(); ctx.arc(cx, cy, p.r, 0, Math.PI*2);
      ctx.fillStyle = p.color; ctx.globalAlpha = p.alpha;
      ctx.shadowBlur = p.layer === 3 ? 12 : 4; ctx.shadowColor = p.color; ctx.fill(); ctx.shadowBlur = 0;
    });
    ctx.globalAlpha = 1;
    requestAnimationFrame(draw);
  }

  resize(); createParticles(); draw();
  window.addEventListener('resize', () => { resize(); createParticles(); });
})();

/* ===== ROMA — Global App Object ===== */
window.ROMA = window.ROMA || {};

/* ===== API KEY MANAGEMENT ===== */
(function() {
  const STORAGE = 'roma_api_key';
  ROMA.getApiKey = function() { return localStorage.getItem(STORAGE) || ''; };
  ROMA.hasApiKey = function() { return !!ROMA.getApiKey(); };

  function updateStatusDots() {
    const has = ROMA.hasApiKey();
    document.querySelectorAll('#keyStatusDot, #chatKeyDot, [data-key-dot]').forEach(el => el.classList.toggle('active', has));
  }

  function openModal() {
    const modal = document.getElementById('apiKeyModal');
    const input = document.getElementById('apiKeyInput');
    const toggleBtn = document.getElementById('toggleVisibility');
    if (!modal || !input) return;
    input.value = ROMA.getApiKey();
    input.type = 'password';
    if (toggleBtn) toggleBtn.textContent = '👁';
    modal.classList.add('open');
    setTimeout(() => input.focus(), 100);
  }

  function closeModal() {
    const modal = document.getElementById('apiKeyModal');
    if (modal) modal.classList.remove('open');
  }

  ROMA.showToast = function(msg) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2800);
  };

  // Bind triggers
  document.querySelectorAll('#apiKeyBtn, #chatApiKeyBtn, [data-open-api-modal]').forEach(btn => btn.addEventListener('click', openModal));
  document.getElementById('modalClose')?.addEventListener('click', closeModal);
  document.getElementById('cancelKeyBtn')?.addEventListener('click', closeModal);
  document.getElementById('apiKeyModal')?.addEventListener('click', e => { if (e.target === e.currentTarget) closeModal(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

  document.getElementById('toggleVisibility')?.addEventListener('click', function() {
    const input = document.getElementById('apiKeyInput');
    if (!input) return;
    const isPass = input.type === 'password';
    input.type = isPass ? 'text' : 'password';
    this.textContent = isPass ? '🙈' : '👁';
  });

  document.getElementById('saveKeyBtn')?.addEventListener('click', () => {
    const val = document.getElementById('apiKeyInput')?.value?.trim();
    if (val) { localStorage.setItem(STORAGE, val); ROMA.showToast('✅ API Key успешно сохранён'); }
    else { localStorage.removeItem(STORAGE); ROMA.showToast('🗑 API Key удалён'); }
    updateStatusDots(); closeModal();
  });

  document.getElementById('deleteKeyBtn')?.addEventListener('click', () => {
    localStorage.removeItem(STORAGE);
    const input = document.getElementById('apiKeyInput');
    if (input) input.value = '';
    updateStatusDots();
    ROMA.showToast('🗑 API Key удалён');
    closeModal();
  });

  updateStatusDots();
})();

/* ===== ANIMATED COUNTERS ===== */
(function() {
  function easeOutCubic(t) { return 1 - Math.pow(1 - t, 3); }
  const observed = new Set();
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting || observed.has(entry.target)) return;
      observed.add(entry.target);
      entry.target.querySelectorAll('[data-target]').forEach(el => {
        const target = parseInt(el.dataset.target, 10);
        const duration = 1800;
        const start = performance.now();
        function tick(now) {
          const eased = easeOutCubic(Math.min((now - start) / duration, 1));
          const val = Math.floor(target * eased);
          el.textContent = val >= 1000 ? val.toLocaleString('en-US') : val;
          if ((now - start) < duration) requestAnimationFrame(tick);
          else el.textContent = target >= 1000 ? target.toLocaleString('en-US') : target;
        }
        requestAnimationFrame(tick);
      });
    });
  }, { threshold: 0.3 });
  document.querySelectorAll('[data-counter-section]').forEach(s => observer.observe(s));
})();

/* ===== AI CHAT (streaming + Stop + history + name) ===== */
(function() {
  const fab = document.getElementById('chatFab');
  const windowEl = document.getElementById('chatWindow');
  const closeBtn = document.getElementById('chatCloseBtn');
  const messagesEl = document.getElementById('chatMessages');
  const inputEl = document.getElementById('chatInput');
  const sendBtn = document.getElementById('chatSend');
  const stopBtn = document.getElementById('chatStop');
  const openTriggers = document.querySelectorAll('#openChatFromHero, [data-open-chat]');

  const HISTORY_KEY = 'roma_chat_history';
  const NAME_KEY = 'roma_user_name';
  let userName = localStorage.getItem(NAME_KEY) || '';
  let isStreaming = false;
  let abortController = null;

  function openChat() {
    if (!windowEl) return;
    windowEl.classList.add('open');
    if (!userName) {
      setTimeout(() => {
        const name = prompt('Введите ваше имя для ROMA Assistant:');
        if (name && name.trim()) {
          userName = name.trim();
          localStorage.setItem(NAME_KEY, userName);
          addSystemMessage(`Добро пожаловать, ${userName}! Готов выполнять команды.`);
        }
      }, 300);
    }
    inputEl?.focus();
  }

  function closeChat() { windowEl?.classList.remove('open'); }

  fab?.addEventListener('click', openChat);
  openTriggers.forEach(btn => btn.addEventListener('click', openChat));
  closeBtn?.addEventListener('click', closeChat);

  function addMessage(role, text) {
    if (!messagesEl) return;
    const div = document.createElement('div');
    div.className = `msg ${role}`;
    div.textContent = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    saveHistory();
    return div;
  }

  function addSystemMessage(text) { addMessage('system', text); }

  function saveHistory() {
    if (!messagesEl) return;
    const msgs = [];
    messagesEl.querySelectorAll('.msg').forEach(m => {
      if (!m.classList.contains('system'))
        msgs.push({ role: m.classList.contains('user') ? 'user' : 'assistant', text: m.textContent });
    });
    localStorage.setItem(HISTORY_KEY, JSON.stringify(msgs.slice(-40)));
  }

  function loadHistory() {
    try {
      const raw = localStorage.getItem(HISTORY_KEY);
      if (!raw) return;
      JSON.parse(raw).forEach(m => addMessage(m.role, m.text));
    } catch (e) {}
  }

  loadHistory();
  if (messagesEl && messagesEl.children.length === 0)
    addSystemMessage('ROMA AI Assistant online. Streaming ready.');

  async function streamResponse(userText) {
    if (!messagesEl) return;
    isStreaming = true;
    if (sendBtn) sendBtn.style.display = 'none';
    stopBtn?.classList.add('visible');
    abortController = new AbortController();

    const assistantDiv = addMessage('assistant', '');
    const responses = [
      `Понял, ${userName || 'оператор'}. Инициирую задачу через ROMA Execution Bridge…`,
      `Проверяю доступность GPU-кластера… X-API-Key ${ROMA.hasApiKey() ? 'обнаружен' : 'не установлен'}.`,
      `Задача принята в очередь. Job ID: job_${Date.now().toString(36)}. Статус: queued → running.`,
      `Мониторинг активен. Используйте GET /status/{job_id} для отслеживания.`
    ];
    let full = '';
    try {
      for (const chunk of responses) {
        if (abortController.signal.aborted) break;
        for (const char of chunk + ' ') {
          if (abortController.signal.aborted) break;
          full += char;
          assistantDiv.textContent = full;
          messagesEl.scrollTop = messagesEl.scrollHeight;
          await new Promise(r => setTimeout(r, 12 + Math.random() * 18));
        }
        await new Promise(r => setTimeout(r, 180));
      }
    } catch (e) {}
    isStreaming = false;
    if (sendBtn) sendBtn.style.display = 'flex';
    stopBtn?.classList.remove('visible');
    saveHistory();
  }

  function sendMessage() {
    if (!inputEl) return;
    const text = inputEl.value.trim();
    if (!text || isStreaming) return;
    addMessage('user', text);
    inputEl.value = '';
    inputEl.style.height = 'auto';
    streamResponse(text);
  }

  sendBtn?.addEventListener('click', sendMessage);
  inputEl?.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });
  stopBtn?.addEventListener('click', () => {
    if (abortController) abortController.abort();
    isStreaming = false;
    if (sendBtn) sendBtn.style.display = 'flex';
    stopBtn?.classList.remove('visible');
  });
  inputEl?.addEventListener('input', () => {
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 140) + 'px';
  });
})();

/* ===== NAV ACTIVE STATE ===== */
(function() {
  const path = window.location.pathname.replace(/\/$/, '') || '/';
  document.querySelectorAll('.nav a').forEach(a => {
    const href = a.getAttribute('href') || '';
    if (href === path || (path !== '/' && href !== '/' && path.includes(href)))
      a.classList.add('active');
  });
})();
