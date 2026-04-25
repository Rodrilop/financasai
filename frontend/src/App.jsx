import { BrowserRouter, Routes, Route, NavLink, Navigate, Outlet } from 'react-router-dom'
import { useContext, useEffect, useState } from 'react'
import axios from 'axios'
import Dashboard from './pages/Dashboard'
import Expenses from './pages/Expenses'
import Analysis from './pages/Analysis'
import Investments from './pages/Investments'
import Settings from './pages/Settings'
import Login from './pages/Login'
import Register from './pages/Register'
import { AuthProvider, AuthContext } from './contexts/AuthContext'

const NAV = [
  { to: '/',            icon: '🏠', label: 'Dashboard' },
  { to: '/expenses',    icon: '🧾', label: 'Despesas' },
  { to: '/analysis',    icon: '📊', label: 'Análise' },
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
        <button onClick={logout} className="nav-item" style={{background: 'none', border: 'none', width: '100%', textAlign: 'left', cursor: 'pointer', marginTop: '1rem', color: '#ff4d4f'}}>
          <span className="icon">🚪</span> Sair
        </button>
      </div>
    </aside>
  )
}

function ProtectedLayout({ month }) {
  const { user, loading } = useContext(AuthContext);

  if (loading) return <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh'}}>Carregando...</div>;
  if (!user) return <Navigate to="/login" replace />;

  return (
    <div className="app-layout">
      <div className="mobile-header">
        <span>FinançasAI</span>
      </div>
      <Sidebar month={month} />
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  const [month, setMonth] = useState('')

  useEffect(() => {
    // Intercepta respostas 401 para limpar o localStorage
    const interceptor = axios.interceptors.response.use(
      response => response,
      error => {
        if (error.response?.status === 401) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('user_name');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );

    const token = localStorage.getItem('access_token');
    if (token) {
        axios.get('/api/settings').then(r => {
          setMonth(r.data.reference_month || '')
        }).catch(() => {})
    }

    return () => axios.interceptors.response.eject(interceptor);
  }, [])

  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route element={<ProtectedLayout month={month} />}>
            <Route path="/"            element={<Dashboard />} />
            <Route path="/expenses"    element={<Expenses />} />
            <Route path="/analysis"    element={<Analysis />} />
            <Route path="/investments" element={<Investments />} />
            <Route path="/settings"    element={<Settings onMonthChange={setMonth} />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
