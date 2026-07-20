import { useState, useRef, useEffect } from 'react';

const QUICK_BUTTONS = [
  { id: 'luck', label: 'Удача', icon: '🟢', color: '#22c55e' },
  { id: 'muhurta', label: 'Muhurta: 90/100', icon: '⭐', color: '#eab308' },
  { id: 'factors', label: 'Показать астро-факторы', icon: '🔮', color: '#a78bfa' },
  { id: 'amrit', label: 'Amrit', icon: '💎', color: '#3b82f6' },
  { id: 'agents', label: 'Все 13 агентов + консенсус', icon: '🤖', color: '#f97316' },
];

// Force side-effect to prevent tree-shaking
if (typeof window !== 'undefined') {
  (window as any).__CHATV2_LOADED = 1;
}

export default function AstroMindChatV2() {
  const [msgs, setMsgs] = useState<Array<{role:string;content:string}>>([]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [msgs]);

  const send = async (q: string) => {
    setMsgs(prev => [...prev, { role: 'user', content: q }]);
    setLoading(true);
    try {
      const r = await fetch('/api/v1/astro/interpretation');
      const d = await r.json();
      const lines = [
        `### 🌟 AstroFin Sentinel — Ответ`,
        ``,
        `**Вердикт:** ${d.verdict_icon} ${d.verdict} (${d.composite_score}/100)`,
        `**Muhurta:** ${d.muhurta_score}/100 · **Choghadiya:** ${d.choghadiya_current?.name || '—'} (${d.choghadiya_current?.quality || ''})`,
        `**Nakshatra:** ${d.nakshatra} (${d.nakshatra_grade})`,
        ``,
        `### Решения 13 агентов:`,
        ...(d.dashboard?.agents || []).map((a: any) =>
          `**${a.name}:** ${a.signal || 'HOLD'} | Confidence: ${Math.round(a.confidence * 100)}% | Weight: ${a.weight}`),
        ``,
        `### Финальное совместное решение:`,
        `**Action:** ${d.ensemble?.signal || 'NEUTRAL'} · **Confidence:** ${Math.round((d.ensemble?.confidence || 0) * 100)}%`,
        `**Safety Gate:** ${d.safety_gate || 'SAFE'}`,
      ].join('\n');
      setMsgs(prev => [...prev, { role: 'assistant', content: lines }]);
    } catch {
      setMsgs(prev => [...prev, { role: 'assistant', content: '⚠️ Ошибка API' }]);
    } finally { setLoading(false); }
  };

  return (
    <div style={{ position: 'fixed', bottom: 0, right: 0, width: 420, maxHeight: '70vh', background: 'var(--bg-primary)', border: '1px solid var(--border)', borderTopLeftRadius: 16, display: 'flex', flexDirection: 'column', zIndex: 100, boxShadow: '0 -4px 20px rgba(0,0,0,0.5)' }}>
      <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--border)', display: 'flex', gap: 4, flexWrap: 'wrap' }}>
        {QUICK_BUTTONS.map(b => (
          <button key={b.id} onClick={() => send(b.label)} disabled={loading}
            style={{ background: 'transparent', border: `1px solid ${b.color}`, color: b.color, borderRadius: 20, padding: '4px 12px', fontSize: '0.75rem', cursor: 'pointer', whiteSpace: 'nowrap', opacity: loading ? 0.5 : 1 }}>
            {b.icon} {b.label}
          </button>
        ))}
      </div>
      <div style={{ flex: 1, overflow: 'auto', padding: 12, fontSize: '0.8rem', minHeight: 200 }}>
        {msgs.length === 0 && <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 20 }}>Нажмите кнопку для запроса к 13 агентам</div>}
        {msgs.map((m, i) => (
          <div key={i} style={{ marginBottom: 10, textAlign: m.role === 'user' ? 'right' : 'left' }}>
            <div style={{ display: 'inline-block', maxWidth: '90%', padding: '6px 12px', borderRadius: 12, background: m.role === 'user' ? 'var(--accent)' : 'var(--bg-card)', color: m.role === 'user' ? '#000' : 'var(--text-primary)', whiteSpace: 'pre-wrap', textAlign: 'left' }}>
              {m.content}
            </div>
          </div>
        ))}
        {loading && <div style={{ color: 'var(--accent)', fontSize: '0.75rem' }}>⏳ Думаю...</div>}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
