import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import { useToast } from '../contexts/ToastContext'

const STEPS = [
  { id: 1, label: 'Boas-vindas',   icon: '👋' },
  { id: 2, label: 'Sua Renda',     icon: '💼' },
  { id: 3, label: 'Pronto!',       icon: '🚀' },
]

const CATEGORIES = ['Moradia','Alimentação','Transporte','Saúde','Educação','Lazer','Assinaturas','Vestuário','Pets','Outros']

export default function Onboarding({ userName, onComplete }) {
  const navigate = useNavigate()
  const toast    = useToast()
  const [step, setStep]     = useState(1)
  const [loading, setLoading] = useState(false)

  // Step 2 — income
  const today = new Date()
  const currentMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`
  const [income, setIncome] = useState({ name: 'Salário', amount: '' })

  // Step 3 — optional first expense
  const [expense, setExpense]     = useState({ description: '', amount: '', category: 'Alimentação', date: today.toISOString().slice(0, 10) })
  const [skipExpense, setSkipExpense] = useState(false)

  const handleSaveIncome = async () => {
    if (!income.amount || isNaN(parseFloat(income.amount))) {
      toast.warning('Informe o valor da sua renda.')
      return
    }
    setLoading(true)
    try {
      await api.post('/api/income', {
        name: income.name || 'Salário',
        amount: parseFloat(income.amount),
        date: `${currentMonth}-01`
      })
      setStep(3)
    } catch {
      toast.error('Erro ao salvar renda. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveExpense = async () => {
    if (!skipExpense) {
      if (!expense.description || !expense.amount) {
        toast.warning('Preencha a descrição e o valor da despesa.')
        return
      }
      setLoading(true)
      try {
        await api.post('/api/expenses', {
          description: expense.description,
          amount: parseFloat(expense.amount),
          category: expense.category,
          priority: 'Essencial',
          date: expense.date,
          notes: ''
        })
      } catch {
        toast.error('Erro ao salvar despesa.')
        setLoading(false)
        return
      } finally {
        setLoading(false)
      }
    }
    onComplete()
    navigate('/')
  }

  return (
    <div className="onboarding-overlay">
      {/* Progress bar */}
      <div className="onboarding-progress">
        {STEPS.map((s, i) => (
          <div key={s.id} className="onboarding-progress-item">
            <div className={`ob-step-dot ${step > s.id ? 'done' : step === s.id ? 'active' : ''}`}>
              {step > s.id ? '✓' : s.icon}
            </div>
            <span className={`ob-step-label ${step === s.id ? 'active' : ''}`}>{s.label}</span>
            {i < STEPS.length - 1 && <div className={`ob-step-line ${step > s.id ? 'done' : ''}`} />}
          </div>
        ))}
      </div>

      <div className="onboarding-card">

        {/* ── STEP 1: Welcome ─────────────────────────────── */}
        {step === 1 && (
          <div className="ob-step" style={{ animationDelay: '0ms' }}>
            <div className="ob-emoji">🎉</div>
            <h2>Bem-vindo, {userName}!</h2>
            <p>
              O <strong>FinançasAI</strong> é seu assistente financeiro inteligente com IA.
              Vamos configurar sua conta em menos de 1 minuto para você ter
              controle total do seu dinheiro.
            </p>
            <div className="ob-feature-list">
              {[
                ['📊', 'Dashboard com visão mensal do seu dinheiro'],
                ['🤖', 'Assistente de IA que entende linguagem natural'],
                ['📱', 'Integração com WhatsApp para lançamentos rápidos'],
                ['📈', 'Análise inteligente de gastos e investimentos'],
              ].map(([icon, text]) => (
                <div key={text} className="ob-feature">
                  <span>{icon}</span>
                  <span>{text}</span>
                </div>
              ))}
            </div>
            <button className="btn btn-primary ob-btn" onClick={() => setStep(2)}>
              Vamos começar →
            </button>
          </div>
        )}

        {/* ── STEP 2: Income ──────────────────────────────── */}
        {step === 2 && (
          <div className="ob-step">
            <div className="ob-emoji">💼</div>
            <h2>Qual é sua renda este mês?</h2>
            <p>
              Informe seu salário ou renda principal de <strong>{currentMonth}</strong>.
              Você pode adicionar outras fontes de renda depois em <em>Configurações</em>.
            </p>
            <div className="ob-fields">
              <div className="form-group">
                <label>Tipo de renda</label>
                <input
                  className="form-control"
                  value={income.name}
                  onChange={e => setIncome(n => ({ ...n, name: e.target.value }))}
                  placeholder="Ex: Salário, Freelance, Aluguel..."
                />
              </div>
              <div className="form-group">
                <label>Valor (R$) *</label>
                <input
                  className="form-control"
                  type="number"
                  step="0.01"
                  min="0"
                  autoFocus
                  value={income.amount}
                  onChange={e => setIncome(n => ({ ...n, amount: e.target.value }))}
                  placeholder="Ex: 5000,00"
                />
              </div>
            </div>
            <div className="ob-actions">
              <button className="btn btn-secondary" onClick={() => setStep(1)}>← Voltar</button>
              <button className="btn btn-primary ob-btn" onClick={handleSaveIncome} disabled={loading}>
                {loading ? 'Salvando...' : 'Salvar e continuar →'}
              </button>
            </div>
          </div>
        )}

        {/* ── STEP 3: First expense (optional) ────────────── */}
        {step === 3 && (
          <div className="ob-step">
            <div className="ob-emoji">🧾</div>
            <h2>Adicione sua primeira despesa</h2>
            <p>Opcional — mas registrar um gasto agora ajuda a ver seu saldo em tempo real.</p>

            {!skipExpense ? (
              <div className="ob-fields">
                <div className="form-group">
                  <label>Descrição *</label>
                  <input
                    className="form-control"
                    value={expense.description}
                    onChange={e => setExpense(x => ({ ...x, description: e.target.value }))}
                    placeholder="Ex: Aluguel, Supermercado..."
                  />
                </div>
                <div className="form-grid">
                  <div className="form-group">
                    <label>Valor (R$) *</label>
                    <input
                      className="form-control"
                      type="number" step="0.01" min="0"
                      value={expense.amount}
                      onChange={e => setExpense(x => ({ ...x, amount: e.target.value }))}
                      placeholder="0,00"
                    />
                  </div>
                  <div className="form-group">
                    <label>Data</label>
                    <input
                      className="form-control"
                      type="date"
                      value={expense.date}
                      onChange={e => setExpense(x => ({ ...x, date: e.target.value }))}
                      style={{ colorScheme: 'dark' }}
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label>Categoria</label>
                  <select
                    className="form-control"
                    value={expense.category}
                    onChange={e => setExpense(x => ({ ...x, category: e.target.value }))}
                  >
                    {CATEGORIES.map(c => <option key={c}>{c}</option>)}
                  </select>
                </div>
              </div>
            ) : (
              <div style={{ background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', padding: 20, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
                Tudo bem! Você pode adicionar despesas a qualquer momento na aba <strong>Despesas</strong>.
              </div>
            )}

            <div className="ob-actions">
              <button className="btn btn-secondary" onClick={() => setSkipExpense(s => !s)}>
                {skipExpense ? '+ Adicionar despesa' : 'Pular esta etapa'}
              </button>
              <button className="btn btn-primary ob-btn" onClick={handleSaveExpense} disabled={loading}>
                {loading ? 'Salvando...' : skipExpense ? 'Ir para o Dashboard 🚀' : 'Salvar e começar 🚀'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
