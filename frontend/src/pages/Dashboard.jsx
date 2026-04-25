import { useEffect, useState } from 'react'
import api from '../api/client'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'

const COLORS = ['#10b981','#3b82f6','#f59e0b','#8b5cf6','#ef4444','#06b6d4','#ec4899','#84cc16','#f97316','#a78bfa']
const PRIO_COLORS = { Essencial: '#10b981', Importante: '#f59e0b', Opcional: '#ef4444' }

function fmt(v) {
  if (!v && v !== 0) return 'R$ 0,00'
  return 'R$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2 })
}

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: '#0f1829', border: '1px solid #1e3050', borderRadius: 8, padding: '8px 14px', fontSize: 12 }}>
      <div style={{ color: '#f0f6ff', fontWeight: 600 }}>{payload[0].name}</div>
      <div style={{ color: payload[0].color }}>{fmt(payload[0].value)}</div>
    </div>
  )
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/api/analysis').then(r => { setData(r.data); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading"><div className="spinner" /><span>Carregando...</span></div>
  if (!data) return <div className="empty"><div className="icon">âš ï¸</div><p>Erro ao carregar dados</p></div>

  const catData = Object.entries(data.category_totals || {}).map(([name, value]) => ({ name, value }))
  const prioData = [
    { name: 'Essencial', real: data.priority_totals?.Essencial || 0, limite: data.budget_limits?.essential || 0 },
    { name: 'Importante', real: data.priority_totals?.Importante || 0, limite: data.budget_limits?.important || 0 },
    { name: 'Opcional', real: data.priority_totals?.Opcional || 0, limite: data.budget_limits?.optional || 0 },
  ]

  const income = data.total_income || 0
  const expenses = data.total_expenses || 0
  const essPct = income ? ((data.priority_totals?.Essencial || 0) / income * 100) : 0
  const impPct = income ? ((data.priority_totals?.Importante || 0) / income * 100) : 0
  const optPct = income ? ((data.priority_totals?.Opcional || 0) / income * 100) : 0
  const freePct = Math.max(0, 100 - essPct - impPct - optPct)

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>VisÃ£o geral das suas finanÃ§as â€” {data.reference_month || 'mÃªs atual'}</p>
      </div>

      {/* Cards */}
      <div className="cards-grid">
        <div className="card">
          <div className="card-icon">ðŸ’¼</div>
          <div className="card-label">Renda Total</div>
          <div className="card-value green">{fmt(income)}</div>
          <div className="card-sub">SalÃ¡rio + rendas extras</div>
        </div>
        <div className="card">
          <div className="card-icon">ðŸ’¸</div>
          <div className="card-label">Total de Gastos</div>
          <div className={`card-value ${expenses > income ? 'red' : 'amber'}`}>{fmt(expenses)}</div>
          <div className="card-sub">{data.expense_count || 0} lanÃ§amentos</div>
        </div>
        <div className="card">
          <div className="card-icon">ðŸ’°</div>
          <div className="card-label">Saldo DisponÃ­vel</div>
          <div className={`card-value ${data.balance >= 0 ? 'green' : 'red'}`}>{fmt(data.balance)}</div>
          <div className="card-sub">{income > 0 ? ((data.balance / income) * 100).toFixed(1) + '% da renda' : 'â€”'}</div>
        </div>
        <div className="card">
          <div className="card-icon">ðŸŽ­</div>
          <div className="card-label">Gastos Opcionais</div>
          <div className="card-value amber">{fmt(data.optional_expenses)}</div>
          <div className="card-sub">Limite: {fmt(data.budget_limits?.optional)}</div>
        </div>
      </div>

      {/* Commitment bar */}
      <div className="progress-bar-container chart-card" style={{ marginBottom: 16 }}>
        <div className="chart-title">ðŸŽ¯ Comprometimento do salÃ¡rio</div>
        <div className="progress-track">
          <div className="progress-segment" style={{ width: essPct + '%', background: '#10b981' }} title={`Essencial ${essPct.toFixed(1)}%`} />
          <div className="progress-segment" style={{ width: impPct + '%', background: '#f59e0b' }} title={`Importante ${impPct.toFixed(1)}%`} />
          <div className="progress-segment" style={{ width: optPct + '%', background: '#ef4444' }} title={`Opcional ${optPct.toFixed(1)}%`} />
          <div className="progress-segment" style={{ width: freePct + '%', background: '#1e3050' }} title={`Livre ${freePct.toFixed(1)}%`} />
        </div>
        <div className="progress-legend">
          {[['#10b981','Essencial',essPct],['#f59e0b','Importante',impPct],['#ef4444','Opcional',optPct],['#1e3050','DisponÃ­vel',freePct]].map(([c,l,p]) => (
            <div key={l} className="legend-item"><div className="legend-dot" style={{ background: c }} />{l} {p.toFixed(1)}%</div>
          ))}
        </div>
      </div>

      {/* Charts */}
      <div className="charts-grid">
        <div className="chart-card">
          <div className="chart-title">ðŸ• Gastos por Categoria</div>
          {catData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={catData} cx="50%" cy="50%" outerRadius={90} dataKey="value" label={({ name, percent }) => `${name} ${(percent*100).toFixed(0)}%`} labelLine={false} fontSize={11}>
                  {catData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          ) : <div className="empty" style={{ height: 200 }}><p>Sem dados. Adicione despesas.</p></div>}
        </div>

        <div className="chart-card">
          <div className="chart-title">ðŸ“Š Gastos por Prioridade vs. Limite</div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={prioData} barGap={4}>
              <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => 'R$' + (v/1000).toFixed(0) + 'k'} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11, color: '#64748b' }} />
              <Bar dataKey="real" name="Real" radius={[4,4,0,0]} fill="#3b82f6" />
              <Bar dataKey="limite" name="Limite" radius={[4,4,0,0]} fill="#1e3050" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent expenses */}
      <div className="table-card">
        <div className="table-header">
          <h3>ðŸ• Despesas Recentes</h3>
          <a href="/expenses" style={{ fontSize: 12, color: 'var(--accent)', textDecoration: 'none' }}>Ver todas â†’</a>
        </div>
        {data.recent_expenses?.length > 0 ? (
          <table>
            <thead><tr><th>DescriÃ§Ã£o</th><th>Categoria</th><th>Prioridade</th><th>Data</th><th style={{textAlign:'right'}}>Valor</th></tr></thead>
            <tbody>
              {data.recent_expenses.map(e => (
                <tr key={e.id}>
                  <td style={{ color: 'var(--text)' }}>{e.description}</td>
                  <td>{e.category}</td>
                  <td><span className={`badge ${e.priority==='Essencial'?'badge-green':e.priority==='Importante'?'badge-amber':'badge-red'}`}>{e.priority}</span></td>
                  <td>{e.date}</td>
                  <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--text)' }}>{fmt(e.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <div className="empty"><p>Nenhuma despesa cadastrada.</p></div>}
      </div>
    </div>
  )
}

