import { useEffect, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import api from '../api/client'

function fmt(v) { return 'R$ ' + Number(v||0).toLocaleString('pt-BR', { minimumFractionDigits: 2 }) }

export default function Settings() {
  const [settings, setSettings]   = useState(null)
  const [income, setIncome]       = useState([])
  const [newInc, setNewInc]       = useState({ name: '', amount: '' })
  const [saved, setSaved]         = useState(false)
  const [loading, setLoading]     = useState(true)

  const { month } = useOutletContext()

  useEffect(() => {
    Promise.all([api.get('/api/settings'), api.get(`/api/income?month=${month || ''}`)])
      .then(([s, i]) => { setSettings(s.data); setIncome(i.data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [month])

  const save = async () => {
    await api.put('/api/settings', settings)
    setSaved(true)
    setTimeout(() => setSaved(false), 2500)
  }

  const addIncome = async () => {
    if (!newInc.name || !newInc.amount) return
    const r = await api.post('/api/income', { 
      name: newInc.name, 
      amount: parseFloat(newInc.amount),
      date: (month || new Date().toISOString().slice(0, 7)) + '-01'
    })
    setIncome(i => [...i, r.data])
    setNewInc({ name: '', amount: '' })
  }

  const removeIncome = async (id) => {
    await api.delete(`/api/income/${id}`)
    setIncome(i => i.filter(x => x.id !== id))
  }

  const [editIncId, setEditIncId] = useState(null)
  const [editInc, setEditInc]     = useState({ name: '', amount: '' })

  const startEditIncome = (i) => { setEditIncId(i.id); setEditInc({ name: i.name, amount: String(i.amount) }) }
  const cancelEditIncome = () => { setEditIncId(null); setEditInc({ name: '', amount: '' }) }

  const saveEditIncome = async () => {
    if (!editInc.name || !editInc.amount) return
    try {
      const r = await api.put(`/api/income/${editIncId}`, {
        name: editInc.name,
        amount: parseFloat(editInc.amount),
        date: (month || new Date().toISOString().slice(0, 7)) + '-01'
      })
      setIncome(list => list.map(x => x.id === editIncId ? r.data : x))
      cancelEditIncome()
    } catch { cancelEditIncome() }
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
        <h3>💼 Receitas do Mês</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 16 }}>
          Lance aqui todas as suas receitas deste mês (ex: Salário, Freelance, Rendimentos).
        </p>
        <div>
          {income.length === 0 && (
            <div style={{ color: 'var(--text-muted)', fontSize: 13, padding: '12px 0' }}>
              ⚠️ Nenhuma receita lançada este mês. Lance seu salário e outras rendas aqui.
            </div>
          )}
          {income.map(i => (
            <div key={i.id} className="income-item" style={{ alignItems: 'center', gap: 8 }}>
              {editIncId === i.id ? (
                <>
                  <input className="form-control" style={{ flex: 1 }} value={editInc.name}
                    onChange={e => setEditInc(n => ({ ...n, name: e.target.value }))} />
                  <input className="form-control" type="number" style={{ maxWidth: 130 }} value={editInc.amount}
                    onChange={e => setEditInc(n => ({ ...n, amount: e.target.value }))} />
                  <button className="btn btn-primary btn-sm" onClick={saveEditIncome}>✓</button>
                  <button className="btn btn-secondary btn-sm" onClick={cancelEditIncome}>Cancelar</button>
                </>
              ) : (
                <>
                  <span className="income-name">{i.name}</span>
                  <span className="income-amount">{fmt(i.amount)}</span>
                  <button className="btn-icon" onClick={() => startEditIncome(i)} title="Editar">✏️</button>
                  <button className="btn-icon" onClick={() => removeIncome(i.id)} title="Excluir">🗑️</button>
                </>
              )}
            </div>
          ))}
          <div style={{ display: 'flex', gap: 10, marginTop: 12 }}>
            <input className="form-control" placeholder="Nome da receita (ex: Salário)"
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
