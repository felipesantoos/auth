/**
 * Login Page
 * User login form
 */
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [clientId, setClientId] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(email, password, clientId || undefined);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '100px auto', padding: '20px' }}>
      <h1>Login</h1>
      {error && <div style={{ color: 'red', marginBottom: '10px' }}>{error}</div>}
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <label>
            Client ID (optional):
            <input
              type="text"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              placeholder="client_id or leave empty"
              style={{ width: '100%', padding: '8px', marginTop: '5px' }}
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
              style={{ width: '100%', padding: '8px', marginTop: '5px' }}
            />
          </label>
        </div>
        <div style={{ marginBottom: '15px' }}>
          <label>
            Password:
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{ width: '100%', padding: '8px', marginTop: '5px' }}
            />
          </label>
        </div>
        <button type="submit" disabled={isLoading} style={{ width: '100%', padding: '10px' }}>
          {isLoading ? 'Logging in...' : 'Login'}
        </button>
      </form>
      <p style={{ marginTop: '15px', textAlign: 'center' }}>
        <Link to="/forgot-password">Forgot password?</Link>
      </p>
      <p style={{ marginTop: '15px', textAlign: 'center' }}>
        Don't have an account? <Link to="/register">Register</Link>
      </p>
      
      {/* OAuth Login Buttons */}
      <div style={{ marginTop: '30px', borderTop: '1px solid #ddd', paddingTop: '20px' }}>
        <p style={{ textAlign: 'center', marginBottom: '15px', color: '#666' }}>Or login with:</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <button
            type="button"
            onClick={() => {
              const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
              if (clientId) {
                window.location.href = `${apiUrl}/api/auth/oauth/google?client_id=${encodeURIComponent(clientId)}`;
              } else {
                // Try to get client_id from localStorage
                const storedClientId = localStorage.getItem('client_id');
                if (storedClientId) {
                  window.location.href = `${apiUrl}/api/auth/oauth/google?client_id=${encodeURIComponent(storedClientId)}`;
                } else {
                  alert('Please enter a Client ID first');
                }
              }
            }}
            style={{
              width: '100%',
              padding: '10px',
              background: '#4285f4',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            Login with Google
          </button>
          <button
            type="button"
            onClick={() => {
              const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
              if (clientId) {
                window.location.href = `${apiUrl}/api/auth/oauth/github?client_id=${encodeURIComponent(clientId)}`;
              } else {
                // Try to get client_id from localStorage
                const storedClientId = localStorage.getItem('client_id');
                if (storedClientId) {
                  window.location.href = `${apiUrl}/api/auth/oauth/github?client_id=${encodeURIComponent(storedClientId)}`;
                } else {
                  alert('Please enter a Client ID first');
                }
              }
            }}
            style={{
              width: '100%',
              padding: '10px',
              background: '#333',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            Login with GitHub
          </button>
        </div>
      </div>
    </div>
  );
};

