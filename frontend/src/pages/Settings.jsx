import { useEffect, useState } from 'react'
import axios from 'axios'

function fmt(v) { return 'R$ ' + Number(v||0).toLocaleString('pt-BR', { minimumFractionDigits: 2 }) }

export default function Settings({ onMonthChange }) {
  const [settings, setSettings]   = useState(null)
  const [income, setIncome]       = useState([])
  const [newInc, setNewInc]       = useState({ name: '', amount: '' })
  const [saved, setSaved]         = useState(false)
  const [loading, setLoading]     = useState(true)

  useEffect(() => {
    Promise.all([axios.get('/api/settings'), axios.get('/api/income')])
      .then(([s, i]) => { setSettings(s.data); setIncome(i.data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const save = async () => {
    await axios.put('/api/settings', settings)
    onMonthChange?.(settings.reference_month)
    setSaved(true)
    setTimeout(() => setSaved(false), 2500)
  }

  const addIncome = async () => {
    if (!newInc.name || !newInc.amount) return
    const r = await axios.post('/api/income', { name: newInc.name, amount: parseFloat(newInc.amount) })
    setIncome(i => [...i, r.data])
    setNewInc({ name: '', amount: '' })
  }

  const removeIncome = async (id) => {
    await axios.delete(`/api/income/${id}`)
    setIncome(i => i.filter(x => x.id !== id))
  }

  const set = (k, v) => setSettings(s => ({ ...s, [k]: v }))
  const totalBudget = settings ? (settings.budget_essential_pct || 50) + (settings.budget_important_pct || 30) + (settings.budget_optional_pct || 20) : 100

  if (loading) return <div className="loading"><div className="spinner" /></div>

  return (
    <div>
      <div className="page-header">
        <h1>⚙️ Configurações</h1>
        <p>Personalize seu perfil financeiro e metas</p>
      </div>

      {/* Income */}
      <div className="settings-section">
        <h3>💼 Renda</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>Salário Mensal (R$)</label>
            <input className="form-control" type="number" step="0.01" min="0"
              value={settings.salary || ''} onChange={e => set('salary', parseFloat(e.target.value)||0)}
              placeholder="0,00" />
          </div>
          <div className="form-group">
            <label>Mês de Referência</label>
            <input className="form-control" type="month" value={settings.reference_month || ''}
              onChange={e => set('reference_month', e.target.value)} style={{ colorScheme: 'dark' }} />
          </div>
        </div>

        <div style={{ marginTop: 8 }}>
          <div className="chart-title" style={{ marginBottom: 10 }}>➕ Rendas Extras</div>
          {income.map(i => (
            <div key={i.id} className="income-item">
              <span className="income-name">{i.name}</span>
              <span className="income-amount">{fmt(i.amount)}</span>
              <button className="btn-icon" onClick={() => removeIncome(i.id)}>🗑️</button>
            </div>
          ))}
          <div style={{ display: 'flex', gap: 10, marginTop: 12 }}>
            <input className="form-control" placeholder="Nome da renda (ex: Freelance)"
              value={newInc.name} onChange={e => setNewInc(n => ({ ...n, name: e.target.value }))} />
            <input className="form-control" type="number" placeholder="Valor (R$)" style={{ maxWidth: 150 }}
              value={newInc.amount} onChange={e => setNewInc(n => ({ ...n, amount: e.target.value }))} />
            <button className="btn btn-secondary" onClick={addIncome}>+ Adicionar</button>
          </div>
        </div>
      </div>

      {/* Goals */}
      <div className="settings-section">
        <h3>🎯 Metas</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>Meta Reserva de Emergência (R$)</label>
            <input className="form-control" type="number" step="0.01" min="0"
              value={settings.emergency_reserve_goal || ''} onChange={e => set('emergency_reserve_goal', parseFloat(e.target.value)||0)}
              placeholder="Ex: 18000 (6 meses de gastos)" />
          </div>
          <div className="form-group">
            <label>% da Renda para Investimentos</label>
            <div className="slider-row">
              <input type="range" min="5" max="50" step="1"
                value={settings.investment_pct || 20} onChange={e => set('investment_pct', Number(e.target.value))} />
              <span className="slider-val">{settings.investment_pct || 20}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Investor Profile */}
      <div className="settings-section">
        <h3>📈 Perfil de Investidor</h3>
        <div className="profile-grid">
          {[['conservador','🟢','Conservador'],['moderado','🟡','Moderado'],['agressivo','🔴','Agressivo']].map(([k,i,l]) => (
            <div key={k} className={`profile-btn${settings.investor_profile === k ? ' active' : ''}`} onClick={() => set('investor_profile', k)}>
              <span className="icon">{i}</span>
              <div className="name">{l}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Budget rules */}
      <div className="settings-section">
        <h3>🏷️ Regra Orçamentária <span style={{ fontSize: 12, color: totalBudget === 100 ? 'var(--accent)' : 'var(--red)', fontWeight: 600 }}>({totalBudget}% — deve somar 100%)</span></h3>
        {[
          ['Essenciais (Moradia, Alimentação, Saúde...)', 'budget_essential_pct'],
          ['Importantes (Educação, Pets, Serviços...)', 'budget_important_pct'],
          ['Opcionais (Lazer, Assinaturas, Vestuário...)', 'budget_optional_pct'],
        ].map(([label, key]) => (
          <div className="form-group" key={key}>
            <label>{label}</label>
            <div className="slider-row">
              <input type="range" min="5" max="80" step="5"
                value={settings[key] || 0} onChange={e => set(key, Number(e.target.value))} />
              <span className="slider-val">{settings[key] || 0}%</span>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <button className="btn btn-primary" onClick={save}>💾 Salvar Configurações</button>
        {saved && <span style={{ color: 'var(--accent)', fontSize: 13, fontWeight: 600 }}>✅ Salvo com sucesso!</span>}
      </div>
    </div>
  )
}
