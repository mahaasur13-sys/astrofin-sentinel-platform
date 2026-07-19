import { useState, useRef, useEffect } from 'react';

interface ChatMessage {
  role: 'user' | 'ai';
  content: string;
}

interface AspectItem {
  planet1: string;
  planet2: string;
  type: string;
  icon: string;
  orb: number;
  score: number;
}

interface AstroInterpretation {
  verdict: 'favourable' | 'caution' | 'avoid';
  verdict_icon: string;
  verdict_text: string;
  composite_score: number;
  muhurta_score: number;
  nakshatra: string;
  nakshatra_grade: string;
  nakshatra_multiplier: number;
  choghadiya_current: { name: string; icon: string; quality: string; recommended: boolean };
  choghadiya_slots: Array<{ period: number; name: string; start: string; end: string; icon: string; quality: string }>;
  top_favourable: AspectItem[];
  top_unfavourable: AspectItem[];
}

const AstroMindChat: React.FC<{ isOpen: boolean; onToggle: () => void }> = ({ isOpen, onToggle }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'ai', content: '🧠 AstroMind online. Спроси о режиме, риске, сделке или нажми быстрый вопрос.' },
  ]);
  const [input, setInput] = useState('');
  const [astroData, setAstroData] = useState<AstroInterpretation | null>(null);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchAstroData();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchAstroData = async () => {
    try {
      const res = await fetch('/api/v1/astro/interpretation');
      const data = await res.json();
      setAstroData(data);
    } catch (e) {
      console.warn('Astro interpretation fetch failed:', e);
    }
  };

  const formatAspectVerdict = (d: AstroInterpretation): string => {
    const lines: string[] = [];
    lines.push(`**${d.verdict_icon} Вердикт: ${d.verdict === 'favourable' ? 'Благоприятно' : d.verdict === 'caution' ? 'Осторожно' : 'Избегать'}** (${d.composite_score}/100)`);
    lines.push('');
    lines.push(`**Muhurta Score:** ${d.muhurta_score}/100`);
    lines.push(`**Nakshatra:** ${d.nakshatra} (${d.nakshatra_grade}, ×${d.nakshatra_multiplier})`);
    lines.push(`**Choghadiya:** ${d.choghadiya_current.icon || ''} ${d.choghadiya_current.name} (${d.choghadiya_current.quality || '—'})`);
    lines.push('');
    lines.push('**Благоприятные аспекты:**');
    for (const a of d.top_favourable) {
      lines.push(`  ✅ ${a.icon} ${a.planet1} ${a.type} ${a.planet2} (+${a.score.toFixed(1)})`);
    }
    lines.push('');
    lines.push('**Неблагоприятные аспекты:**');
    for (const a of d.top_unfavourable) {
      lines.push(`  ⛔ ${a.icon} ${a.planet1} ${a.type} ${a.planet2} (${a.score.toFixed(1)})`);
    }
    lines.push('');
    lines.push(`🕐 Ближайшие окна: ${d.choghadiya_slots.filter(s => s.quality === 'auspicious' || s.quality === 'profitable').slice(0, 2).map(s => `${s.icon} ${s.name} ${s.start}-${s.end}`).join(', ') || 'нет'}`);
    lines.push('');
    lines.push(`> ${d.verdict_text}`);
    return lines.join('\n');
  };

  const getQuickReplies = (): string[] => {
    if (!astroData) return ['Загрузка данных...'];
    const verdict = astroData.verdict === 'favourable' ? '🟢 Удача' : astroData.verdict === 'avoid' ? '🔴 Риск' : '🟡 Нейтрально';
    const muhurta = `⭐ Muhurta: ${astroData.muhurta_score}/100`;
    const choghadiya = `🕐 ${astroData.choghadiya_current.icon} ${astroData.choghadiya_current.name}`;
    return [verdict, muhurta, '📊 Показать астро-факторы', choghadiya];
  };

  const handleQuickReply = (text: string) => {
    if (!astroData) return;
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setLoading(true);

    setTimeout(() => {
      let response: string;
      if (text === '📊 Показать астро-факторы') {
        response = formatAspectVerdict(astroData);
      } else if (text.includes('Muhurta')) {
        response = `**⭐ Muhurta Score: ${astroData.muhurta_score}/100**\n\n` +
          `Nakshatra: ${astroData.nakshatra} (${astroData.nakshatra_grade})\n` +
          `Choghadiya: ${astroData.choghadiya_current.name}\n\n` +
          `${astroData.muhurta_score >= 80 ? '✅ Отличное время для входа' : astroData.muhurta_score >= 50 ? '⚠️ Входить осторожно' : '🚫 Лучше подождать'}`;
      } else if (text.includes('Удача')) {
        const favCount = astroData.top_favourable.length;
        const unfavCount = astroData.top_unfavourable.length;
        response = `**${astroData.verdict_icon} ${astroData.verdict_text}**\n\n` +
          `Благоприятных аспектов: ${favCount}\n` +
          `Неблагоприятных: ${unfavCount}\n` +
          `Composite: ${astroData.composite_score}/100\n\n` +
          `${favCount > unfavCount ? '✅ Баланс в пользу благоприятных' : '⚠️ Дисбаланс — осторожнее'}`;
      } else {
        response = `**${astroData.choghadiya_current.icon} ${astroData.choghadiya_current.name}** (${astroData.choghadiya_current.quality || '—'})\n\n` +
          `Рекомендация: ${astroData.choghadiya_current.recommended ? '✅ Входить можно' : '⚠️ Лучше подождать'}\n\n` +
          `Ближайшие окна:\n` +
          astroData.choghadiya_slots.filter(s => s.recommended).slice(0, 3).map(s => `• ${s.icon} ${s.name} ${s.start}-${s.end}`).join('\n');
      }

      setMessages(prev => [...prev, { role: 'ai', content: response }]);
      setLoading(false);
    }, 500);
  };

  const handleSend = () => {
    if (!input.trim() || loading) return;
    const text = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setInput('');
    setLoading(true);

    fetch('/api/v1/agent/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agentId: 'astromind', prompt: text }),
    })
      .then(res => res.json())
      .then(data => {
        setMessages(prev => [...prev, { role: 'ai', content: data?.result || 'Нет ответа от агента' }]);
      })
      .catch(() => {
        if (astroData) {
          setMessages(prev => [...prev, { role: 'ai', content: formatAspectVerdict(astroData) }]);
        } else {
          setMessages(prev => [...prev, { role: 'ai', content: '⚠️ API недоступен. Попробуйте позже.' }]);
        }
      })
      .finally(() => setLoading(false));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) {
    return (
      <div
        onClick={onToggle}
        title="AstroMind Chat"
        style={{
          position: 'fixed', bottom: 24, right: 24, zIndex: 9999,
          width: 52, height: 52, borderRadius: '50%',
          background: 'var(--accent)', color: '#000',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer', boxShadow: '0 0 20px var(--accent-glow)',
          fontSize: '1.5rem', fontWeight: 700, userSelect: 'none',
        }}
      >
        🧠
      </div>
    );
  }

  return (
    <div style={{
      position: 'fixed', bottom: 24, right: 24, zIndex: 9999,
      width: 380, height: 520, borderRadius: 14,
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column',
      boxShadow: '0 0 30px rgba(0,0,0,0.5)',
    }}>
      <div onClick={onToggle} style={{
        padding: '12px 16px', borderBottom: '1px solid var(--border)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        cursor: 'pointer', fontSize: '0.9rem', fontWeight: 600,
        color: 'var(--accent)',
      }}>
        <span>🧠 AstroMind</span>
        <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
          {astroData ? `${astroData.verdict_icon} ${astroData.composite_score}/100` : ''}
        </span>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 12 }}>
        {messages.map((m, i) => (
          <div key={i} style={{
            marginBottom: 10,
            textAlign: m.role === 'user' ? 'right' : 'left',
          }}>
            <div style={{
              display: 'inline-block', maxWidth: '85%', padding: '8px 12px',
              borderRadius: 10,
              background: m.role === 'user' ? 'var(--accent)' : 'var(--bg-secondary)',
              color: m.role === 'user' ? '#000' : 'var(--text)',
              fontSize: '0.82rem', lineHeight: 1.5,
              whiteSpace: 'pre-wrap', textAlign: 'left',
            }}>
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ textAlign: 'left', marginBottom: 10 }}>
            <span style={{ color: 'var(--accent)', fontSize: '0.8rem' }}>⏳ Думаю...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div style={{
        padding: '8px 12px', borderTop: '1px solid var(--border)',
        display: 'flex', gap: 6, flexWrap: 'wrap',
      }}>
        {getQuickReplies().map((qr, i) => (
          <button
            key={i}
            onClick={() => handleQuickReply(qr)}
            disabled={loading}
            style={{
              fontSize: '0.7rem', padding: '4px 10px', borderRadius: 14,
              background: 'var(--bg-secondary)', color: 'var(--text-secondary)',
              border: '1px solid var(--border)', cursor: loading ? 'default' : 'pointer',
              opacity: loading ? 0.5 : 1,
            }}
          >
            {qr}
          </button>
        ))}
      </div>

      <div style={{
        padding: '8px 12px', borderTop: '1px solid var(--border)',
        display: 'flex', gap: 8,
      }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Спроси о сделке..."
          disabled={loading}
          style={{
            flex: 1, padding: '8px 12px', borderRadius: 8,
            background: 'var(--bg-secondary)', color: 'var(--text)',
            border: '1px solid var(--border)', fontSize: '0.82rem',
            outline: 'none',
          }}
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          style={{
            padding: '8px 16px', borderRadius: 8,
            background: loading || !input.trim() ? 'var(--bg-secondary)' : 'var(--accent)',
            color: loading || !input.trim() ? 'var(--text-secondary)' : '#000',
            border: 'none', cursor: loading || !input.trim() ? 'default' : 'pointer',
            fontSize: '0.82rem', fontWeight: 600,
          }}
        >
          →
        </button>
      </div>
    </div>
  );
};

export default AstroMindChat;
