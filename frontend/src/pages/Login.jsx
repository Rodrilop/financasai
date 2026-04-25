import React, { useState, useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

export default function Login() {
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError('Email ou senha incorretos.');
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Bem-vindo ao FinançasAI</h2>
        <p>Faça login para continuar</p>
        
        {error && <div className="auth-error">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email</label>
            <input 
              type="email" 
              required 
              value={email} 
              onChange={e => setEmail(e.target.value)} 
            />
          </div>
          <div className="form-group">
            <label>Senha</label>
            <input 
              type="password" 
              required 
              value={password} 
              onChange={e => setPassword(e.target.value)} 
            />
          </div>
          <button type="submit" className="auth-btn">Entrar</button>
        </form>
        <div className="auth-links">
          <p>Não tem uma conta? <Link to="/register">Cadastre-se</Link></p>
        </div>
      </div>
    </div>
  );
}
