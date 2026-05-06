import { BrowserRouter, Routes, Route, NavLink, Navigate, Outlet } from 'react-router-dom'
import { useContext, useEffect, useState, useMemo } from 'react'
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
import Onboarding from './pages/Onboarding'
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
        {user && <div className="sidebar-user">👤 {user.name}</div>}
        <button onClick={logout} className="nav-item" style={{background: 'none', border: 'none', width: '100%', textAlign: 'left', cursor: 'pointer', marginTop: '1rem', color: '#ff4d4f'}}>
          <span className="icon">🚪</span> Sair
        </button>
      </div>
    </aside>
  )
}

function MonthSelector({ month, setMonth }) {
  const handlePrev = () => {
    if (!month) return;
    const [y, m] = month.split('-');
    let date = new Date(y, parseInt(m) - 2);
    setMonth(`${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`);
  }
  const handleNext = () => {
    if (!month) return;
    const [y, m] = month.split('-');
    let date = new Date(y, parseInt(m));
    setMonth(`${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`);
  }

  const monthLabel = useMemo(() => {
    if (!month) return '';
    const [y, m] = month.split('-');
    const date = new Date(y, parseInt(m) - 1);
    const mName = date.toLocaleString('pt-BR', { month: 'long' });
    return `${mName.charAt(0).toUpperCase() + mName.slice(1)} ${y}`;
  }, [month]);

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1rem', padding: '1rem', background: 'var(--bg-card)', borderBottom: '1px solid var(--border)', position: 'sticky', top: 0, zIndex: 10 }}>
      <button onClick={handlePrev} className="btn btn-secondary btn-sm" style={{ padding: '4px 12px' }}>&lt;</button>
      <span style={{ fontWeight: 600, minWidth: 120, textAlign: 'center' }}>📅 {monthLabel}</span>
      <button onClick={handleNext} className="btn btn-secondary btn-sm" style={{ padding: '4px 12px' }}>&gt;</button>
    </div>
  )
}

function ProtectedApp() {
  const { user, loading, isNewUser, completeOnboarding } = useContext(AuthContext);
  const currentYm = new Date().toISOString().slice(0, 7);
  const [month, setMonth] = useState(currentYm)

  useEffect(() => {
    if (!user) setMonth(currentYm)
  }, [user])

  if (loading) return <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh'}}>Carregando...</div>;
  if (!user) return <Navigate to="/login" replace />;

  // Show onboarding for new users before the main app
  if (isNewUser) {
    return <Onboarding userName={user.name} onComplete={completeOnboarding} />
  }

  return (
    // key={user.name} forces React to fully re-mount all child pages when user switches
    <div className="app-layout" key={user.name}>
      <div className="mobile-header">
        <span>FinançasAI</span>
      </div>
      <Sidebar />
      <main className="main-content" style={{ padding: 0 }}>
        <MonthSelector month={month} setMonth={setMonth} />
        <div style={{ padding: '1.5rem' }}>
          <Outlet context={{ month, setMonth }} />
        </div>
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
