import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import App from '../App';

describe('App Layout Component', () => {
  it('should render the FinançasAI header', () => {
    render(<App />);
    const headerElement = screen.getByText(/FinançasAI/i);
    expect(headerElement).toBeDefined();
  });
});
