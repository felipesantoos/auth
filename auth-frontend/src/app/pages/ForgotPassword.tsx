/**
 * Forgot Password Page
 * Request password reset
 */
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { AuthService } from '../../core/services/auth/authService';
import { AuthRepository } from '../../core/repositories/auth_repository';

export const ForgotPassword: React.FC = () => {
  const [email, setEmail] = useState('');
  const [clientId, setClientId] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const authRepository = new AuthRepository();
  const authService = new AuthService(authRepository);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setIsLoading(true);

    try {
      const result = await authService.forgotPassword({
        email,
        client_id: clientId || undefined,
      });
      setMessage(result.message);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send password reset email');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '100px auto', padding: '20px' }}>
      <h1>Forgot Password</h1>
      {error && <div style={{ color: 'red', marginBottom: '10px', padding: '10px', background: '#fee', borderRadius: '4px' }}>{error}</div>}
      {message && <div style={{ color: 'green', marginBottom: '10px', padding: '10px', background: '#efe', borderRadius: '4px' }}>{message}</div>}
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <label>
            Client ID (optional):
            <input
              type="text"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              placeholder="client_id or leave empty"
              style={{ width: '100%', padding: '8px', marginTop: '5px', boxSizing: 'border-box' }}
            />
          </label>
        </div>
        <div style={{ marginBottom: '15px' }}>
          <label>
            Email:
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{ width: '100%', padding: '8px', marginTop: '5px', boxSizing: 'border-box' }}
            />
          </label>
        </div>
        <button type="submit" disabled={isLoading} style={{ width: '100%', padding: '10px', marginBottom: '15px' }}>
          {isLoading ? 'Sending...' : 'Send Reset Link'}
        </button>
      </form>
      <p style={{ marginTop: '15px', textAlign: 'center' }}>
        <Link to="/login">Back to Login</Link>
      </p>
    </div>
  );
};

