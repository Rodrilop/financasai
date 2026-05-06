import { useEffect, useState } from 'react'
import api from '../api/client'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { SkeletonChart, SkeletonTable } from '../components/Skeletons'
import EmptyState from '../components/EmptyState'

function fmt(v) { return 'R$ ' + Number(v||0).toLocaleString('pt-BR', { minimumFractionDigits: 2 }) }

const PROFILES = [
  { key: 'conservador', icon: '🟢', name: 'Conservador', desc: 'Segurança e renda estável' },
  { key: 'moderado',    icon: '🟡', name: 'Moderado',    desc: 'Equilíbrio crescimento/risco' },
  { key: 'agressivo',   icon: '🔴', name: 'Agressivo',   desc: 'Crescimento patrimonial' },
]

const SIG = { buy: { label: '🟢 Compra', cls: 'signal-buy' }, neutral: { label: '🟡 Neutro', cls: 'signal-neutral' }, wait: { label: '🔴 Aguardar', cls: 'signal-wait' } }

export default function Investments() {
  const [invData, setInvData]   = useState(null)
  const [market, setMarket]     = useState(null)
  const [portfolio, setPortfolio] = useState(null)
  const [loadInv, setLoadInv]   = useState(true)
  const [loadMkt, setLoadMkt]   = useState(true)
  const [loadPort, setLoadPort] = useState(true)
  const [activeTab, setActiveTab] = useState('acoes')
  const [profile, setProfile]   = useState('moderado')
  const [form, setForm] = useState({ ticker: '', quantity: '', average_price: '' })

  useEffect(() => {
    api.get('/api/investments').then(r => { setInvData(r.data); setProfile(r.data.profile?.toLowerCase() === 'conservador' ? 'conservador' : r.data.profile?.toLowerCase() === 'agressivo' ? 'agressivo' : 'moderado'); setLoadInv(false) }).catch(() => setLoadInv(false))
    api.get('/api/market').then(r => { setMarket(r.data); setLoadMkt(false) }).catch(() => setLoadMkt(false))
    api.get('/api/portfolio').then(r => { setPortfolio(r.data); setLoadPort(false) }).catch(() => setLoadPort(false))
  }, [])

  const changeProfile = async (p) => {
    setProfile(p)
    const s = await api.get('/api/settings').catch(() => ({ data: {} }))
    await api.put('/api/settings', { ...s.data, investor_profile: p }).catch(() => {})
    const r = await api.get('/api/investments').catch(() => ({ data: invData }))
    setInvData(r.data)
  }

  const addPortfolioItem = async (e) => {
    e.preventDefault()
    if (!form.ticker || !form.quantity || !form.average_price) return
    setLoadPort(true)
    await api.post('/api/portfolio', form).catch(() => {})
    setForm({ ticker: '', quantity: '', average_price: '' })
    api.get('/api/portfolio').then(r => { setPortfolio(r.data); setLoadPort(false) }).catch(() => setLoadPort(false))
  }

  const deletePortfolioItem = async (id) => {
    setLoadPort(true)
    await api.delete(`/api/portfolio/${id}`).catch(() => {})
    api.get('/api/portfolio').then(r => { setPortfolio(r.data); setLoadPort(false) }).catch(() => setLoadPort(false))
  }

  const emergencyPct = invData?.emergency_goal > 0
    ? Math.min(100, ((invData.balance || 0) / invData.emergency_goal) * 100)
    : 0

  return (
    <div>
      <div className="page-header">
        <h1>🌱 Investimentos</h1>
        <p>Plano de alocação personalizado e acompanhamento de mercado B3</p>
      </div>

      {/* Profile Selector */}
      <div className="chart-card" style={{ marginBottom: 16 }}>
        <div className="chart-title">Seu Perfil de Investidor</div>
        <div className="profile-grid">
          {PROFILES.map(p => (
            <div key={p.key} className={`profile-btn${profile === p.key ? ' active' : ''}`} onClick={() => changeProfile(p.key)}>
              <span className="icon">{p.icon}</span>
              <div className="name">{p.name}</div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>{p.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Allocation + Pie */}
      <div className="charts-grid" style={{ marginBottom: 16 }}>
        <div className="chart-card">
          <div className="chart-title">📐 Alocação Sugerida</div>
          {loadInv ? <SkeletonChart height={180} /> : invData ? (
            <>
              <div style={{ marginBottom: 12, fontSize: 13, color: 'var(--text-muted)' }}>
                💰 Valor disponível para investir: <strong style={{ color: 'var(--accent)' }}>{fmt(invData.investment_suggested)}</strong>
              </div>
              <div className="alloc-grid">
                {invData.breakdown?.map(b => (
                  <div key={b.name} className="alloc-item">
                    <div className="alloc-dot" style={{ background: b.color }} />
                    <div>
                      <div className="alloc-name">{b.name}</div>
                    </div>
                    <div className="alloc-values">
                      <div className="alloc-pct" style={{ color: b.color }}>{b.pct}%</div>
                      <div className="alloc-amount">{fmt(b.value)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : null}
        </div>

        <div className="chart-card">
          <div className="chart-title">🍕 Gráfico de Alocação</div>
          {invData?.breakdown ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={invData.breakdown} cx="50%" cy="50%" outerRadius={80} dataKey="pct" label={({ name, pct }) => `${name} ${pct}%`} labelLine={false} fontSize={10}>
                  {invData.breakdown.map((b, i) => <Cell key={i} fill={b.color} />)}
                </Pie>
                <Tooltip formatter={(v) => v + '%'} contentStyle={{ background: '#0f1829', border: '1px solid #1e3050', borderRadius: 8 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : <SkeletonChart height={220} />}
        </div>
      </div>

      {/* Emergency Reserve */}
      <div className="chart-card" style={{ marginBottom: 16 }}>
        <div className="emergency-bar">
          <div className="emergency-header">
            <h4>🏦 Reserva de Emergência</h4>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Meta: {fmt(invData?.emergency_goal || 0)} • Recomendação: Tesouro Selic ou CDB liquidez diária
            </span>
          </div>
          <div className="progress-thin">
            <div className="progress-fill" style={{ width: emergencyPct + '%' }} />
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>{emergencyPct.toFixed(0)}% da meta atingida</div>
        </div>
      </div>

      {/* Minha Carteira Real */}
      <div className="chart-card" style={{ marginBottom: 16 }}>
        <div className="chart-title">💼 Minha Carteira (Tempo Real B3)</div>
        
        {loadPort ? <SkeletonTable rows={3} /> : portfolio && (
          <div>
            <div style={{ display: 'flex', gap: 24, marginBottom: 16, background: 'var(--bg-base)', padding: 16, borderRadius: 8 }}>
                <div>Total Investido<br/><strong style={{ fontSize: 18 }}>{fmt(portfolio.total_invested)}</strong></div>
                <div>Saldo Atual<br/><strong style={{ fontSize: 18 }}>{fmt(portfolio.total_equity)}</strong></div>
                <div style={{ color: portfolio.total_profit >= 0 ? '#10b981' : '#ef4444' }}>
                   Lucro / Prejuízo<br/>
                   <strong style={{ fontSize: 18 }}>{fmt(portfolio.total_profit)} ({portfolio.total_profit_pct.toFixed(2)}%)</strong>
                </div>
            </div>

            <div className="table-container" style={{ marginBottom: 16, maxHeight: 300, overflowY: 'auto' }}>
              <table className="table">
                <thead><tr><th>Ativo</th><th>Qtd</th><th>Preço Médio</th><th>Preço Atual</th><th>Saldo</th><th>Lucro/Prej.</th><th></th></tr></thead>
                <tbody>
                  {portfolio.items?.map(i => (
                    <tr key={i.id}>
                      <td style={{ fontWeight: 600 }}>{i.ticker}</td>
                      <td>{i.quantity}</td>
                      <td>{fmt(i.average_price)}</td>
                      <td style={{ color: i.current_price ? 'inherit' : 'var(--text-muted)' }}>{i.current_price ? fmt(i.current_price) : 'N/D'}</td>
                      <td>{fmt(i.equity)}</td>
                      <td style={{ color: i.profit >= 0 ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                        {fmt(i.profit)} ({i.profit_pct.toFixed(2)}%)
                      </td>
                      <td style={{ textAlign: 'right' }}><button className="btn btn-secondary btn-sm" onClick={() => deletePortfolioItem(i.id)}>🗑️</button></td>
                    </tr>
                  ))}
                  {portfolio.items?.length === 0 && (
                    <tr>
                      <td colSpan="7" style={{ padding: 0 }}>
                        <EmptyState
                          icon="💼"
                          title="Sua carteira está vazia"
                          subtitle="Adicione ativos abaixo para acompanhar as cotações ao vivo."
                          height="180px"
                        />
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <form onSubmit={addPortfolioItem} style={{ display: 'flex', gap: 10, alignItems: 'flex-end', background: 'var(--bg-elevated)', padding: 16, borderRadius: 8, border: '1px solid var(--border)' }}>
            <div style={{ flex: 1 }}>
               <label className="form-label" style={{ fontSize: 12, marginBottom: 4 }}>Ticker (Ex: PETR4)</label>
               <input className="form-control" value={form.ticker} onChange={e => setForm({...form, ticker: e.target.value.toUpperCase()})} required />
            </div>
            <div style={{ flex: 1 }}>
               <label className="form-label" style={{ fontSize: 12, marginBottom: 4 }}>Quantidade</label>
               <input type="number" step="0.01" min="0.01" className="form-control" value={form.quantity} onChange={e => setForm({...form, quantity: e.target.value})} required />
            </div>
            <div style={{ flex: 1 }}>
               <label className="form-label" style={{ fontSize: 12, marginBottom: 4 }}>Preço Médio (R$)</label>
               <input type="number" step="0.01" min="0.01" className="form-control" value={form.average_price} onChange={e => setForm({...form, average_price: e.target.value})} required />
            </div>
            <button type="submit" className="btn btn-primary" style={{ height: 42, padding: '0 24px' }} disabled={loadPort}>
              Adicionar
            </button>
        </form>
      </div>

      {/* Market Tabs */}
      <div className="chart-card">
        <div className="chart-title">📡 Mercado ao Vivo (B3)</div>
        <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
          {[['acoes','📈 Ações Barsi'],['fiis','🏢 FIIs']].map(([k,l]) => (
            <button key={k} className={`btn ${activeTab===k?'btn-primary':'btn-secondary'} btn-sm`} onClick={() => setActiveTab(k)}>{l}</button>
          ))}
          {loadMkt && <span className="text-muted text-sm">⏳ Carregando cotações...</span>}
        </div>

        {loadMkt ? (
          <SkeletonChart height={200} />
        ) : (
          <div className="stocks-grid">
            {(activeTab === 'acoes' ? market?.stocks : market?.fiis)?.map(s => (
              <div key={s.ticker} className="stock-card">
                <div className="flex-between">
                  <div><div className="stock-ticker">{s.ticker}</div><div className="stock-name">{s.name}</div></div>
                  <span className={SIG[s.signal]?.cls || ''}>{SIG[s.signal]?.label || '—'}</span>
                </div>
                <div className="stock-price" style={{ color: s.price ? 'var(--text)' : 'var(--text-muted)' }}>
                  {s.price ? `R$ ${Number(s.price).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}` : '—'}
                </div>
                {s.change_pct !== null && (
                  <div className={`stock-change ${s.change_pct >= 0 ? 'positive' : 'negative'}`}>
                    {s.change_pct >= 0 ? '▲' : '▼'} {Math.abs(s.change_pct).toFixed(2)}%
                  </div>
                )}
                <div className="stock-meta">
                  <div className="stock-meta-item">DY: <strong>{s.dy ? s.dy + '%' : '—'}</strong></div>
                  <div className="stock-meta-item">P/VP: <strong>{s.pvp || '—'}</strong></div>
                  <div className="stock-meta-item">{activeTab === 'acoes' ? s.sector : s.segment}</div>
                </div>
                {s.error && <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>⚠️ Dados indisponíveis</div>}
              </div>
            ))}
          </div>
        )}
        <div style={{ marginTop: 14, fontSize: 11, color: 'var(--text-muted)' }}>
          🟢 Compra = DY &gt; 6% e P/VP &lt; 2 (critérios Barsi) &nbsp;|&nbsp; Dados: Yahoo Finance (yfinance) &nbsp;|&nbsp; Atualização: ao carregar a página
        </div>
      </div>
    </div>
  )
}
