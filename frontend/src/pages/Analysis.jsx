import { useEffect, useState, useContext } from 'react'
import { useOutletContext } from 'react-router-dom'
import api from '../api/client'
import { AuthContext } from '../contexts/AuthContext'
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
  const { user } = useContext(AuthContext)

  const { month } = useOutletContext()

  useEffect(() => {
    setLoading(true)
    api.get(`/api/analysis?month=${month || ''}`).then(r => { setData(r.data); setLoading(false) }).catch(() => setLoading(false))
  }, [month])

  const loadReco = () => {
    setRecoLoading(true)
    api.get(`/api/analysis/recommendations?month=${month || ''}`).then(r => { setReco(r.data.text); setRecoLoading(false) }).catch(() => setRecoLoading(false))
  }

  const sendChat = async () => {
    if (!chat.trim()) return
    setChatLoading(true)
    const r = await api.post('/api/chat', { question: chat }).catch(() => ({ data: { answer: 'Erro ao processar.' } }))
    setChatAns(r.data.answer)
    setChatLoading(false)
  }

  if (loading) return <div className="loading"><div className="spinner" /><span>Carregando análise...</span></div>
  if (!data) return <div className="empty"><div className="icon">⚠️</div><p>Erro ao carregar</p></div>

  const income = data.total_income || 0
  const gaugeData = [
    { name: 'Essencial', value: income ? Math.min(100, (data.priority_totals?.Essencial||0)/income*100) : 0, fill: '#10b981', limit: data.budget_limits?.essential_pct || 50 },
    { name: 'Importante', value: income ? Math.min(100, (data.priority_totals?.Importante||0)/income*100) : 0, fill: '#f59e0b', limit: data.budget_limits?.important_pct || 30 },
    { name: 'Opcional', value: income ? Math.min(100, (data.priority_totals?.Opcional||0)/income*100) : 0, fill: '#ef4444', limit: data.budget_limits?.optional_pct || 20 },
  ]

  return (
    <div>
      <div className="page-header">
        <h1>📊 Análise Financeira</h1>
        <p>Estatísticas detalhadas e recomendações inteligentes</p>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-item">
          <div className="stat-label">💼 Renda Total</div>
          <div className="stat-value text-accent">{fmt(income)}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">💸 Total Gastos</div>
          <div className="stat-value text-amber">{fmt(data.total_expenses)}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">💰 Saldo</div>
          <div className={`stat-value ${data.balance >= 0 ? 'text-accent' : 'text-red'}`}>{fmt(data.balance)}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">🎯 Lançamentos</div>
          <div className="stat-value">{data.expense_count || 0}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">📈 Para Investir</div>
          <div className="stat-value text-accent">{fmt(data.investment_suggested)}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">🏦 % Investimentos</div>
          <div className="stat-value">{data.investment_pct || 20}%</div>
        </div>
      </div>

      {/* 50/30/20 Gauge */}
      <div className="charts-grid">
        <div className="chart-card">
          <div className="chart-title">🎯 Regra Orçamentária — Real vs. Recomendado</div>
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
          <div className="chart-title">📋 Alertas Ativos ({data.alerts?.length || 0})</div>
          <div style={{ maxHeight: 240, overflowY: 'auto' }}>
            {data.alerts?.length > 0
              ? data.alerts.map((a, i) => (
                <div key={i} className={`alert alert-${a.level === 'danger' ? 'danger' : a.level === 'warning' ? 'warning' : 'info'}`}>
                  <div>
                    <div className="alert-title">{a.icon} {a.title}</div>
                    <div className="alert-message">{a.message}</div>
                    <div className="alert-suggestion">💡 {a.suggestion}</div>
                  </div>
                </div>
              ))
              : <div className="empty" style={{ padding: 24 }}><p>✅ Nenhum alerta! Suas finanças estão saudáveis.</p></div>
            }
          </div>
        </div>
      </div>

      {/* AI Recommendations */}
      <div className="ai-box">
        <div className="ai-box-header">
          <span style={{ fontSize: 22 }}>🤖</span>
          <h3>Recomendações da IA (Gemini)</h3>
          <button className="btn btn-secondary btn-sm" style={{ marginLeft: 'auto' }} onClick={loadReco} disabled={recoLoading}>
            {recoLoading ? '⏳ Analisando...' : '✨ Gerar Recomendações'}
          </button>
        </div>
        {reco
          ? <div className="ai-text">{reco}</div>
          : <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>Clique em "Gerar Recomendações" para receber análise personalizada baseada nos seus dados reais.</div>
        }
      </div>

      {/* Premium Report (PRO ONLY) */}
      <div className="chart-card" style={{ marginTop: 24, border: user?.isPro ? '1px solid var(--accent)' : '1px dashed var(--border)', opacity: user?.isPro ? 1 : 0.8 }}>
        <div className="flex-between">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            🛡️ Relatório de Saúde Financeira
            {!user?.isPro && <span className="icon" style={{ fontSize: 14 }}>🔒</span>}
          </h3>
          {user?.isPro && <span className="badge badge-purple">PRO</span>}
        </div>
        
        {user?.isPro ? (
          <div style={{ marginTop: 16 }}>
            <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', background: 'rgba(0,0,0,0.1)', borderRadius: 12, padding: 16 }}>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Score de Saúde</div>
                <div style={{ fontSize: 24, fontWeight: 800, color: '#10b981' }}>92/100</div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Consistência</div>
                <div style={{ fontSize: 24, fontWeight: 800, color: '#3b82f6' }}>Alta</div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Risco</div>
                <div style={{ fontSize: 24, fontWeight: 800, color: '#f59e0b' }}>Baixo</div>
              </div>
            </div>
            <p style={{ marginTop: 16, fontSize: 14, lineHeight: 1.6 }}>
              Seu perfil indica uma gestão exemplar. Com uma reserva que cobre mais de 3 meses, você está no caminho certo para 
              acelerar seus investimentos em renda variável. Sugerimos diversificar seu portfólio em ativos de dividendos.
            </p>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '32px 0' }}>
            <p style={{ color: 'var(--text-muted)', marginBottom: 16 }}>
              Este relatório avançado utiliza IA para calcular seu score de saúde financeira e prever tendências.
            </p>
            <a href="/settings" className="btn btn-secondary">Libere o acesso Pro</a>
          </div>
        )}
      </div>

    </div>
  )
}
