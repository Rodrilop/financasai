import React, { createContext, useState, useEffect } from 'react';
import axios from 'axios';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const name = localStorage.getItem('user_name');
    if (token && name) {
      setUser({ token, name });
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const res = await axios.post('/api/auth/login', { email, password });
    const { access_token, name } = res.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('user_name', name);
    setUser({ token: access_token, name });
    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
  };

  const register = async (name, email, password) => {
    await axios.post('/api/auth/register', { name, email, password });
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_name');
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
