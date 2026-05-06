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
    const isPro = localStorage.getItem('is_pro') === 'true';
    const newFlag = localStorage.getItem('is_new_user') === 'true';
    if (token && name) {
      setUser({ token, name, isPro });
      setIsNewUser(newFlag);
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const res = await api.post('/api/auth/login', { email, password });
    const { access_token, name, is_pro } = res.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('user_name', name);
    localStorage.setItem('is_pro', is_pro ? 'true' : 'false');
    localStorage.removeItem('is_new_user');
    setIsNewUser(false);
    setUser({ token: access_token, name, isPro: !!is_pro });
  };

  const register = async (name, email, password) => {
    await api.post('/api/auth/register', { name, email, password });
    // Auto-login after register and mark as new user
    const res = await api.post('/api/auth/login', { email, password });
    const { access_token, is_pro } = res.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('user_name', name);
    localStorage.setItem('is_pro', is_pro ? 'true' : 'false');
    localStorage.setItem('is_new_user', 'true');
    setIsNewUser(true);
    setUser({ token: access_token, name, isPro: !!is_pro });
  };

  const completeOnboarding = () => {
    localStorage.removeItem('is_new_user');
    setIsNewUser(false);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_name');
    localStorage.removeItem('is_pro');
    localStorage.removeItem('is_new_user');
    setUser(null);
  };

  const refreshProfile = async () => {
    try {
      const res = await api.get('/api/profile');
      const { name, is_pro } = res.data;
      localStorage.setItem('user_name', name);
      localStorage.setItem('is_pro', is_pro ? 'true' : 'false');
      setUser(prev => ({ ...prev, name, isPro: !!is_pro }));
    } catch (err) {
      console.error('Error refreshing profile:', err);
    }
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading, isNewUser, completeOnboarding, refreshProfile }}>
      {children}
    </AuthContext.Provider>
  );
};
