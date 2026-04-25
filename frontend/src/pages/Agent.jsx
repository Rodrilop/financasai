import { useState, useRef, useEffect } from 'react';
import api from '../api/client';

export default function Agent() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Olá! Sou seu Assistente Financeiro IA. 🤖\nPosso analisar seus gastos ou registrar novas despesas para você. Exemplo: "Gastei R$ 45 de Uber hoje" ou "Adicione uma despesa de R$ 120 no supermercado ontem". Como posso ajudar?'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (presetText = null) => {
    const text = presetText || input;
    if (!text.trim()) return;

    const newMsgs = [...messages, { role: 'user', content: text }];
    setMessages(newMsgs);
    setInput('');
    setLoading(true);

    try {
      const res = await api.post('/api/chat', { question: text });
      setMessages([...newMsgs, { role: 'assistant', content: res.data.answer }]);
    } catch (err) {
      setMessages([...newMsgs, { role: 'assistant', content: 'Desculpe, ocorreu um erro ao processar sua solicitação.' }]);
    } finally {
      setLoading(false);
    }
  };

  const suggestions = [
    "Gastei R$ 50 no Ifood hoje",
    "Fiz uma compra de R$ 120 no supermercado ontem",
    "Como posso economizar?",
    "Resuma meus gastos deste mês"
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 60px)', maxWidth: '800px', margin: '0 auto' }}>
      <div className="page-header" style={{ marginBottom: '16px' }}>
        <h1>🤖 Assistente IA</h1>
        <p>Converse com a inteligência artificial para gerenciar suas finanças.</p>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', background: 'var(--bg-elevated)', borderRadius: '12px', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', border: '1px solid var(--border)' }}>
        {messages.map((m, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{
              maxWidth: '80%',
              padding: '12px 16px',
              borderRadius: '16px',
              borderBottomRightRadius: m.role === 'user' ? 0 : '16px',
              borderBottomLeftRadius: m.role === 'assistant' ? 0 : '16px',
              background: m.role === 'user' ? 'var(--accent)' : 'var(--bg-base)',
              color: m.role === 'user' ? '#fff' : 'var(--text)',
              border: m.role === 'assistant' ? '1px solid var(--border)' : 'none',
              lineHeight: 1.5,
              whiteSpace: 'pre-wrap'
            }}>
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{ padding: '12px 16px', borderRadius: '16px', background: 'var(--bg-base)', border: '1px solid var(--border)' }}>
              <div className="spinner" style={{ width: '16px', height: '16px', borderTopColor: 'var(--accent)' }} />
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div style={{ marginTop: '16px' }}>
        <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '8px', marginBottom: '8px' }}>
          {suggestions.map((s, i) => (
            <button key={i} className="btn btn-secondary btn-sm" style={{ whiteSpace: 'nowrap', borderRadius: '20px' }} onClick={() => sendMessage(s)}>
              {s}
            </button>
          ))}
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <input 
            className="form-control" 
            style={{ flex: 1, borderRadius: '24px', padding: '0 20px' }}
            value={input} 
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && sendMessage()}
            placeholder="Digite sua mensagem (ex: Gastei R$ 30 na padaria)..." 
            disabled={loading}
          />
          <button className="btn btn-primary" style={{ borderRadius: '24px', padding: '0 24px' }} onClick={() => sendMessage()} disabled={loading || !input.trim()}>
            Enviar
          </button>
        </div>
      </div>
    </div>
  );
}
