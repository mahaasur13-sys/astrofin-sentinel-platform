import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { sanitizeHtml } from '@/lib/sanitize';
import { env } from '@/config/env';

const QUICK_BUTTONS = [
  { id: 'luck',    label: 'Удача',              icon: '🟢', color: '#22c55e', endpoint: `${env.VITE_API_URL}/astro/interpretation` },
  { id: 'muhurta', label: 'Muhurta',             icon: '⭐', color: '#eab308', endpoint: `${env.VITE_API_URL}/astro/interpretation` },
  { id: 'factors', label: 'Астро-факторы',        icon: '🔮', color: '#a78bfa', endpoint: `${env.VITE_API_URL}/astro/aspects` },
  { id: 'amrit',   label: 'Amrit',               icon: '💎', color: '#3b82f6', endpoint: `${env.VITE_API_URL}/astro/interpretation` },
  { id: 'agents',  label: 'Все 13 агентов',       icon: '🤖', color: '#f97316', endpoint: `${env.VITE_API_URL}/dashboard` },
] as const;

type QuickButtonId = (typeof QUICK_BUTTONS)[number]['id'];

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface AstroMindChatProps {
  variant?: 'embedded' | 'floating';
  className?: string;
}

const SAVED_PROMPTS_KEY = 'astrofin_saved_prompts';

function loadPrompts(): string[] {
  try { return JSON.parse(localStorage.getItem(SAVED_PROMPTS_KEY) || '[]') as string[]; } catch { return []; }
}
function savePrompts(prompts: string[]): void {
  localStorage.setItem(SAVED_PROMPTS_KEY, JSON.stringify(prompts));
}

function formatInterpretation(d: Record<string, unknown>, btnId: QuickButtonId): string {
  const score = (d.composite_score as number) ?? 77;
  const muhurta = (d.muhurta_score as number) ?? 90;
  const choghadiya = (d.choghadiya_current as Record<string, unknown>) ?? {};
  const nakshatra = (d.nakshatra as string) ?? 'Hasta';
  const grade = (d.nakshatra_grade as string) ?? 'благоприятная';
  const verdict = (d.verdict as string) ?? 'Благоприятно';
  const verdictIcon = (d.verdict_icon as string) ?? '🌟';

  const lines = [
    btnId === 'muhurta' || btnId === 'amrit'
      ? `### 🕉️ Muhurta & Timing\n\n**Muhurta Score:** ${muhurta}/100\n**Choghadiya:** ${choghadiya.name || 'Amrit'} (${choghadiya.quality || 'благоприятное'})\n**Nakshatra:** ${nakshatra} (${grade})\n\n**Рекомендация:** ${verdictIcon} ${verdict} (score: ${score}/100)`
      : `### 🌟 ${btnId === 'luck' ? 'Удача' : 'Анализ'} на текущий момент\n\n**Вердикт:** ${verdictIcon} ${verdict} (${score}/100)\n**Muhurta:** ${muhurta}/100 · **Choghadiya:** ${choghadiya.name || 'Amrit'} · **Nakshatra:** ${nakshatra}`,
  ];

  const topFav = d.top_favourable as Array<Record<string, unknown>> | undefined;
  if (topFav?.length) {
    lines.push('\n**🌟 Благоприятные аспекты:**');
    topFav.slice(0, 5).forEach((a) => lines.push(`  ${a.icon} ${a.planet1} ${a.type} ${a.planet2} — score: ${a.score}`));
  }

  const topUnf = d.top_unfavourable as Array<Record<string, unknown>> | undefined;
  if (topUnf?.length) {
    lines.push('\n**⚠️ Неблагоприятные аспекты:**');
    topUnf.slice(0, 5).forEach((a) => lines.push(`  ${a.icon} ${a.planet1} ${a.type} ${a.planet2} — score: ${a.score}`));
  }
  return lines.join('\n');
}

function formatAspects(d: Record<string, unknown>): string {
  const aspects = d.aspects as Array<Record<string, unknown>> | undefined;
  const lines = ['### 🔮 Астро-факторы (Swiss Ephemeris)', ''];
  if (aspects?.length) {
    lines.push(`**Всего аспектов:** ${aspects.length}`, '');
    aspects.forEach((a) => {
      const orb = typeof a.orb === 'number' ? a.orb.toFixed(2) : String(a.orb ?? '?');
      lines.push(`${a.icon || '·'} **${a.planet1} ${a.type} ${a.planet2}** — orb: ${orb}° · score: ${a.score}`);
    });
  } else {
    lines.push('Нет активных аспектов.');
  }
  lines.push('', '*Источник: Swiss Ephemeris (Самара 53°N/50°E)*');
  return lines.join('\n');
}

function formatDashboard(d: Record<string, unknown>): string {
  const agents = (d.agents as Array<Record<string, unknown>>) ?? [];
  const ensemble = d.ensemble as Record<string, unknown> | undefined;
  const lines = [
    '### 🤖 Решения 13 агентов',
    '',
    ...agents.map((a) => {
      const sig = (a.signal as string) || 'HOLD';
      const conf = Math.round(((a.confidence as number) || 0) * 100);
      const icon = sig === 'LONG' ? '🟢' : sig === 'SHORT' ? '🔴' : '🟡';
      return `${icon} **${a.name}:** ${sig} | Confidence: ${conf}%`;
    }),
    '',
    '### 🏛️ Финальное совместное решение:',
    '',
    `**Action:** ${ensemble?.signal || 'NEUTRAL'}`,
    `**Confidence:** ${Math.round(((ensemble?.confidence as number) || 0) * 100)}%`,
    `**Safety Gate:** ${d.safety_gate || 'SAFE'}`,
  ];
  return lines.join('\n');
}

export default function AstroMindChat({ variant = 'embedded', className = '' }: AstroMindChatProps) {
  const [msgs, setMsgs] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPrompts, setShowPrompts] = useState(false);
  const [savedPrompts, setSavedPrompts] = useState<string[]>(loadPrompts);
  const bottomRef = useRef<HTMLDivElement>(null);


  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [msgs]);

  const addMsg = useCallback((role: ChatMessage['role'], content: string) => {
    setMsgs((prev) => [...prev, { role, content }]);
  }, []);

  const sendQuick = useCallback(async (btn: (typeof QUICK_BUTTONS)[number]) => {
    addMsg('user', `${btn.icon} ${btn.label}`);
    setLoading(true);
    try {
      const r = await fetch(btn.endpoint);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json() as Record<string, unknown>;
      let content: string;
      if (btn.id === 'factors') {
        content = formatAspects(d);
      } else if (btn.id === 'agents') {
        content = formatDashboard(d);
      } else {
        content = formatInterpretation(d, btn.id);
      }
      addMsg('assistant', content);
    } catch {
      addMsg('assistant', '⚠️ Астро-данные временно недоступны.');
    } finally {
      setLoading(false);
    }
  }, [addMsg]);

  const sendPrompt = useCallback(async () => {
    const p = input.trim();
    if (!p) return;
    setInput('');
    addMsg('user', p);
    setLoading(true);
    try {
      const r = await fetch(`${env.VITE_API_URL}/agent/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agentId: 'ensemble', prompt: p }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json() as Record<string, unknown>;
      addMsg('assistant', (d.result || d.output || JSON.stringify(d, null, 2)) as string);
    } catch {
      addMsg('assistant', '⚠️ Не удалось получить ответ от агентов.');
    } finally {
      setLoading(false);
    }
  }, [input, addMsg]);

  const addSavedPrompt = useCallback(() => {
    const p = input.trim();
    if (!p || savedPrompts.includes(p)) return;
    const next = [p, ...savedPrompts].slice(0, 20);
    setSavedPrompts(next);
    savePrompts(next);
    setInput('');
  }, [input, savedPrompts]);

  const selectPrompt = useCallback((p: string) => {
    setInput(p);
    setShowPrompts(false);
  }, []);

  const containerClass = useMemo(() => {
    if (variant === 'floating') {
      return `fixed bottom-0 right-0 w-[420px] max-h-[75vh] z-100 border border-[var(--border,#30363d)] rounded-tl-2xl shadow-[0_-4px_20px_rgba(0,0,0,0.5)] ${className}`;
    }
    return `flex flex-col h-full rounded-lg overflow-hidden font-mono ${className}`;
  }, [variant, className]);

  return (
    <div className={containerClass} style={{ background: 'var(--bg-primary, #0d1117)', color: 'var(--text-primary, #e0e0e0)' }}>
      {/* Quick buttons */}
      <div className="flex gap-1 p-2 border-b border-[var(--border,#30363d)] flex-wrap">
        {QUICK_BUTTONS.map((b) => (
          <button
            key={b.id}
            onClick={() => sendQuick(b)}
            disabled={loading}
            className="inline-flex items-center gap-1 rounded-full px-3 py-1 text-[0.7rem] whitespace-nowrap cursor-pointer disabled:opacity-50 disabled:cursor-wait transition-colors"
            style={{ border: `1px solid ${b.color}`, color: b.color, background: 'transparent' }}
          >
            {b.icon} {b.label}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div
        className="flex-1 overflow-auto p-2 text-[0.78rem] min-h-[160px]"
        style={{ background: 'var(--bg-secondary, #0a0e14)', maxHeight: variant === 'floating' ? '350px' : undefined }}
      >
        {msgs.length === 0 && (
          <div className="text-center p-6 text-[0.75rem]" style={{ color: 'var(--text-muted, #8b949e)' }}>
            💬 Нажмите кнопку или введите промпт ниже<br />
            <span className="text-[0.65rem]">Все 13 агентов + контекст рынка</span>
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={`mb-2 ${m.role === 'user' ? 'text-right' : 'text-left'}`}>
            <div
              className="inline-block max-w-[92%] px-2.5 py-1.5 rounded-[10px] whitespace-pre-wrap text-left font-mono text-[0.73rem]"
              style={{
                background: m.role === 'user' ? 'var(--accent, #d8a657)' : 'var(--bg-card, #161b22)',
                color: m.role === 'user' ? '#000' : 'var(--text-primary, #c9d1d9)',
              }}
              dangerouslySetInnerHTML={{ __html: sanitizeHtml(m.content) }}
            />
          </div>
        ))}
        {loading && <div className="text-[0.7rem] pl-1" style={{ color: 'var(--accent, #d8a657)' }}>⏳ Анализ рынка...</div>}
        <div ref={bottomRef} />
      </div>

      {/* Input + prompt manager */}
      <div
        className="flex gap-1 p-1.5 items-center border-t border-[var(--border,#30363d)]"
        style={{ background: 'var(--bg-primary, #0d1117)' }}
      >
        <button
          onClick={() => setShowPrompts(!showPrompts)}
          className="bg-transparent border border-[var(--border,#30363d)] rounded-md px-2 py-1 text-[0.65rem] cursor-pointer"
          style={{ color: 'var(--text-muted, #8b949e)' }}
        >
          📋 Промпты
        </button>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendPrompt()}
          placeholder="Свой промпт для 13 агентов…"
          className="flex-1 rounded-md px-2.5 py-1.5 text-[0.75rem] outline-none"
          style={{ background: 'var(--bg-card, #161b22)', border: '1px solid var(--border, #30363d)', color: 'var(--text-primary, #c9d1d9)' }}
        />
        <button
          onClick={sendPrompt}
          disabled={loading || !input.trim()}
          className="rounded-md px-2.5 py-1.5 text-[0.75rem] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ background: 'var(--accent, #d8a657)', color: '#000', border: 'none' }}
        >
          ▶
        </button>
        <button
          onClick={addSavedPrompt}
          disabled={!input.trim()}
          className="bg-transparent border border-[var(--border,#30363d)] rounded-md px-1.5 py-1 text-[0.65rem] cursor-pointer disabled:opacity-50"
          style={{ color: 'var(--text-muted, #8b949e)' }}
        >
          💾
        </button>
      </div>

      {/* Prompt manager dropdown */}
      {showPrompts && (
        <div
          className="absolute bottom-[44px] left-0 right-0 max-h-[200px] overflow-auto z-[101] rounded-t-lg border border-[var(--border,#30363d)]"
          style={{ background: 'var(--bg-card, #161b22)' }}
        >
          {savedPrompts.length === 0 ? (
            <div className="p-3 text-[0.7rem] text-center" style={{ color: 'var(--text-muted, #8b949e)' }}>Нет сохранённых промптов</div>
          ) : (
            savedPrompts.map((p, i) => (
              <div
                key={i}
                onClick={() => selectPrompt(p)}
                className="px-2.5 py-1.5 text-[0.7rem] cursor-pointer border-b border-[var(--border,#30363d)]"
                style={{ color: 'var(--text-primary, #c9d1d9)' }}
              >
                {p.length > 80 ? p.slice(0, 80) + '…' : p}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
