import { useEffect, useState, useCallback } from 'react'
import { useOutletContext } from 'react-router-dom'
import api from '../api/client'
import Modal from '../components/Modal'
import { useToast } from '../contexts/ToastContext'
import EmptyState from '../components/EmptyState'
import { SkeletonTable } from '../components/Skeletons'

const CATEGORIES = ['Moradia','Alimentação','Transporte','Saúde','Educação','Lazer','Assinaturas','Vestuário','Pets','Outros']
const PRIORITIES = ['Essencial','Importante','Opcional']

function fmt(v) { return 'R$ ' + Number(v || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 }) }

const makeEmptyForm = (month) => {
  const base = month || new Date().toISOString().slice(0, 7)
  const today = new Date().toISOString().slice(0, 7)
  // Se o mês selecionado for o mês atual, usa a data de hoje; senão, usa o último dia do mês
  let date
  if (base === today) {
    date = new Date().toISOString().slice(0, 10)
  } else {
    const [y, m] = base.split('-')
    date = `${y}-${m}-01`
  }
  return { description: '', amount: '', category: 'Alimentação', priority: 'Essencial', date, notes: '' }
}

export default function Expenses() {
  const toast = useToast()
  const [expenses, setExpenses] = useState([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(null) // null | 'add' | 'edit'
  const [form, setForm] = useState(() => makeEmptyForm(new Date().toISOString().slice(0, 7)))
  const [editId, setEditId] = useState(null)
  const [selected, setSelected] = useState([])
  const { month } = useOutletContext()
  const [filters, setFilters] = useState({ q: '', category: '', priority: '' })
  const [settings, setSettings] = useState({})

  const load = useCallback(() => {
    const p = { ...filters, month: month || '' }
    Object.keys(p).forEach(k => !p[k] && delete p[k])
    api.get('/api/expenses', { params: p }).then(r => { setExpenses(r.data); setLoading(false) }).catch(() => setLoading(false))
  }, [filters, month])

  useEffect(() => { load() }, [load])
  useEffect(() => { api.get('/api/settings').then(r => setSettings(r.data)).catch(() => {}) }, [])

  const openAdd = () => { setForm(makeEmptyForm(month)); setEditId(null); setModal('form') }
  const openEdit = (e) => { setForm({ description:e.description, amount:String(e.amount), category:e.category, priority:e.priority, date:e.date, notes:e.notes||'' }); setEditId(e.id); setModal('form') }
  
  const save = async () => {
    const body = { ...form, amount: parseFloat(form.amount) || 0 }
    if (!body.description || !body.amount) {
      toast.warning('Preencha a descrição e o valor da despesa.')
      return
    }
    try {
      if (editId) {
        await api.put(`/api/expenses/${editId}`, body)
        toast.success('Despesa atualizada com sucesso!')
      } else {
        await api.post('/api/expenses', body)
        toast.success('✅ Despesa adicionada!')
      }
      setModal(null); load()
    } catch {
      toast.error('Erro ao salvar despesa. Tente novamente.')
    }
  }

  const remove = async (id) => {
    if (!window.confirm('Excluir esta despesa?')) return
    try {
      await api.delete(`/api/expenses/${id}`)
      toast.info('Despesa removida.')
      load()
    } catch {
      toast.error('Erro ao excluir despesa.')
    }
  }

  const bulkDelete = async () => {
    if (!selected.length || !window.confirm(`Excluir ${selected.length} despesa(s)?`)) return
    try {
      await api.post('/api/expenses/bulk-delete', { ids: selected })
      toast.info(`${selected.length} despesa(s) removida(s).`)
      setSelected([]); load()
    } catch {
      toast.error('Erro ao excluir despesas.')
    }
  }

  const toggle = (id) => setSelected(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id])
  const toggleAll = () => setSelected(s => s.length === expenses.length ? [] : expenses.map(e => e.id))

  const total = expenses.reduce((a, e) => a + e.amount, 0)

  return (
    <div>
      <div className="page-header">
        <h1>🧾 Despesas</h1>
        <p>Gerencie todos os seus gastos de forma categorizada</p>
      </div>

      <div className="filters-bar">
        <div className="search-box">
          <span className="search-icon">🔍</span>
          <input placeholder="Buscar despesa..." value={filters.q} onChange={e => setFilters(f => ({...f, q: e.target.value}))} />
        </div>
        <select className="filter-select" value={filters.category} onChange={e => setFilters(f => ({...f, category: e.target.value}))}>
          <option value="">Todas as categorias</option>
          {CATEGORIES.map(c => <option key={c}>{c}</option>)}
        </select>
        <select className="filter-select" value={filters.priority} onChange={e => setFilters(f => ({...f, priority: e.target.value}))}>
          <option value="">Todas as prioridades</option>
          {PRIORITIES.map(p => <option key={p}>{p}</option>)}
        </select>

        <button className="btn btn-primary" onClick={openAdd}>+ Adicionar</button>
        {selected.length > 0 && <button className="btn btn-danger btn-sm" onClick={bulkDelete}>🗑️ Excluir {selected.length}</button>}
      </div>

      <div className="table-card">
        <div className="table-header">
          <h3>{expenses.length} despesas — Total: <span className="text-accent">{fmt(total)}</span></h3>
        </div>
        {loading ? (
          <SkeletonTable rows={5} />
        ) : expenses.length === 0 ? (
          <EmptyState
            icon="🧾"
            title="Nenhuma despesa encontrada"
            subtitle="Adicione sua primeira despesa ou ajuste os filtros de busca."
            actionLabel="+ Adicionar Despesa"
            onAction={openAdd}
            height="220px"
          />
        ) : (
          <table>
            <thead>
              <tr>
                <th><input type="checkbox" onChange={toggleAll} checked={selected.length === expenses.length && expenses.length > 0} /></th>
                <th>Descrição</th><th>Categoria</th><th>Prioridade</th><th>Data</th>
                <th style={{textAlign:'right'}}>Valor</th><th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {expenses.map(e => (
                <tr key={e.id}>
                  <td><input type="checkbox" checked={selected.includes(e.id)} onChange={() => toggle(e.id)} /></td>
                  <td style={{ color: 'var(--text)', fontWeight: 500 }}>{e.description}{e.notes && <div className="text-sm text-muted">{e.notes}</div>}</td>
                  <td>{e.category}</td>
                  <td><span className={`badge ${e.priority==='Essencial'?'badge-green':e.priority==='Importante'?'badge-amber':'badge-red'}`}>{e.priority}</span></td>
                  <td>{e.date}</td>
                  <td style={{textAlign:'right', fontWeight:600, color:'var(--text)'}}>{fmt(e.amount)}</td>
                  <td>
                    <div style={{display:'flex',gap:6}}>
                      <button className="btn-icon" onClick={() => openEdit(e)} title="Editar">✏️</button>
                      <button className="btn-icon" onClick={() => remove(e.id)} title="Excluir">🗑️</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {modal === 'form' && (
        <Modal title={editId ? '✏️ Editar Despesa' : '+ Nova Despesa'} onClose={() => setModal(null)}
          footer={<><button className="btn btn-secondary" onClick={() => setModal(null)}>Cancelar</button><button className="btn btn-primary" onClick={save}>Salvar</button></>}>
          <div className="form-grid">
            <div className="form-group" style={{gridColumn:'1/-1'}}>
              <label>Descrição *</label>
              <input className="form-control" value={form.description} onChange={e => setForm(f=>({...f,description:e.target.value}))} placeholder="Ex: Supermercado" />
            </div>
            <div className="form-group">
              <label>Valor (R$) *</label>
              <input className="form-control" type="number" step="0.01" min="0" value={form.amount} onChange={e => setForm(f=>({...f,amount:e.target.value}))} placeholder="0,00" />
            </div>
            <div className="form-group">
              <label>Data *</label>
              <input className="form-control" type="date" value={form.date} onChange={e => setForm(f=>({...f,date:e.target.value}))} style={{ colorScheme: 'dark' }} />
            </div>
            <div className="form-group">
              <label>Categoria</label>
              <select className="form-control" value={form.category} onChange={e => setForm(f=>({...f,category:e.target.value}))}>
                {CATEGORIES.map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Prioridade</label>
              <select className="form-control" value={form.priority} onChange={e => setForm(f=>({...f,priority:e.target.value}))}>
                {PRIORITIES.map(p => <option key={p}>{p}</option>)}
              </select>
            </div>
            <div className="form-group" style={{gridColumn:'1/-1'}}>
              <label>Observações</label>
              <textarea className="form-control" value={form.notes} onChange={e => setForm(f=>({...f,notes:e.target.value}))} placeholder="Opcional..." />
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
