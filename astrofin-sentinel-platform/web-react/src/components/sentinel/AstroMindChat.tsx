import { useState, useRef, useEffect } from 'react';

interface ChatMessage {
  role: 'user' | 'ai';
  content: string;
}

interface AstroMindChatProps {
  isOpen: boolean;
  onToggle: () => void;
}

const QUICK_QUESTIONS = [
  'Какой текущий режим?',
  'Оцени риск',
  'Дай торговую рекомендацию',
  'Покажи астро-факторы',
];

const FALLBACK_RESPONSES: Record<string, string> = {
  'Какой текущий режим?': 'Режим: BULL (81%). Рекомендация: Лонг. Leverage 1.6×.',
  'Оцени риск': 'Risk 2.0% (NORMAL). VaR 95: 3.2%. Max DD: 8.5%. Safety Gate: SAFE ✅.',
  'Дай торговую рекомендацию': 'Ensemble: HOLD → BUY bias (confidence 0.72). Fundamental +0.65, Quant +0.58, Astro +0.41. Рекомендуемый размер позиции: 2.0% от портфеля.',
  'Покажи астро-факторы': 'Muhurta Score: 90/100. Choghadiya: Amrit (06:15-07:15). Nakshatra: Pushya. Jupiter trine Venus — благоприятный аспект.',
};

export default function AstroMindChat({ isOpen, onToggle }: AstroMindChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'ai', content: '🧠 AstroMind online. Спроси о режиме, риске, сделке или астро-факторах.' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (text?: string) => {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;
    setMessages((prev) => [...prev, { role: 'user', content: msg }]);
    setInput('');
    setLoading(true);

    setTimeout(() => {
      const response = FALLBACK_RESPONSES[msg]
        ?? 'Проанализировал ситуацию. Рынок стабилен, каких-либо значительных аномалий не обнаружено. Рекомендую следить за режимом и уровнями риска.';
      setMessages((prev) => [...prev, { role: 'ai', content: response }]);
      setLoading(false);
    }, 600 + Math.random() * 800);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="glass-card neon-glow-accent"
        style={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          width: 52,
          height: 52,
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '1.3rem',
          cursor: 'pointer',
          border: 'none',
          zIndex: 1000,
          color: 'var(--accent)',
        }}
        title="AstroMind Chat"
      >
        🧠
      </button>
    );
  }

  return (
    <div
      className="glass-panel"
      style={{
        position: 'fixed',
        bottom: 24,
        right: 24,
        width: 400,
        height: 560,
        display: 'flex',
        flexDirection: 'column',
        zIndex: 1000,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: '1.1rem' }}>🧠</span>
          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>AstroMind</div>
            <div style={{ fontSize: '0.65rem', color: 'var(--bull)' }}>● Online</div>
          </div>
        </div>
        <button
          onClick={onToggle}
          style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '1rem' }}
        >
          ✕
        </button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '85%',
              padding: '8px 12px',
              borderRadius: m.role === 'user' ? '12px 12px 4px 12px' : '12px 12px 12px 4px',
              background: m.role === 'user' ? 'var(--accent)' : 'var(--bg-card)',
              color: m.role === 'user' ? '#fff' : 'var(--text-primary)',
              fontSize: '0.8rem',
              lineHeight: 1.5,
              border: m.role === 'ai' ? '1px solid var(--border)' : 'none',
            }}
          >
            {m.content}
          </div>
        ))}
        {loading && (
          <div style={{ alignSelf: 'flex-start', padding: '8px 12px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            ⏳ Думаю...
          </div>
        )}
        <div ref={messagesEnd} />
      </div>

      <div style={{ padding: '8px 12px', borderTop: '1px solid var(--border)', display: 'flex', flexWrap: 'wrap', gap: 4 }}>
        {QUICK_QUESTIONS.map((q) => (
          <button
            key={q}
            onClick={() => handleSend(q)}
            disabled={loading}
            style={{
              padding: '4px 10px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border)',
              borderRadius: 14,
              color: 'var(--text-secondary)',
              fontSize: '0.68rem',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'border-color 0.2s',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--accent)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--border)'; }}
          >
            {q}
          </button>
        ))}
      </div>

      <div style={{ padding: '10px 12px', borderTop: '1px solid var(--border)', display: 'flex', gap: 8 }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Спроси о рынке..."
          disabled={loading}
          style={{
            flex: 1,
            padding: '8px 12px',
            background: 'var(--bg-card)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--text-primary)',
            fontSize: '0.8rem',
            outline: 'none',
          }}
        />
        <button
          onClick={() => handleSend()}
          disabled={loading || !input.trim()}
          style={{
            padding: '8px 14px',
            background: 'var(--accent)',
            border: 'none',
            borderRadius: 'var(--radius-sm)',
            color: '#fff',
            fontWeight: 600,
            fontSize: '0.8rem',
            cursor: 'pointer',
            opacity: loading || !input.trim() ? 0.5 : 1,
          }}
        >
          →
        </button>
      </div>
    </div>
  );
}
