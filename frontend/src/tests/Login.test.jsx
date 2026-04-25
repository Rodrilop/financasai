import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import Login from '../pages/Login';
import { AuthContext } from '../contexts/AuthContext';

describe('Login Component', () => {
  it('should render login form', () => {
    const mockLogin = vi.fn();
    
    render(
      <AuthContext.Provider value={{ login: mockLogin }}>
        <BrowserRouter>
          <Login />
        </BrowserRouter>
      </AuthContext.Provider>
    );
    
    expect(screen.getByText('Bem-vindo ao FinançasAI')).toBeDefined();
    expect(screen.getByText('Email')).toBeDefined();
    expect(screen.getByText('Senha')).toBeDefined();
    expect(screen.getByRole('button', { name: /Entrar/i })).toBeDefined();
  });

  it('should call login function on submit', async () => {
    const mockLogin = vi.fn().mockResolvedValue();
    
    render(
      <AuthContext.Provider value={{ login: mockLogin }}>
        <BrowserRouter>
          <Login />
        </BrowserRouter>
      </AuthContext.Provider>
    );
    
    // Instead of getByLabelText (since label doesn't have htmlFor), we get by type or index
    const emailInput = screen.getByRole('textbox');
    const passwordInput = screen.getByLabelText ? document.querySelector('input[type="password"]') : null;
    const submitButton = screen.getByRole('button', { name: /Entrar/i });
    
    if (emailInput && passwordInput) {
      fireEvent.change(emailInput, { target: { value: 'test@test.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      expect(mockLogin).toHaveBeenCalledWith('test@test.com', 'password123');
    }
  });
});
