import React, { createContext, useState, useEffect } from 'react';
import api from '../api/client';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isNewUser, setIsNewUser] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const name = localStorage.getItem('user_name');
    const newFlag = localStorage.getItem('is_new_user') === 'true';
    if (token && name) {
      setUser({ token, name });
      setIsNewUser(newFlag);
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const res = await api.post('/api/auth/login', { email, password });
    const { access_token, name } = res.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('user_name', name);
    localStorage.removeItem('is_new_user');
    setIsNewUser(false);
    setUser({ token: access_token, name });
  };

  const register = async (name, email, password) => {
    await api.post('/api/auth/register', { name, email, password });
    // Auto-login after register and mark as new user
    const res = await api.post('/api/auth/login', { email, password });
    const { access_token } = res.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('user_name', name);
    localStorage.setItem('is_new_user', 'true');
    setIsNewUser(true);
    setUser({ token: access_token, name });
  };

  const completeOnboarding = () => {
    localStorage.removeItem('is_new_user');
    setIsNewUser(false);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_name');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading, isNewUser, completeOnboarding }}>
      {children}
    </AuthContext.Provider>
  );
};
