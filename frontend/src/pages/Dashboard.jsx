import { useEffect, useState } from 'react'
import { useNavigate, useOutletContext } from 'react-router-dom'
import api from '../api/client'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { SkeletonCardsGrid, SkeletonChart, SkeletonTable } from '../components/Skeletons'
import EmptyState from '../components/EmptyState'
import CountUp from '../components/CountUp'

const COLORS = ['#10b981','#3b82f6','#f59e0b','#8b5cf6','#ef4444','#06b6d4','#ec4899','#84cc16','#f97316','#a78bfa']
const PRIO_COLORS = { Essencial: '#10b981', Importante: '#f59e0b', Opcional: '#ef4444' }

function fmt(v) {
  if (!v && v !== 0) return 'R$ 0,00'
  return 'R$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2 })
}

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-light)', borderRadius: 8, padding: '8px 14px', fontSize: 12, boxShadow: 'var(--shadow)' }}>
      <div style={{ color: 'var(--text)', fontWeight: 600 }}>{payload[0].name}</div>
      <div style={{ color: payload[0].color }}>{fmt(payload[0].value)}</div>
    </div>
  )
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  const { month } = useOutletContext()

  useEffect(() => {
    setLoading(true);
    api.get(`/api/analysis?month=${month || ''}`)
      .then(r => { setData(r.data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [month])

  /* ── Skeleton ── */
  if (loading) return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Carregando seus dados financeiros...</p>
      </div>
      <SkeletonCardsGrid count={4} />
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: 22, marginBottom: 28 }}>
        <div className="skeleton" style={{ width: '30%', height: 13, marginBottom: 16, borderRadius: 6 }} />
        <div className="skeleton" style={{ width: '100%', height: 10, borderRadius: 99 }} />
        <div style={{ display: 'flex', gap: 16, marginTop: 10 }}>
          {[70, 80, 60, 55].map((w, i) => <div key={i} className="skeleton" style={{ width: w, height: 11, borderRadius: 6 }} />)}
        </div>
      </div>
      <div className="charts-grid">
        <div className="chart-card"><SkeletonChart height={220} /></div>
        <div className="chart-card"><SkeletonChart height={220} /></div>
      </div>
      <div className="table-card">
        <div className="table-header">
          <div className="skeleton" style={{ width: 160, height: 14, borderRadius: 6 }} />
          <div className="skeleton" style={{ width: 60, height: 12, borderRadius: 6 }} />
        </div>
        <SkeletonTable rows={4} />
      </div>
    </div>
  )

  /* ── Erro / sem dados ── */
  if (!data) return (
    <div>
      <div className="page-header"><h1>Dashboard</h1></div>
      <EmptyState
        icon="⚠️"
        title="Não foi possível carregar os dados"
        subtitle="Verifique sua conexão ou tente atualizar a página."
        actionLabel="Tentar novamente"
        onAction={() => window.location.reload()}
        height="320px"
      />
    </div>
  )

  const catData = Object.entries(data.category_totals || {}).map(([name, value]) => ({ name, value }))
  const prioData = [
    { name: 'Essencial',  real: data.priority_totals?.Essencial  || 0, limite: data.budget_limits?.essential || 0 },
    { name: 'Importante', real: data.priority_totals?.Importante || 0, limite: data.budget_limits?.important || 0 },
    { name: 'Opcional',   real: data.priority_totals?.Opcional   || 0, limite: data.budget_limits?.optional  || 0 },
  ]

  const income   = data.total_income   || 0
  const expenses = data.total_expenses || 0
  const essPct = income ? ((data.priority_totals?.Essencial  || 0) / income * 100) : 0
  const impPct = income ? ((data.priority_totals?.Importante || 0) / income * 100) : 0
  const optPct = income ? ((data.priority_totals?.Opcional   || 0) / income * 100) : 0
  const freePct = Math.max(0, 100 - essPct - impPct - optPct)

  const hasExpenses = catData.length > 0

  return (
    <div>
      <div className="page-header" style={{ animation: 'fadeIn 300ms ease' }}>
        <h1>Dashboard</h1>
        <p>Visão geral das suas finanças</p>
      </div>

      {/* ── KPI Cards (stagger fadeInUp) ── */}
      <div className="cards-grid" style={{ marginBottom: 28 }}>

        <div className="card card-animated">
          <div className="card-icon">💼</div>
          <div className="card-label">Receitas do Mês</div>
          <div className="card-value green">
            R$ <CountUp end={income} decimals={2} locale="pt-BR" />
          </div>
          <div className="card-sub">{data.previous_balance > 0 ? `+ ${fmt(data.previous_balance)} de saldo anterior` : 'Todas as receitas'}</div>
        </div>

        <div className="card card-animated">
          <div className="card-icon">💸</div>
          <div className="card-label">Total de Gastos</div>
          <div className={`card-value ${expenses > income ? 'red' : 'amber'}`}>
            R$ <CountUp end={expenses} decimals={2} locale="pt-BR" />
          </div>
          <div className="card-sub">{data.expense_count || 0} lançamentos</div>
        </div>

        <div className="card card-animated">
          <div className="card-icon">💰</div>
          <div className="card-label">Saldo Disponível</div>
          <div className={`card-value ${(data.balance ?? 0) >= 0 ? 'green' : 'red'}`}>
            R$ <CountUp end={data.balance ?? 0} decimals={2} locale="pt-BR" />
          </div>
          <div className="card-sub">
            {income > 0 ? ((data.balance / income) * 100).toFixed(1) + '% da renda' : '—'}
          </div>
        </div>

        <div className="card card-animated">
          <div className="card-icon">🎭</div>
          <div className="card-label">Gastos Opcionais</div>
          <div className="card-value amber">
            R$ <CountUp end={data.optional_expenses ?? 0} decimals={2} locale="pt-BR" />
          </div>
          <div className="card-sub">Limite: {fmt(data.budget_limits?.optional)}</div>
        </div>

      </div>

      {/* ── Barra de Comprometimento (animação de preenchimento) ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16, marginBottom: 16 }}>
        
        <div className="progress-bar-container chart-card" style={{ marginBottom: 0, animation: 'fadeInUp 500ms 280ms var(--ease-out) both' }}>
          <div className="chart-title">🎯 Comprometimento do salário</div>
          <div className="progress-track">
            <div className="progress-segment" style={{ width: essPct + '%', background: '#10b981', animation: 'progressFill 1.2s 400ms ease both' }} title={`Essencial ${essPct.toFixed(1)}%`} />
            <div className="progress-segment" style={{ width: impPct + '%', background: '#f59e0b', animation: 'progressFill 1.2s 550ms ease both' }} title={`Importante ${impPct.toFixed(1)}%`} />
            <div className="progress-segment" style={{ width: optPct + '%', background: '#ef4444', animation: 'progressFill 1.2s 700ms ease both' }} title={`Opcional ${optPct.toFixed(1)}%`} />
            <div className="progress-segment" style={{ width: freePct + '%', background: 'var(--border)', animation: 'progressFill 1.2s 850ms ease both' }} title={`Livre ${freePct.toFixed(1)}%`} />
          </div>
          <div className="progress-legend">
            {[['#10b981','Essencial',essPct],['#f59e0b','Importante',impPct],['#ef4444','Opcional',optPct],['var(--border)','Disponível',freePct]].map(([c,l,p]) => (
              <div key={l} className="legend-item"><div className="legend-dot" style={{ background: c }} />{l} {p.toFixed(1)}%</div>
            ))}
          </div>
        </div>

        <div className="chart-card" style={{ animation: 'fadeInUp 500ms 350ms var(--ease-out) both', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <div className="chart-title">🛡️ Reserva de Emergência</div>
          <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>
            {fmt(data.emergency_current)} <small style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 400 }}>de {fmt(data.emergency_goal)}</small>
          </div>
          <div className="progress-thin" style={{ height: 8 }}>
            <div className="progress-fill" style={{ width: Math.min(100, (data.emergency_current / (data.emergency_goal || 1)) * 100) + '%' }} />
          </div>
          <div style={{ fontSize: 11, marginTop: 8, color: 'var(--text-muted)' }}>
            {data.emergency_goal > 0 
              ? `${Math.min(100, (data.emergency_current / data.emergency_goal) * 100).toFixed(1)}% da meta atingida`
              : 'Defina uma meta em Configurações'}
          </div>
        </div>

      </div>

      {/* ── Gráficos ── */}
      <div className="charts-grid">
        <div className="chart-card chart-card-animated">
          <div className="chart-title">🍕 Gastos por Categoria</div>
          {hasExpenses ? (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={catData} cx="50%" cy="50%" outerRadius={90} dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent*100).toFixed(0)}%`}
                  labelLine={false} fontSize={11}>
                  {catData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState
              icon="🍕"
              title="Nenhuma categoria ainda"
              subtitle="Adicione despesas para ver como seus gastos se distribuem."
              actionLabel="+ Adicionar Despesa"
              onAction={() => navigate('/expenses')}
              height="200px"
            />
          )}
        </div>

        <div className="chart-card chart-card-animated">
          <div className="chart-title">📊 Gastos por Prioridade vs. Limite</div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={prioData} barGap={4}>
              <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => 'R$' + (v/1000).toFixed(0) + 'k'} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11, color: '#64748b' }} />
              <Bar dataKey="real"   name="Real"   radius={[4,4,0,0]} fill="#3b82f6" />
              <Bar dataKey="limite" name="Limite" radius={[4,4,0,0]} fill="var(--border)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Despesas Recentes ── */}
      <div className="table-card" style={{ animation: 'fadeInUp 500ms 460ms var(--ease-out) both' }}>
        <div className="table-header">
          <h3>🕐 Despesas Recentes</h3>
          <a href="/expenses" style={{ fontSize: 12, color: 'var(--accent)', textDecoration: 'none' }}>Ver todas →</a>
        </div>
        {data.recent_expenses?.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>Descrição</th><th>Categoria</th><th>Prioridade</th><th>Data</th>
                <th style={{ textAlign: 'right' }}>Valor</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_expenses.map(e => (
                <tr key={e.id}>
                  <td style={{ color: 'var(--text)' }}>{e.description}</td>
                  <td>{e.category}</td>
                  <td>
                    <span className={`badge ${e.priority==='Essencial'?'badge-green':e.priority==='Importante'?'badge-amber':'badge-red'}`}>
                      {e.priority}
                    </span>
                  </td>
                  <td>{e.date}</td>
                  <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--text)' }}>{fmt(e.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <EmptyState
            icon="🧾"
            title="Nenhuma despesa ainda"
            subtitle="Registre seu primeiro gasto e veja tudo aqui em tempo real."
            actionLabel="+ Registrar Despesa"
            onAction={() => navigate('/expenses')}
            height="200px"
          />
        )}
      </div>
    </div>
  )
}
