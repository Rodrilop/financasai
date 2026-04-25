import { useEffect, useState, useCallback } from 'react'
import api from '../api/client'
import Modal from '../components/Modal'

const CATEGORIES = ['Moradia','AlimentaÃ§Ã£o','Transporte','SaÃºde','EducaÃ§Ã£o','Lazer','Assinaturas','VestuÃ¡rio','Pets','Outros']
const PRIORITIES = ['Essencial','Importante','Opcional']

function fmt(v) { return 'R$ ' + Number(v || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 }) }

const EMPTY_FORM = { description: '', amount: '', category: 'AlimentaÃ§Ã£o', priority: 'Essencial', date: new Date().toISOString().slice(0,10), notes: '' }

export default function Expenses() {
  const [expenses, setExpenses] = useState([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(null) // null | 'add' | 'edit'
  const [form, setForm] = useState(EMPTY_FORM)
  const [editId, setEditId] = useState(null)
  const [selected, setSelected] = useState([])
  const [filters, setFilters] = useState({ q: '', category: '', priority: '', month: '' })
  const [settings, setSettings] = useState({})

  const load = useCallback(() => {
    const p = { ...filters }
    Object.keys(p).forEach(k => !p[k] && delete p[k])
    api.get('/api/expenses', { params: p }).then(r => { setExpenses(r.data); setLoading(false) }).catch(() => setLoading(false))
  }, [filters])

  useEffect(() => { load() }, [load])
  useEffect(() => { api.get('/api/settings').then(r => setSettings(r.data)).catch(() => {}) }, [])

  const openAdd = () => { setForm({...EMPTY_FORM, date: new Date().toISOString().slice(0,10)}); setEditId(null); setModal('form') }
  const openEdit = (e) => { setForm({ description:e.description, amount:String(e.amount), category:e.category, priority:e.priority, date:e.date, notes:e.notes||'' }); setEditId(e.id); setModal('form') }
  
  const save = async () => {
    const body = { ...form, amount: parseFloat(form.amount) || 0 }
    if (!body.description || !body.amount) return alert('Preencha descriÃ§Ã£o e valor.')
    if (editId) await api.put(`/api/expenses/${editId}`, body)
    else await api.post('/api/expenses', body)
    setModal(null); load()
  }

  const remove = async (id) => {
    if (!confirm('Excluir esta despesa?')) return
    await api.delete(`/api/expenses/${id}`)
    load()
  }

  const bulkDelete = async () => {
    if (!selected.length || !confirm(`Excluir ${selected.length} despesas?`)) return
    await api.post('/api/expenses/bulk-delete', { ids: selected })
    setSelected([]); load()
  }

  const toggle = (id) => setSelected(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id])
  const toggleAll = () => setSelected(s => s.length === expenses.length ? [] : expenses.map(e => e.id))

  const total = expenses.reduce((a, e) => a + e.amount, 0)

  return (
    <div>
      <div className="page-header">
        <h1>ðŸ§¾ Despesas</h1>
        <p>Gerencie todos os seus gastos de forma categorizada</p>
      </div>

      <div className="filters-bar">
        <div className="search-box">
          <span className="search-icon">ðŸ”</span>
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
        <input type="month" className="filter-select" value={filters.month} onChange={e => setFilters(f => ({...f, month: e.target.value}))} style={{ colorScheme: 'dark' }} />
        <button className="btn btn-primary" onClick={openAdd}>+ Adicionar</button>
        {selected.length > 0 && <button className="btn btn-danger btn-sm" onClick={bulkDelete}>ðŸ—‘ï¸ Excluir {selected.length}</button>}
      </div>

      <div className="table-card">
        <div className="table-header">
          <h3>{expenses.length} despesas â€” Total: <span className="text-accent">{fmt(total)}</span></h3>
        </div>
        {loading ? <div className="loading"><div className="spinner" /></div> : expenses.length === 0 ? (
          <div className="empty"><div className="icon">ðŸ“­</div><p>Nenhuma despesa encontrada.</p></div>
        ) : (
          <table>
            <thead>
              <tr>
                <th><input type="checkbox" onChange={toggleAll} checked={selected.length === expenses.length && expenses.length > 0} /></th>
                <th>DescriÃ§Ã£o</th><th>Categoria</th><th>Prioridade</th><th>Data</th>
                <th style={{textAlign:'right'}}>Valor</th><th>AÃ§Ãµes</th>
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
                      <button className="btn-icon" onClick={() => openEdit(e)} title="Editar">âœï¸</button>
                      <button className="btn-icon" onClick={() => remove(e.id)} title="Excluir">ðŸ—‘ï¸</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {modal === 'form' && (
        <Modal title={editId ? 'âœï¸ Editar Despesa' : '+ Nova Despesa'} onClose={() => setModal(null)}
          footer={<><button className="btn btn-secondary" onClick={() => setModal(null)}>Cancelar</button><button className="btn btn-primary" onClick={save}>Salvar</button></>}>
          <div className="form-grid">
            <div className="form-group" style={{gridColumn:'1/-1'}}>
              <label>DescriÃ§Ã£o *</label>
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
              <label>ObservaÃ§Ãµes</label>
              <textarea className="form-control" value={form.notes} onChange={e => setForm(f=>({...f,notes:e.target.value}))} placeholder="Opcional..." />
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}

