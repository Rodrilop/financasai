import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Expenses from './pages/Expenses'
import Analysis from './pages/Analysis'
import Investments from './pages/Investments'
import Settings from './pages/Settings'
import { useEffect, useState } from 'react'
import axios from 'axios'

const NAV = [
  { to: '/',            icon: '🏠', label: 'Dashboard' },
  { to: '/expenses',    icon: '🧾', label: 'Despesas' },
  { to: '/analysis',    icon: '📊', label: 'Análise' },
  { to: '/investments', icon: '🌱', label: 'Investimentos' },
  { to: '/settings',    icon: '⚙️', label: 'Configurações' },
]

function Sidebar({ month }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div>
          <span>FinançasAI</span>
          <small>Assistente financeiro pessoal</small>
        </div>
      </div>
      <nav className="sidebar-nav">
        {NAV.map(n => (
          <NavLink key={n.to} to={n.to} end={n.to === '/'} className={({ isActive }) => 'nav-item' + (isActive ? ' active' : '')}>
            <span className="icon">{n.icon}</span>
            {n.label}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-footer">
        <div className="sidebar-month">📅 {month || 'Sem mês definido'}</div>
      </div>
    </aside>
  )
}

export default function App() {
  const [month, setMonth] = useState('')

  useEffect(() => {
    axios.get('/api/settings').then(r => {
      setMonth(r.data.reference_month || '')
    }).catch(() => {})
  }, [])

  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar month={month} />
        <main className="main-content">
          <Routes>
            <Route path="/"            element={<Dashboard />} />
            <Route path="/expenses"    element={<Expenses />} />
            <Route path="/analysis"    element={<Analysis />} />
            <Route path="/investments" element={<Investments />} />
            <Route path="/settings"    element={<Settings onMonthChange={setMonth} />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
