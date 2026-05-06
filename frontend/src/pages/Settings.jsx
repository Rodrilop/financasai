import { useEffect, useState, useContext } from 'react'
import { useOutletContext } from 'react-router-dom'
import api from '../api/client'
import { useToast } from '../contexts/ToastContext'
import { AuthContext } from '../contexts/AuthContext'

function fmt(v) { return 'R$ ' + Number(v||0).toLocaleString('pt-BR', { minimumFractionDigits: 2 }) }

export default function Settings() {
  const { user, refreshProfile } = useContext(AuthContext)
  const { toast } = useToast()
  const [settings, setSettings]   = useState(null)
  const [income, setIncome]       = useState([])
  const [newInc, setNewInc]       = useState({ name: '', amount: '', account: 'Geral' })
  const [saved, setSaved]         = useState(false)
  const [loading, setLoading]     = useState(true)
  const [phone, setPhone]         = useState('')
  const [phoneSaved, setPhoneSaved] = useState(false)
  const [accounts, setAccounts]   = useState([])
  const [newAcc, setNewAcc]       = useState({ name: '', type: 'Conta Corrente' })

  const { month } = useOutletContext()

  useEffect(() => {
    Promise.all([
      api.get('/api/settings'),
      api.get(`/api/income?month=${month || ''}`),
      api.get('/api/profile'),
      api.get('/api/accounts')
    ])
      .then(([s, i, p, a]) => {
        setSettings(s.data)
        setIncome(i.data)
        setPhone(p.data.phone || '')
        setAccounts(a.data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [month])

  const savePhone = async () => {
    try {
      await api.put('/api/profile', { phone })
      setPhoneSaved(true)
      setTimeout(() => setPhoneSaved(false), 2500)
    } catch (err) {
      alert(err?.response?.data?.detail || 'Erro ao salvar número.')
    }
  }

  const save = async () => {
    await api.put('/api/settings', settings)
    setSaved(true)
    setTimeout(() => setSaved(false), 2500)
  }

  const addIncome = async () => {
    if (!newInc.name || !newInc.amount) return
    await api.post('/api/income', { ...newInc, amount: parseFloat(newInc.amount), date: `${month}-01` })
    setNewInc({ name: '', amount: '', account: 'Geral' })
    const r = await api.get(`/api/income?month=${month || ''}`)
    setIncome(r.data)
  }

  const removeIncome = async (id) => {
    await api.delete(`/api/income/${id}`)
    setIncome(income.filter(i => i.id !== id))
  }

  const addAccount = async () => {
    if (!newAcc.name) return
    await api.post('/api/accounts', newAcc)
    setNewAcc({ name: '', type: 'Conta Corrente' })
    const r = await api.get('/api/accounts')
    setAccounts(r.data)
  }

  const removeAccount = async (id) => {
    if (!window.confirm('Excluir esta conta?')) return
    await api.delete(`/api/accounts/${id}`)
    setAccounts(accounts.filter(a => a.id !== id))
  }

  const handleUpgrade = async () => {
    try {
      await api.post('/api/auth/upgrade')
      toast.success('🚀 Parabéns! Você agora é um usuário PRO.')
      await refreshProfile()
    } catch {
      toast.error('Erro ao realizar upgrade.')
    }
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

      {/* Plano Pro */}
      <div className={`settings-section ${user?.isPro ? 'pro-active' : ''}`} style={{ background: user?.isPro ? 'linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(59, 130, 246, 0.1))' : 'var(--bg-card)', border: user?.isPro ? '1px solid var(--accent)' : '1px solid var(--border)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {user?.isPro ? '💎 Plano Pro Ativo' : '🚀 Upgrade para o Pro'}
              {user?.isPro && <span className="badge badge-purple" style={{ fontSize: 10 }}>PREMIUM</span>}
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
              {user?.isPro 
                ? 'Você tem acesso ilimitado a todas as ferramentas e análises avançadas da IA.' 
                : 'Libere recomendações personalizadas, suporte a multi-contas e insights de mercado ilimitados.'}
            </p>
          </div>
          {!user?.isPro && (
            <button className="btn btn-primary" onClick={handleUpgrade} style={{ padding: '10px 20px', fontWeight: 700 }}>
              Virar Pro — Grátis
            </button>
          )}
        </div>
      </div>

      {/* Perfil / WhatsApp */}
      <div className="settings-section">
        <h3>📱 Meu Perfil — Integração WhatsApp</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 16 }}>
          Cadastre seu número de WhatsApp (com DDD, sem espaços ou caracteres especiais) para usar o assistente financeiro diretamente pelo WhatsApp.
        </p>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <input
            className="form-control"
            placeholder="Ex: 11999998888"
            value={phone}
            onChange={e => setPhone(e.target.value.replace(/\D/g, ''))}
            maxLength={13}
            style={{ maxWidth: 220 }}
          />
          <button className="btn btn-secondary" onClick={savePhone}>💾 Salvar Número</button>
          {phoneSaved && <span style={{ color: 'var(--accent)', fontSize: 13, fontWeight: 600 }}>✅ Número salvo!</span>}
        </div>
        {phone && (
          <p style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 8 }}>
            📞 Número cadastrado: <strong style={{ color: 'var(--text)' }}>+{phone}</strong>
          </p>
        )}
      </div>

      {/* Accounts */}
      <div className="settings-section">
        <h3>🏦 Minhas Contas</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 16 }}>
          Gerencie as contas bancárias e carteiras que você utiliza.
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12, marginBottom: 16 }}>
          {accounts.map(acc => (
            <div key={acc.id} className="card" style={{ padding: '12px 16px', position: 'relative' }}>
              <div style={{ fontSize: 14, fontWeight: 700 }}>{acc.name}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{acc.type}</div>
              <button className="btn-icon" onClick={() => removeAccount(acc.id)} 
                style={{ position: 'absolute', top: 8, right: 8, padding: 4, fontSize: 12 }}>🗑️</button>
            </div>
          ))}
          {accounts.length === 0 && <div className="text-muted" style={{ fontSize: 13, gridColumn: '1/-1' }}>Nenhuma conta cadastrada.</div>}
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <input className="form-control" placeholder="Nome da conta (ex: Nubank)" value={newAcc.name} onChange={e => setNewAcc({ ...newAcc, name: e.target.value })} />
          <select className="form-control" value={newAcc.type} onChange={e => setNewAcc({ ...newAcc, type: e.target.value })} style={{ maxWidth: 160 }}>
            <option>Conta Corrente</option>
            <option>Poupança</option>
            <option>Investimentos</option>
            <option>Dinheiro</option>
          </select>
          <button className="btn btn-secondary" onClick={addAccount}>+ Adicionar</button>
        </div>
      </div>

      {/* Income */}
      <div className="settings-section">
        <h3>💼 Receitas do Mês</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 16 }}>Registre todas as entradas de dinheiro para o mês de {month}.</p>
        
        <div className="income-list" style={{ marginBottom: 16 }}>
          {income.map(i => (
            <div key={i.id} className="income-item">
              <div className="income-name">{i.name} <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>({i.account})</span></div>
              <div className="income-amount">{fmt(i.amount)}</div>
              <button className="btn-icon" onClick={() => removeIncome(i.id)}>🗑️</button>
            </div>
          ))}
          {income.length === 0 && <div className="text-muted" style={{ fontSize: 13 }}>Nenhuma receita registrada para este mês.</div>}
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <input className="form-control" placeholder="Nome (Ex: Salário)" value={newInc.name} onChange={e => setNewInc({ ...newInc, name: e.target.value })} />
          <input className="form-control" type="number" placeholder="Valor" value={newInc.amount} onChange={e => setNewInc({ ...newInc, amount: e.target.value })} style={{ maxWidth: 120 }} />
          <select className="form-control" value={newInc.account} onChange={e => setNewInc({ ...newInc, account: e.target.value })} style={{ maxWidth: 140 }}>
            <option value="Geral">Conta Geral</option>
            {accounts.map(a => <option key={a.id} value={a.name}>{a.name}</option>)}
          </select>
          <button className="btn btn-primary" onClick={addIncome}>+ Adicionar</button>
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
