import { BrowserRouter, Routes, Route, NavLink, Navigate, Outlet } from 'react-router-dom'
import { useContext, useEffect, useState } from 'react'
import api from './api/client'
import Dashboard from './pages/Dashboard'
import Expenses from './pages/Expenses'
import Analysis from './pages/Analysis'
import Agent from './pages/Agent'
import Investments from './pages/Investments'
import Settings from './pages/Settings'
import Login from './pages/Login'
import Register from './pages/Register'
import Notifications from './pages/Notifications'
import { AuthProvider, AuthContext } from './contexts/AuthContext'
import { ToastProvider } from './contexts/ToastContext'
import ToastContainer from './components/ToastContainer'

const NAV = [
  { to: '/',            icon: '📊', label: 'Dashboard' },
  { to: '/expenses',    icon: '📋', label: 'Despesas' },
  { to: '/analysis',    icon: '📈', label: 'Análise' },
  { to: '/agent',       icon: '🤖', label: 'Assistente IA' },
  { to: '/notifications', icon: '🔔', label: 'Notificações' },
  { to: '/investments', icon: '🌱', label: 'Investimentos' },
  { to: '/settings',    icon: '⚙️', label: 'Configurações' },
]

function Sidebar({ month }) {
  const { logout, user } = useContext(AuthContext);
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
        {user && <div className="sidebar-user">👤 {user.name}</div>}
        <button onClick={logout} className="nav-item" style={{background: 'none', border: 'none', width: '100%', textAlign: 'left', cursor: 'pointer', marginTop: '1rem', color: '#ff4d4f'}}>
          <span className="icon">🚪</span> Sair
        </button>
      </div>
    </aside>
  )
}

function ProtectedApp() {
  const { user, loading } = useContext(AuthContext);
  const [month, setMonth] = useState('')

  // Re-fetch settings whenever the logged-in user changes (key dependency: user?.name)
  useEffect(() => {
    if (!user) {
      setMonth('')
      return
    }
    api.get('/api/settings').then(r => {
      setMonth(r.data.reference_month || '')
    }).catch(() => {})
  }, [user])

  if (loading) return <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh'}}>Carregando...</div>;
  if (!user) return <Navigate to="/login" replace />;

  return (
    // key={user.name} forces React to fully re-mount all child pages when user switches
    <div className="app-layout" key={user.name}>
      <div className="mobile-header">
        <span>FinançasAI</span>
      </div>
      <Sidebar month={month} />
      <main className="main-content">
        <Outlet context={{ setMonth }} />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route element={<ProtectedApp />}>
              <Route path="/"            element={<Dashboard />} />
              <Route path="/expenses"    element={<Expenses />} />
              <Route path="/analysis"    element={<Analysis />} />
              <Route path="/agent"       element={<Agent />} />
              <Route path="/notifications" element={<Notifications />} />
              <Route path="/investments" element={<Investments />} />
              <Route path="/settings"    element={<Settings />} />
            </Route>
          </Routes>
        </BrowserRouter>
        <ToastContainer />
      </AuthProvider>
    </ToastProvider>
  )
}
