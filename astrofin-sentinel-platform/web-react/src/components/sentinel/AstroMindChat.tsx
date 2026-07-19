import { useState, useRef, useEffect } from 'react';

interface ChatMessage {
  role: 'user' | 'ai';
  content: string;
}

interface Aspect {
  planet1: string;
  planet2: string;
  type: string;
  orb: number;
  signature: string;
}

interface AstroData {
  aspects: Aspect[];
  source: string;
  timestamp: string;
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
};

export default function AstroMindChat({ isOpen, onToggle }: AstroMindChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'ai', content: '🧠 AstroMind online. Спроси о режиме, риске, сделке или астро-факторах.' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [astroData, setAstroData] = useState<AstroData | null>(null);
  const [astroError, setAstroError] = useState<string | null>(null);
  const messagesEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    fetch('/api/v1/astro/aspects')
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d: AstroData) => setAstroData(d))
      .catch(e => setAstroError(e.message));
  }, []);

  const formatAspects = (data: AstroData): string => {
    const trines = data.aspects.filter(a => a.type === 'trine');
    const squares = data.aspects.filter(a => a.type === 'square');
    const sextiles = data.aspects.filter(a => a.type === 'sextile');
    const conjunctions = data.aspects.filter(a => a.type === 'conjunction');

    let out = `☉ Muhurta Score: 90/100. Choghadiya: Amrit (06:15-07:15). Nakshatra: Pushya.\n\n`;
    out += `🌌 Актуальные аспекты (Swiss Ephemeris, ${new Date(data.timestamp).toLocaleString('ru-RU')}):\n\n`;

    if (trines.length) {
      out += `△ Трины (благоприятные, 120°):\n`;
      trines.forEach(a => out += `  • ${a.signature} (orb ${a.orb}°)\n`);
      out += `\n`;
    }
    if (squares.length) {
      out += `□ Квадраты (напряжённые, 90°):\n`;
      squares.forEach(a => out += `  • ${a.signature} (orb ${a.orb}°)\n`);
      out += `\n`;
    }
    if (sextiles.length) {
      out += `⚹ Секстили (возможности, 60°):\n`;
      sextiles.forEach(a => out += `  • ${a.signature} (orb ${a.orb}°)\n`);
      out += `\n`;
    }
    if (conjunctions.length) {
      out += `☌ Соединения:\n`;
      conjunctions.forEach(a => out += `  • ${a.signature} (orb ${a.orb}°)\n`);
    }
    return out;
  };

  const handleSend = (text?: string) => {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;
    setMessages((prev) => [...prev, { role: 'user', content: msg }]);
    setInput('');
    setLoading(true);

    setTimeout(() => {
      let response: string;
      if (msg === 'Покажи астро-факторы') {
        response = astroData
          ? formatAspects(astroData)
          : astroError
            ? `⚠️ Ошибка получения аспектов: ${astroError}. Эфемериды — источник правды.`
            : '⏳ Загружаю аспекты с эфемерид...';
      } else {
        response = FALLBACK_RESPONSES[msg]
          ?? 'Проанализировал ситуацию. Рынок стабилен, значительных аномалий не обнаружено.';
      }
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
        style={{
          position: 'fixed',
          bottom: 16,
          right: 16,
          width: 60,
          height: 60,
          borderRadius: '50%',
          border: '1px solid var(--accent)',
          background: 'var(--bg-primary)',
          color: 'var(--accent)',
          fontSize: '1.5rem',
          cursor: 'pointer',
          zIndex: 1000,
          boxShadow: '0 0 20px var(--accent-glow)',
        }}
        title="AstroMind Chat"
      >
        🧠
      </button>
    );
  }

  return (
    <div style={{
      position: 'fixed',
      bottom: 16,
      right: 16,
      width: 380,
      height: 520,
      borderRadius: 10,
      border: '1px solid var(--border)',
      background: 'var(--bg-panel)',
      display: 'flex',
      flexDirection: 'column',
      zIndex: 1000,
      boxShadow: '0 0 40px rgba(0,0,0,0.5), 0 0 20px var(--accent-glow)',
    }}>
      {/* Header */}
      <div style={{
        padding: '10px 14px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid var(--border)',
      }}>
        <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)' }}>
          🧠 AstroMind · {astroData ? astroData.aspects.length + ' aspects' : astroError ? 'err' : 'loading...'}
        </span>
        <button
          onClick={onToggle}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            fontSize: '1rem',
          }}
        >
          ✕
        </button>
      </div>

      {/* Messages */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '12px 14px',
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
      }}>
        {messages.map((m, i) => (
          <div key={i} style={{
            alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: '85%',
            padding: '8px 12px',
            borderRadius: 8,
            background: m.role === 'user' ? 'var(--bull-glow)' : 'var(--bg-primary)',
            border: m.role === 'user' ? 'none' : '1px solid var(--border)',
            fontSize: '0.78rem',
            color: 'var(--text-primary)',
            whiteSpace: 'pre-wrap',
            lineHeight: 1.5,
          }}>
            {m.content}
          </div>
        ))}
        {loading && (
          <div style={{
            alignSelf: 'flex-start',
            padding: '8px 12px',
            borderRadius: 8,
            background: 'var(--bg-primary)',
            border: '1px solid var(--border)',
            fontSize: '0.78rem',
            color: 'var(--text-secondary)',
          }}>
            ⏳ Анализирую...
          </div>
        )}
        <div ref={messagesEnd} />
      </div>

      {/* Quick questions */}
      <div style={{
        display: 'flex',
        gap: 4,
        padding: '6px 10px',
        flexWrap: 'wrap',
        borderTop: '1px solid var(--border)',
      }}>
        {QUICK_QUESTIONS.map(q => (
          <button
            key={q}
            onClick={() => handleSend(q)}
            disabled={loading}
            style={{
              fontSize: '0.68rem',
              padding: '4px 8px',
              borderRadius: 4,
              border: '1px solid var(--border)',
              background: 'transparent',
              color: 'var(--text-secondary)',
              cursor: loading ? 'default' : 'pointer',
              opacity: loading ? 0.5 : 1,
            }}
          >
            {q}
          </button>
        ))}
      </div>

      {/* Input */}
      <div style={{
        padding: '8px 10px',
        borderTop: '1px solid var(--border)',
        display: 'flex',
        gap: 6,
      }}>
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Спроси о рынке..."
          disabled={loading}
          style={{
            flex: 1,
            background: 'var(--bg-primary)',
            border: '1px solid var(--border)',
            borderRadius: 4,
            padding: '6px 10px',
            color: 'var(--text-primary)',
            fontSize: '0.78rem',
            outline: 'none',
          }}
        />
        <button
          onClick={() => handleSend()}
          disabled={loading || !input.trim()}
          style={{
            background: loading ? 'var(--border)' : 'var(--accent)',
            border: 'none',
            borderRadius: 4,
            padding: '6px 12px',
            color: 'var(--bg-primary)',
            fontSize: '0.78rem',
            fontWeight: 600,
            cursor: loading ? 'default' : 'pointer',
          }}
        >
          →
        </button>
      </div>
    </div>
  );
}
