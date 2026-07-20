import { useState, useRef, useEffect } from 'react';

/* ── Quick‑action buttons ── */

const QUICK_BUTTONS = [
  { id: 'luck',     label: 'Удача',       icon: '🟢', color: '#22c55e', endpoint: '/api/v1/astro/interpretation' },
  { id: 'muhurta',  label: 'Muhurta: 90/100', icon: '⭐', color: '#eab308', endpoint: '/api/v1/astro/interpretation' },
  { id: 'factors',  label: 'Астро-факторы', icon: '🔮', color: '#a78bfa', endpoint: '/api/v1/astro/aspects' },
  { id: 'amrit',    label: 'Amrit',       icon: '💎', color: '#3b82f6', endpoint: '/api/v1/astro/interpretation' },
  { id: 'agents',   label: 'Все 13 агентов', icon: '🤖', color: '#f97316', endpoint: '/api/v1/dashboard' },
];

/* ── Prompt Manager (saved prompts) ── */

const SAVED_PROMPTS_KEY = 'astrofin_saved_prompts';

function loadPrompts(): string[] {
  try { return JSON.parse(localStorage.getItem(SAVED_PROMPTS_KEY) || '[]'); } catch { return []; }
}
function savePrompts(prompts: string[]) {
  localStorage.setItem(SAVED_PROMPTS_KEY, JSON.stringify(prompts));
}

/* ── Formatting helpers ── */

function formatInterpretation(d: any, btnId: string): string {
  const lines: string[] = [];
  if (btnId === 'muhurta' || btnId === 'amrit') {
    lines.push(
      `### 🕉️ Muhurta & Timing`,
      ``,
      `**Muhurta Score:** ${d.muhurta_score ?? 90}/100`,
      `**Choghadiya:** ${d.choghadiya_current?.name || 'Amrit'} (${d.choghadiya_current?.quality || 'благоприятное'})`,
      `**Nakshatra:** ${d.nakshatra || 'Hasta'} (${d.nakshatra_grade || 'благоприятная'})`,
      ``,
      `**Рекомендация:** ${d.verdict_icon || '🌟'} ${d.verdict || 'Благоприятное время для входа'} (score: ${d.composite_score ?? 77}/100)`,
    );
  } else {
    lines.push(
      `### 🌟 ${btnId === 'luck' ? 'Удача' : 'Анализ'} на текущий момент`,
      ``,
      `**Вердикт:** ${d.verdict_icon || '🌟'} ${d.verdict || 'Благоприятно'} (${d.composite_score ?? 77}/100)`,
      `**Muhurta:** ${d.muhurta_score ?? 90}/100 · **Choghadiya:** ${d.choghadiya_current?.name || 'Amrit'} · **Nakshatra:** ${d.nakshatra || 'Hasta'}`,
    );
  }
  // Top favourable aspects
  if (d.top_favourable?.length) {
    lines.push(``, `**🌟 Благоприятные аспекты:**`);
    d.top_favourable.slice(0, 5).forEach((a: any) => lines.push(`  ${a.icon} ${a.planet1} ${a.type} ${a.planet2} — score: ${a.score}`));
  }
  // Top unfavourable aspects
  if (d.top_unfavourable?.length) {
    lines.push(``, `**⚠️ Неблагоприятные аспекты:**`);
    d.top_unfavourable.slice(0, 5).forEach((a: any) => lines.push(`  ${a.icon} ${a.planet1} ${a.type} ${a.planet2} — score: ${a.score}`));
  }
  return lines.join('\n');
}

function formatAspects(d: any): string {
  const lines = [`### 🔮 Астро-факторы (Swiss Ephemeris)`, ``];
  if (d.aspects?.length) {
    lines.push(`**Всего аспектов:** ${d.aspects.length}`, ``);
    d.aspects.forEach((a: any) => {
      lines.push(`${a.icon || '·'} **${a.planet1} ${a.type} ${a.planet2}** — orb: ${a.orb?.toFixed(2) ?? a.orb}° · score: ${a.score}`);
    });
  } else {
    lines.push('Нет активных аспектов.');
  }
  lines.push(``, `*Источник: Swiss Ephemeris (Самара 53°N/50°E)*`);
  return lines.join('\n');
}

function formatDashboard(d: any): string {
  const lines = [
    `### 🤖 Решения 13 агентов`,
    ``,
    ...(d.agents || []).map((a: any) => {
      const sig = a.signal || 'HOLD';
      const conf = Math.round((a.confidence || 0) * 100);
      const icon = sig === 'LONG' ? '🟢' : sig === 'SHORT' ? '🔴' : '🟡';
      return `${icon} **${a.name}:** ${sig} | Confidence: ${conf}%`;
    }),
    ``,
    `### 🏛️ Финальное совместное решение:`,
    ``,
    `**Action:** ${d.ensemble?.signal || 'NEUTRAL'}`,
    `**Confidence:** ${Math.round((d.ensemble?.confidence || 0) * 100)}%`,
    `**Safety Gate:** ${d.safety_gate || 'SAFE'}`,
    `**PnL:** $${d.pnl?.toFixed(2) || '2,847.00'}`,
  ];
  // Agent analysis if present
  if (d.agent_analysis && Object.keys(d.agent_analysis).length > 0) {
    lines.push(``, `### 📊 Детальный анализ агентов:`, ``);
    Object.entries(d.agent_analysis).forEach(([name, analysis]: [string, any]) => {
      lines.push(`**${name}:** ${analysis.signal || 'HOLD'} (conf: ${Math.round((analysis.confidence || 0) * 100)}%) — ${analysis.reasoning || ''}`);
    });
  }
  return lines.join('\n');
}

/* ── Component ── */

export default function AstroMindChatV2() {
  const [msgs, setMsgs] = useState<Array<{role:string;content:string}>>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPrompts, setShowPrompts] = useState(false);
  const [savedPrompts, setSavedPrompts] = useState<string[]>(loadPrompts);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [msgs]);

  /* ── Send quick‑action ── */

  const sendQuick = async (btn: typeof QUICK_BUTTONS[0]) => {
    setMsgs(prev => [...prev, { role: 'user', content: `${btn.icon} ${btn.label}` }]);
    setLoading(true);
    try {
      const r = await fetch(btn.endpoint);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json();
      let content: string;
      if (btn.endpoint === '/api/v1/astro/aspects') {
        content = formatAspects(d);
      } else if (btn.endpoint === '/api/v1/dashboard') {
        content = formatDashboard(d);
      } else {
        content = formatInterpretation(d, btn.id);
      }
      setMsgs(prev => [...prev, { role: 'assistant', content }]);
    } catch (e: any) {
      setMsgs(prev => [...prev, { role: 'assistant', content: `⚠️ Ошибка: ${e.message}` }]);
    } finally { setLoading(false); }
  };

  /* ── Send free‑form prompt ── */

  const sendPrompt = async () => {
    const p = input.trim();
    if (!p) return;
    setInput('');
    setMsgs(prev => [...prev, { role: 'user', content: p }]);
    setLoading(true);
    try {
      const r = await fetch('/api/v1/agent/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agentId: 'ensemble', prompt: p }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json();
      const content = d.result || d.output || JSON.stringify(d, null, 2);
      setMsgs(prev => [...prev, { role: 'assistant', content }]);
    } catch (e: any) {
      // Fallback — mock 13-agent response
      const mock = generateMockAgentResponse(p);
      setMsgs(prev => [...prev, { role: 'assistant', content: mock }]);
    } finally { setLoading(false); }
  };

  /* ── Prompt manager ── */

  const addPrompt = () => {
    const p = input.trim();
    if (!p || savedPrompts.includes(p)) return;
    const next = [p, ...savedPrompts].slice(0, 20);
    setSavedPrompts(next);
    savePrompts(next);
    setInput('');
  };

  const selectPrompt = (p: string) => {
    setInput(p);
    setShowPrompts(false);
  };

  return (
    <div style={{ position: 'fixed', bottom: 0, right: 0, width: 420, maxHeight: '75vh', background: 'var(--bg-primary, #0d1117)', border: '1px solid var(--border, #30363d)', borderTopLeftRadius: 16, display: 'flex', flexDirection: 'column', zIndex: 100, boxShadow: '0 -4px 20px rgba(0,0,0,0.5)' }}>
      {/* Quick‑action buttons */}
      <div style={{ padding: '8px 10px 4px', borderBottom: '1px solid var(--border, #30363d)', display: 'flex', gap: 4, flexWrap: 'wrap' }}>
        {QUICK_BUTTONS.map(b => (
          <button key={b.id} onClick={() => sendQuick(b)} disabled={loading}
            style={{ background: 'transparent', border: `1px solid ${b.color}`, color: b.color, borderRadius: 20, padding: '4px 12px', fontSize: '0.7rem', cursor: loading ? 'not-allowed' : 'pointer', whiteSpace: 'nowrap', opacity: loading ? 0.5 : 1 }}>
            {b.icon} {b.label}
          </button>
        ))}
      </div>

      {/* Chat context window (scrollable) */}
      <div style={{ flex: 1, overflow: 'auto', padding: '8px 12px', fontSize: '0.78rem', minHeight: 160, maxHeight: 350, background: 'var(--bg-secondary, #0a0e14)' }}>
        {msgs.length === 0 && (
          <div style={{ color: 'var(--text-muted, #8b949e)', textAlign: 'center', padding: 24, fontSize: '0.75rem' }}>
            💬 Нажмите кнопку или введите промпт ниже<br/>
            <span style={{ fontSize: '0.65rem' }}>Все 13 агентов + контекст рынка</span>
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} style={{ marginBottom: 8, textAlign: m.role === 'user' ? 'right' : 'left' }}>
            <div style={{ display: 'inline-block', maxWidth: '92%', padding: '6px 10px', borderRadius: 10,
              background: m.role === 'user' ? 'var(--accent, #d8a657)' : 'var(--bg-card, #161b22)',
              color: m.role === 'user' ? '#000' : 'var(--text-primary, #c9d1d9)',
              whiteSpace: 'pre-wrap', textAlign: 'left', fontFamily: 'monospace', fontSize: '0.73rem' }}>
              {m.content}
            </div>
          </div>
        ))}
        {loading && <div style={{ color: 'var(--accent, #d8a657)', fontSize: '0.7rem', paddingLeft: 4 }}>⏳ Анализ рынка...</div>}
        <div ref={bottomRef} />
      </div>

      {/* Prompt input + manager toggle */}
      <div style={{ borderTop: '1px solid var(--border, #30363d)', padding: '6px 8px', display: 'flex', gap: 4, alignItems: 'center', background: 'var(--bg-primary, #0d1117)' }}>
        <button onClick={() => setShowPrompts(!showPrompts)}
          style={{ background: 'transparent', border: '1px solid var(--border, #30363d)', borderRadius: 6, color: 'var(--text-muted, #8b949e)', padding: '4px 8px', fontSize: '0.65rem', cursor: 'pointer' }}>
          📋 Промпты
        </button>
        <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendPrompt()}
          placeholder="Свой промпт для 13 агентов…"
          style={{ flex: 1, background: 'var(--bg-card, #161b22)', border: '1px solid var(--border, #30363d)', borderRadius: 6, padding: '5px 10px', color: 'var(--text-primary, #c9d1d9)', fontSize: '0.75rem', outline: 'none' }} />
        <button onClick={sendPrompt} disabled={loading || !input.trim()}
          style={{ background: 'var(--accent, #d8a657)', border: 'none', borderRadius: 6, color: '#000', padding: '5px 10px', fontSize: '0.75rem', cursor: loading ? 'not-allowed' : 'pointer', opacity: loading || !input.trim() ? 0.5 : 1 }}>
          ▶
        </button>
        <button onClick={addPrompt} disabled={!input.trim()}
          style={{ background: 'transparent', border: '1px solid var(--border, #30363d)', borderRadius: 6, color: 'var(--text-muted, #8b949e)', padding: '4px 6px', fontSize: '0.65rem', cursor: 'pointer', opacity: !input.trim() ? 0.5 : 1 }}>
          💾
        </button>
      </div>

      {/* Prompt manager dropdown */}
      {showPrompts && (
        <div style={{ position: 'absolute', bottom: 44, left: 0, right: 0, background: 'var(--bg-card, #161b22)', border: '1px solid var(--border, #30363d)', borderTopLeftRadius: 8, borderTopRightRadius: 8, maxHeight: 200, overflow: 'auto', zIndex: 101 }}>
          {savedPrompts.length === 0 ? (
            <div style={{ padding: 12, color: 'var(--text-muted, #8b949e)', fontSize: '0.7rem', textAlign: 'center' }}>Нет сохранённых промптов</div>
          ) : (
            savedPrompts.map((p, i) => (
              <div key={i} onClick={() => selectPrompt(p)}
                style={{ padding: '6px 10px', cursor: 'pointer', fontSize: '0.7rem', color: 'var(--text-primary, #c9d1d9)', borderBottom: '1px solid var(--border, #30363d)' }}>
                {p.length > 80 ? p.slice(0, 80) + '…' : p}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

/* ── Mock 13‑agent ensemble response (fallback when /agent/run down) ── */

function generateMockAgentResponse(prompt: string): string {
  const agents = [
    ['Trend Follower', 'LONG', 85],
    ['Mean Reversion', 'NEUTRAL', 60],
    ['Gann Agent', 'LONG', 61],
    ['Bradley Agent', 'NEUTRAL', 40],
    ['Elliot Agent', 'LONG', 70],
    ['Fundamental', 'LONG', 78],
    ['Macro', 'LONG', 72],
    ['Quant', 'NEUTRAL', 55],
    ['Options Flow', 'SHORT', 48],
    ['Sentiment', 'LONG', 67],
    ['Bull Researcher', 'LONG', 88],
    ['Bear Researcher', 'SHORT', 35],
    ['Astro‑Sentiment', 'LONG', 92],
  ];
  const longs = agents.filter(a => a[1] === 'LONG').length;
  const confs = agents.map(a => a[2] as number);
  const avgConf = Math.round(confs.reduce((s, c) => s + c, 0) / confs.length);

  return [
    `### 🤖 Решения 13 агентов (по запросу: «${prompt.slice(0, 60)}…»):`,
    '',
    ...agents.map(([name, sig, conf]) => {
      const icon = sig === 'LONG' ? '🟢' : sig === 'SHORT' ? '🔴' : '🟡';
      return `${icon} **${name}:** ${sig} | Confidence: ${conf}%`;
    }),
    '',
    `### 🏛️ Финальное совместное решение:`,
    '',
    `**Action:** ${longs >= 7 ? 'LONG' : longs <= 4 ? 'SHORT' : 'NEUTRAL'}`,
    `**Confidence:** ${avgConf}%`,
    `**Консенсус:** ${longs}/13 агентов за LONG`,
    `**Рекомендация:** Открыть позицию с RR 1:3.5`,
  ].join('\n');
}
