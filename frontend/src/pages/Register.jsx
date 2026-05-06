import React, { useState, useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

export default function Register() {
  // register() in AuthContext now handles auto-login + isNewUser flag
  const { register } = useContext(AuthContext);
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      // register() auto-logs in and sets isNewUser=true
      // ProtectedApp will render <Onboarding> instead of the dashboard
      await register(name, email, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao criar conta.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Criar Conta</h2>
        <p>Comece a gerenciar suas finanças com IA</p>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Nome completo</label>
            <input
              className="form-control"
              type="text"
              required
              autoFocus
              placeholder="Ex: João Silva"
              value={name}
              onChange={e => setName(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input
              className="form-control"
              type="email"
              required
              placeholder="seu@email.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>Senha (mín. 6 caracteres)</label>
            <input
              className="form-control"
              type="password"
              required
              minLength={6}
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
            />
          </div>
          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? 'Criando conta...' : 'Criar Conta Grátis →'}
          </button>
        </form>
        <div className="auth-links">
          <p>Já tem uma conta? <Link to="/login">Faça Login</Link></p>
        </div>
      </div>
    </div>
  );
}
