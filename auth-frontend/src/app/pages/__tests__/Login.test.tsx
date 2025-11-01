/**
 * Login Page Component Tests
 * Tests UI behavior and form validation
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryProvider } from '../../providers/QueryProvider';
import { Login } from '../Login';

const renderLogin = () => {
  return render(
    <BrowserRouter>
      <QueryProvider>
        <Login />
      </QueryProvider>
    </BrowserRouter>
  );
};

describe('Login Page', () => {
  it('should render login form', () => {
    renderLogin();

    expect(screen.getByRole('heading', { name: /Login/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/seu@email.com/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/••••••••/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Entrar/i })).toBeInTheDocument();
  });

  it('should have email and password inputs with proper labels', () => {
    renderLogin();

    // Verify labels are properly associated (accessibility)
    const emailInput = screen.getByLabelText(/Email/i);
    const passwordInput = screen.getByLabelText(/Senha/i);

    expect(emailInput).toHaveAttribute('type', 'email');
    expect(emailInput).toHaveAttribute('name', 'email');
    expect(passwordInput).toHaveAttribute('type', 'password');
    expect(passwordInput).toHaveAttribute('name', 'password');
  });

  it('should show validation error for short password', async () => {
    renderLogin();

    const emailInput = screen.getByLabelText(/Email/i);
    const passwordInput = screen.getByLabelText(/Senha/i);
    const submitButton = screen.getByRole('button', { name: /Entrar/i });

    fireEvent.change(emailInput, { target: { value: 'test@test.com' } });
    fireEvent.change(passwordInput, { target: { value: '123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Senha deve ter no mínimo 8 caracteres/i)).toBeInTheDocument();
    });
  });

  it('should show link to register page', () => {
    renderLogin();

    const registerLink = screen.getByText(/Registre-se/i);
    expect(registerLink).toBeInTheDocument();
    expect(registerLink.closest('a')).toHaveAttribute('href', '/register');
  });

  it('should show link to forgot password', () => {
    renderLogin();

    const forgotLink = screen.getByText(/Esqueceu a senha/i);
    expect(forgotLink).toBeInTheDocument();
    expect(forgotLink.closest('a')).toHaveAttribute('href', '/forgot-password');
  });

  it('should show OAuth login options', () => {
    renderLogin();

    expect(screen.getByRole('button', { name: /Login com Google/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Login com GitHub/i })).toBeInTheDocument();
  });
});

