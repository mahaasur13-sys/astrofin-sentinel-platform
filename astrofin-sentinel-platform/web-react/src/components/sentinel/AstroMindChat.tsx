// VBUILD-20260720-v2
if (typeof window !== "undefined") { window.__AstroMindChat = AstroMindChat; }
import { useState, useRef, useEffect } from 'react';

// ────────────────────────────────────── types
interface AstroResponse {
  interpretation: {
    verdict: string;
    verdict_text: string;
    composite_score: number;
    muhurta_score: number;
    nakshatra: string;
    nakshatra_grade: string;
    choghadiya_current: { name: string; icon: string; quality: string; start: string; end: string };
  };
  aspects: { top_favourable: Array<{planet1:string;planet2:string;type:string;icon:string;orb:number;score:number}>; top_unfavourable: Array<{planet1:string;planet2:string;type:string;icon:string;orb:number;score:number}> };
  agents?: { gann?: {signal:string;confidence:number}; bradley?: {signal:string;confidence:number}; elliot?: {signal:string;confidence:number} };
  dashboard?: { agents: Array<{name:string;signal:string;confidence:number;weight:number;status:string}> };
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

const QUICK_BUTTONS = [
  { id: 'luck', label: 'Удача', icon: '🟢', color: '#22c55e' },
  { id: 'muhurta', label: 'Muhurta: 90/100', icon: '⭐', color: '#eab308' },
  { id: 'factors', label: 'Показать астро-факторы', icon: '🔮', color: '#a78bfa' },
  { id: 'amrit', label: 'Amrit', icon: '💎', color: '#3b82f6' },
  { id: 'agents', label: 'Все 13 агентов + консенсус', icon: '🤖', color: '#f97316' },
];

// ────────────────────────────────────── component
export default function AstroMindChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', content: '👋 **AstroMind AI** готов. Задайте вопрос или нажмите быструю кнопку.' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [astroData, setAstroData] = useState<AstroResponse | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const addMessages = (msgs: ChatMessage[]) => {
    setMessages((prev) => [...prev, ...msgs]);
  };

  // ─── interpretation fetch
  const fetchInterpretation = async () => {
    try {
      const r = await fetch('/api/v1/astro/interpretation');
      if (!r.ok) throw new Error('API error');
      return await r.json();
    } catch { return null; }
  };

  const fetchDashboard = async () => {
    try {
      const r = await fetch('/api/v1/dashboard');
      if (!r.ok) throw new Error('API error');
      return await r.json();
    } catch { return null; }
  };

  const fetchAgent = async (name: string) => {
    try {
      const r = await fetch(`/api/v1/agent/analyze/${name}?symbol=BTCUSDT&price=64550`);
      if (!r.ok) throw new Error('API error');
      return await r.json();
    } catch { return null; }
  };

  // ─── format agent consensus response
  const formatConsensusResponse = (
    data: AstroResponse,
    dash: any
  ): string => {
    const interp = data.interpretation;
    const agents = dash?.agent_analysis || {};

    const agentNames: Record<string, string> = {
      fundamental: 'Fundamental', macro: 'Macro', quant: 'Quant',
      options_flow: 'OptionsFlow', sentiment: 'Sentiment', technical: 'Technical',
      bull_researcher: 'BullResearcher', bear_researcher: 'BearResearcher',
      bradley: 'Bradley', gann: 'Gann', elliot: 'Elliot',
      cycle: 'Cycle', electoral: 'Electoral', time_window: 'TimeWindow',
    };

    const lines: string[] = [];
    lines.push('### 🔮 Решения 13 агентов:');
    lines.push('');

    let longVotes = 0, shortVotes = 0, neutralVotes = 0;
    let totalConf = 0, count = 0;

    const keys = Object.keys(agents);
    if (keys.length === 0) {
      // Fallback: use dashboard agent list
      const dashAgents = dash?.agents || [];
      for (const a of dashAgents) {
        const signal = a.signal || 'NEUTRAL';
        const conf = a.confidence || 50;
        lines.push(`**${a.name || a.id}:** ${signal === 'LONG' ? '🟢' : signal === 'SHORT' ? '🔴' : '🟡'} ${signal} | Confidence: ${conf}%`);
        if (signal === 'LONG') longVotes++;
        else if (signal === 'SHORT') shortVotes++;
        else neutralVotes++;
        totalConf += conf;
        count++;
      }
    } else {
      for (const [key, agent] of Object.entries(agents) as [string, any][]) {
        const signal = agent?.signal || 'NEUTRAL';
        const conf = agent?.confidence || 50;
        const name = agentNames[key] || key;
        lines.push(`**${name}:** ${signal === 'LONG' ? '🟢' : signal === 'SHORT' ? '🔴' : '🟡'} ${signal} | Confidence: ${conf}%`);
        if (signal === 'LONG') longVotes++;
        else if (signal === 'SHORT') shortVotes++;
        else neutralVotes++;
        totalConf += conf;
        count++;
      }
    }

    lines.push('');
    lines.push('### 🧠 Финальное совместное решение:');
    lines.push('');

    const avgConf = count > 0 ? Math.round(totalConf / count) : 50;
    const finalSignal = longVotes > shortVotes + neutralVotes ? '🟢 LONG'
      : shortVotes > longVotes + neutralVotes ? '🔴 SHORT'
      : longVotes > shortVotes ? '🟡 NEUTRAL (LONG bias)'
      : shortVotes > longVotes ? '🟡 NEUTRAL (SHORT bias)'
      : '🟡 NEUTRAL';

    lines.push(`**Action:** ${finalSignal}`);
    lines.push(`**Confidence:** ${avgConf}%`);
    lines.push('');
    lines.push('**Астро-факторы:**');
    lines.push(`- Muhurta: ${interp.muhurta_score}/100 (${interp.nakshatra}, ${interp.nakshatra_grade})`);
    lines.push(`- Choghadiya: ${interp.choghadiya_current.name} ${interp.choghadiya_current.icon} (${interp.choghadiya_current.quality})`);
    lines.push(`- Composite Score: ${interp.composite_score}`);
    lines.push('');

    const fav = data.aspects?.top_favourable || [];
    const unf = data.aspects?.top_unfavourable || [];
    if (fav.length > 0) {
      lines.push('**Благоприятные аспекты:**');
      for (const a of fav.slice(0, 3)) {
        lines.push(`- ${a.icon} ${a.planet1} ${a.type} ${a.planet2} (orb: ${a.orb}°)`);
      }
    }
    if (unf.length > 0) {
      lines.push('**Напряжённые аспекты:**');
      for (const a of unf.slice(0, 3)) {
        lines.push(`- ${a.icon} ${a.planet1} ${a.type} ${a.planet2} (orb: ${a.orb}°)`);
      }
    }

    return lines.join('\n');
  };

  // ─── quick reply handler
  const handleQuickReply = async (btnId: string) => {
    addMessages([{ role: 'user', content: QUICK_BUTTONS.find((b) => b.id === btnId)?.label || btnId }]);
    setLoading(true);

    const interp = await fetchInterpretation();
    const dash = await fetchDashboard();

    if (btnId === 'luck') {
      if (interp) {
        const i = interp.interpretation;
        const text = i.composite_score >= 70
          ? `🌟 **Благоприятно!** Score: ${i.composite_score}/100\nMuhurta: ${i.muhurta_score}/100 · Nakshatra: ${i.nakshatra} (${i.nakshatra_grade})\nChoghadiya: ${i.choghadiya_current.name} ${i.choghadiya_current.icon}\nРекомендация: ${i.verdict_text}`
          : `🟡 **Caution.** Score: ${i.composite_score}/100\nMuhurta: ${i.muhurta_score}/100 · Лучше дождаться более сильного окна.`;
        addMessages([{ role: 'assistant', content: text }]);
      } else {
        addMessages([{ role: 'assistant', content: '⚠️ Астро-данные временно недоступны.' }]);
      }
    } else if (btnId === 'muhurta') {
      if (interp) {
        const i = interp.interpretation;
        addMessages([{ role: 'assistant', content: `⭐ **Muhurta: ${i.muhurta_score}/100**\nNakshatra: **${i.nakshatra}** (${i.nakshatra_grade})\nChoghadiya: **${i.choghadiya_current.name}** ${i.choghadiya_current.icon}\nКачество: *${i.choghadiya_current.quality}*\nОкно: ${i.choghadiya_current.start} – ${i.choghadiya_current.end}\n\n${i.muhurta_score >= 70 ? '✅ Отличное время для входа!' : i.muhurta_score >= 50 ? '🟡 Приемлемо, но с осторожностью.' : '🔴 Лучше воздержаться.'}` }]);
      }
    } else if (btnId === 'factors') {
      if (interp) {
        const fav = interp.aspects?.top_favourable || [];
        const unf = interp.aspects?.top_unfavourable || [];
        let text = '🔮 **Астрологические факторы:**\n\n';
        if (fav.length > 0) { text += '**Благоприятные:**\n'; for (const a of fav.slice(0,5)) text += `- ${a.icon} ${a.planet1} ${a.type} ${a.planet2} (orb: ${a.orb}°)\n`; }
        if (unf.length > 0) { text += '\n**Напряжённые:**\n'; for (const a of unf.slice(0,5)) text += `- ${a.icon} ${a.planet1} ${a.type} ${a.planet2} (orb: ${a.orb}°)\n`; }
        if (fav.length === 0 && unf.length === 0) text += 'Нет значимых аспектов в данный момент.';
        addMessages([{ role: 'assistant', content: text }]);
      }
    } else if (btnId === 'amrit') {
      if (interp) {
        const c = interp.interpretation.choghadiya_current;
        addMessages([{ role: 'assistant', content: `💎 **Amrit период**\nВремя: ${c.start} – ${c.end}\nТекущий Choghadiya: **${c.name}** ${c.icon}\nКачество: *${c.quality}*\n\nAmrit — наиболее благоприятный период суток для любых начинаний.` }]);
      }
    } else if (btnId === 'agents') {
      if (interp && dash) {
        const [gann, bradley, elliot] = await Promise.all([
          fetchAgent('gann'), fetchAgent('bradley'), fetchAgent('elliot'),
        ]);
        const fullData: AstroResponse = {
          ...interp,
          agents: { gann, bradley, elliot },
          dashboard: dash,
        };
        const text = formatConsensusResponse(fullData, dash);
        addMessages([{ role: 'assistant', content: text }]);
      } else {
        addMessages([{ role: 'assistant', content: '⚠️ Не удалось загрузить данные агентов.' }]);
      }
    }

    setAstroData(interp);
    setLoading(false);
  };

  // ─── free text submit
  const handleSubmit = async () => {
    if (!input.trim() || loading) return;
    addMessages([{ role: 'user', content: input }]);
    setInput('');
    setLoading(true);

    const interp = await fetchInterpretation();
    const dash = await fetchDashboard();

    if (interp && dash) {
      const text = formatConsensusResponse(interp, dash);
      addMessages([{ role: 'assistant', content: text }]);
    } else {
      addMessages([{ role: 'assistant', content: '⚠️ Не удалось получить данные. Проверьте соединение с API.' }]);
    }

    setAstroData(interp);
    setLoading(false);
  };

  // ────────────────────────────────────── render
  return (
      
    <div style={{
      display: 'flex', flexDirection: 'column', height: '100%',
      background: 'var(--bg-primary, #0a0a0f)', color: 'var(--text-primary, #e0e0e0)',
      borderRadius: 8, overflow: 'hidden', fontFamily: 'monospace',
    }}>
      {/* Quick buttons */}
      <div style={{
        display: 'flex', gap: 8, padding: '12px 16px', flexWrap: 'wrap',
        borderBottom: '1px solid var(--border, #1a1a2e)',
        background: 'rgba(10,10,20,0.95)',
      }}>
        {QUICK_BUTTONS.map((btn) => (
          <button
            key={btn.id}
            onClick={() => handleQuickReply(btn.id)}
            disabled={loading}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              padding: '6px 14px', borderRadius: 20, border: `1px solid ${btn.color}40`,
              background: `${btn.color}15`, color: btn.color, cursor: loading ? 'wait' : 'pointer',
              fontSize: 13, fontWeight: 600, transition: 'all 0.2s',
              opacity: loading ? 0.5 : 1,
            }}
            onMouseEnter={(e) => { if (!loading) { e.currentTarget.style.background = `${btn.color}25`; e.currentTarget.style.borderColor = btn.color; }}}
            onMouseLeave={(e) => { if (!loading) { e.currentTarget.style.background = `${btn.color}15`; e.currentTarget.style.borderColor = `${btn.color}40`; }}}
          >
            <span style={{ fontSize: 16 }}>{btn.icon}</span>
            {btn.label}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div style={{
        flex: 1, overflowY: 'auto', padding: '12px 16px',
        display: 'flex', flexDirection: 'column', gap: 10,
      }}>
        {messages.map((m, i) => (
          <div key={i} style={{
            alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: '85%',
            background: m.role === 'user' ? 'var(--accent, #3b82f6)' : 'rgba(20,20,40,0.8)',
            color: m.role === 'user' ? '#fff' : 'var(--text-primary, #e0e0e0)',
            padding: '10px 14px', borderRadius: 12,
            fontSize: 13, lineHeight: 1.6,
            whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            border: m.role === 'assistant' ? '1px solid var(--border, #1a1a2e)' : 'none',
          }}>
            <Markdown text={m.content} />
          </div>
        ))}
        {loading && (
          <div style={{ alignSelf: 'flex-start', padding: '8px 14px', color: 'var(--text-muted, #666)', fontSize: 12 }}>
            ⏳ Анализирую...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{
        display: 'flex', gap: 8, padding: '10px 16px',
        borderTop: '1px solid var(--border, #1a1a2e)',
        background: 'rgba(10,10,20,0.95)',
      }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit(); }}
          placeholder="Задайте вопрос о рынке..."
          disabled={loading}
          style={{
            flex: 1, padding: '8px 12px', borderRadius: 8,
            border: '1px solid var(--border, #1a1a2e)',
            background: 'rgba(0,0,0,0.3)', color: '#e0e0e0',
            fontSize: 13, fontFamily: 'monospace', outline: 'none',
          }}
        />
        <button
          onClick={handleSubmit}
          disabled={loading || !input.trim()}
          style={{
            padding: '8px 16px', borderRadius: 8, border: 'none',
            background: loading ? '#333' : 'var(--accent, #3b82f6)',
            color: '#fff', cursor: loading ? 'wait' : 'pointer',
            fontSize: 13, fontWeight: 600,
          }}
        >
          →
        </button>
      </div>
    </div>
  );
}

// ─── simple markdown renderer (bold, italic, code, headings)
function Markdown({ text }: { text: string }) {
  if (!text) return null;
  const html = text
    .replace(/### (.*)/g, '<h4 style="margin:6px 0;color:var(--accent,#3b82f6)">$1</h4>')
    .replace(/## (.*)/g, '<h3 style="margin:6px 0;color:var(--accent,#3b82f6)">$1</h3>')
    .replace(/# (.*)/g, '<h2 style="margin:6px 0;color:var(--accent,#3b82f6)">$1</h2>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br/>')
    .replace(/`([^`]+)`/g, '<code style="background:rgba(255,255,255,0.1);padding:1px 4px;border-radius:3px">$1</code>')
    .replace(/- (.*)/g, '<li style="margin-left:12px">$1</li>');
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}
