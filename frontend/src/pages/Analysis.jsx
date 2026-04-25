import { useEffect, useState } from 'react'
import api from '../api/client'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, RadialBarChart, RadialBar, Legend } from 'recharts'

function fmt(v) { return 'R$ ' + Number(v||0).toLocaleString('pt-BR', { minimumFractionDigits: 2 }) }

export default function Analysis() {
  const [data, setData]     = useState(null)
  const [reco, setReco]     = useState('')
  const [recoLoading, setRecoLoading] = useState(false)
  const [chat, setChat]     = useState('')
  const [chatAns, setChatAns] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/api/analysis').then(r => { setData(r.data); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  const loadReco = () => {
    setRecoLoading(true)
    api.get('/api/analysis/recommendations').then(r => { setReco(r.data.text); setRecoLoading(false) }).catch(() => setRecoLoading(false))
  }

  const sendChat = async () => {
    if (!chat.trim()) return
    setChatLoading(true)
    const r = await api.post('/api/chat', { question: chat }).catch(() => ({ data: { answer: 'Erro ao processar.' } }))
    setChatAns(r.data.answer)
    setChatLoading(false)
  }

  if (loading) return <div className="loading"><div className="spinner" /><span>Carregando anÃ¡lise...</span></div>
  if (!data) return <div className="empty"><div className="icon">âš ï¸</div><p>Erro ao carregar</p></div>

  const income = data.total_income || 0
  const gaugeData = [
    { name: 'Essencial', value: income ? Math.min(100, (data.priority_totals?.Essencial||0)/income*100) : 0, fill: '#10b981', limit: data.budget_limits?.essential_pct || 50 },
    { name: 'Importante', value: income ? Math.min(100, (data.priority_totals?.Importante||0)/income*100) : 0, fill: '#f59e0b', limit: data.budget_limits?.important_pct || 30 },
    { name: 'Opcional', value: income ? Math.min(100, (data.priority_totals?.Opcional||0)/income*100) : 0, fill: '#ef4444', limit: data.budget_limits?.optional_pct || 20 },
  ]

  return (
    <div>
      <div className="page-header">
        <h1>ðŸ“Š AnÃ¡lise Financeira</h1>
        <p>EstatÃ­sticas detalhadas e recomendaÃ§Ãµes inteligentes</p>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-item">
          <div className="stat-label">ðŸ’¼ Renda Total</div>
          <div className="stat-value text-accent">{fmt(income)}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">ðŸ’¸ Total Gastos</div>
          <div className="stat-value text-amber">{fmt(data.total_expenses)}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">ðŸ’° Saldo</div>
          <div className={`stat-value ${data.balance >= 0 ? 'text-accent' : 'text-red'}`}>{fmt(data.balance)}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">ðŸŽ¯ LanÃ§amentos</div>
          <div className="stat-value">{data.expense_count || 0}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">ðŸ“ˆ Para Investir</div>
          <div className="stat-value text-accent">{fmt(data.investment_suggested)}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">ðŸ¦ % Investimentos</div>
          <div className="stat-value">{data.investment_pct || 20}%</div>
        </div>
      </div>

      {/* 50/30/20 Gauge */}
      <div className="charts-grid">
        <div className="chart-card">
          <div className="chart-title">ðŸŽ¯ Regra OrÃ§amentÃ¡ria â€” Real vs. Recomendado</div>
          <div style={{ marginTop: 8 }}>
            {gaugeData.map(g => (
              <div key={g.name} style={{ marginBottom: 14 }}>
                <div className="flex-between" style={{ marginBottom: 4 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: g.fill }}>{g.name}</span>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{g.value.toFixed(1)}% / {g.limit}% limite</span>
                </div>
                <div className="progress-track" style={{ height: 8 }}>
                  <div className="progress-segment" style={{ width: Math.min(100, g.value / g.limit * 100) + '%', background: g.value > g.limit ? '#ef4444' : g.fill }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="chart-card">
          <div className="chart-title">ðŸ“‹ Alertas Ativos ({data.alerts?.length || 0})</div>
          <div style={{ maxHeight: 240, overflowY: 'auto' }}>
            {data.alerts?.length > 0
              ? data.alerts.map((a, i) => (
                <div key={i} className={`alert alert-${a.level === 'danger' ? 'danger' : a.level === 'warning' ? 'warning' : 'info'}`}>
                  <div>
                    <div className="alert-title">{a.icon} {a.title}</div>
                    <div className="alert-message">{a.message}</div>
                    <div className="alert-suggestion">ðŸ’¡ {a.suggestion}</div>
                  </div>
                </div>
              ))
              : <div className="empty" style={{ padding: 24 }}><p>âœ… Nenhum alerta! Suas finanÃ§as estÃ£o saudÃ¡veis.</p></div>
            }
          </div>
        </div>
      </div>

      {/* AI Recommendations */}
      <div className="ai-box">
        <div className="ai-box-header">
          <span style={{ fontSize: 22 }}>ðŸ¤–</span>
          <h3>RecomendaÃ§Ãµes da IA (Gemini)</h3>
          <button className="btn btn-secondary btn-sm" style={{ marginLeft: 'auto' }} onClick={loadReco} disabled={recoLoading}>
            {recoLoading ? 'â³ Analisando...' : 'âœ¨ Gerar RecomendaÃ§Ãµes'}
          </button>
        </div>
        {reco
          ? <div className="ai-text">{reco}</div>
          : <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>Clique em "Gerar RecomendaÃ§Ãµes" para receber anÃ¡lise personalizada baseada nos seus dados reais.</div>
        }
      </div>

      {/* Chat */}
      <div className="chart-card">
        <div className="chart-title">ðŸ’¬ Pergunte sobre suas finanÃ§as</div>
        <div style={{ display: 'flex', gap: 10, marginBottom: 12 }}>
          <input className="form-control" style={{ flex: 1 }}
            value={chat} onChange={e => setChat(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && sendChat()}
            placeholder="Ex: Quanto gastei em alimentaÃ§Ã£o? O que posso cortar?" />
          <button className="btn btn-primary" onClick={sendChat} disabled={chatLoading}>
            {chatLoading ? 'â³' : 'Perguntar'}
          </button>
        </div>
        {chatAns && (
          <div style={{ background: 'var(--bg-elevated)', borderRadius: 8, padding: '14px 16px', fontSize: 13, color: 'var(--text-subtle)', lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
            {chatAns}
          </div>
        )}
      </div>
    </div>
  )
}

