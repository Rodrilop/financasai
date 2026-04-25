import React, { useState, useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

export default function Register() {
  const { register, login } = useContext(AuthContext);
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await register(name, email, password);
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao criar conta.');
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Criar Conta</h2>
        <p>Comece a gerenciar suas finanças</p>
        
        {error && <div className="auth-error">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Nome</label>
            <input 
              type="text" 
              required 
              value={name} 
              onChange={e => setName(e.target.value)} 
            />
          </div>
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
            <label>Senha (mín. 6 caracteres)</label>
            <input 
              type="password" 
              required 
              minLength={6}
              value={password} 
              onChange={e => setPassword(e.target.value)} 
            />
          </div>
          <button type="submit" className="auth-btn">Cadastrar</button>
        </form>
        <div className="auth-links">
          <p>Já tem uma conta? <Link to="/login">Faça Login</Link></p>
        </div>
      </div>
    </div>
  );
}
