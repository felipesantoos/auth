/**
 * Reset Password Page
 * Reset password with token from email
 */
import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { AuthService } from '../../core/services/auth/authService';
import { AuthRepository } from '../../core/repositories/auth_repository';

export const ResetPassword: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [clientId, setClientId] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const authRepository = new AuthRepository();
  const authService = new AuthService(authRepository);

  useEffect(() => {
    // Get token from URL query params
    const token = searchParams.get('token');
    const client_id = searchParams.get('client_id');
    if (token) {
      setResetToken(token);
    }
    if (client_id) {
      setClientId(client_id);
    }
  }, [searchParams]);

  const validatePassword = (password: string): boolean => {
    if (password.length < 8) {
      setPasswordError('Password must be at least 8 characters');
      return false;
    }
    if (!/[A-Z]/.test(password)) {
      setPasswordError('Password must contain at least one uppercase letter');
      return false;
    }
    if (!/[a-z]/.test(password)) {
      setPasswordError('Password must contain at least one lowercase letter');
      return false;
    }
    if (!/[0-9]/.test(password)) {
      setPasswordError('Password must contain at least one number');
      return false;
    }
    setPasswordError('');
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    
    if (!resetToken) {
      setError('Reset token is required');
      return;
    }

    if (!validatePassword(newPassword)) {
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);

    try {
      const result = await authService.resetPassword({
        reset_token: resetToken,
        new_password: newPassword,
        client_id: clientId || undefined,
      });
      setMessage(result.message);
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reset password');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '100px auto', padding: '20px' }}>
      <h1>Reset Password</h1>
      {error && <div style={{ color: 'red', marginBottom: '10px', padding: '10px', background: '#fee', borderRadius: '4px' }}>{error}</div>}
      {message && <div style={{ color: 'green', marginBottom: '10px', padding: '10px', background: '#efe', borderRadius: '4px' }}>{message}</div>}
      <form onSubmit={handleSubmit}>
        {!resetToken && (
          <div style={{ marginBottom: '15px' }}>
            <label>
              Reset Token (from email):
              <input
                type="text"
                value={resetToken}
                onChange={(e) => setResetToken(e.target.value)}
                required
                placeholder="Paste reset token from email"
                style={{ width: '100%', padding: '8px', marginTop: '5px', boxSizing: 'border-box' }}
              />
            </label>
          </div>
        )}
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
            New Password:
            <input
              type="password"
              value={newPassword}
              onChange={(e) => {
                setNewPassword(e.target.value);
                if (e.target.value) validatePassword(e.target.value);
              }}
              required
              style={{ width: '100%', padding: '8px', marginTop: '5px', boxSizing: 'border-box' }}
            />
          </label>
          {passwordError && <div style={{ color: 'red', fontSize: '12px', marginTop: '5px' }}>{passwordError}</div>}
          <p style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
            Min 8 characters with uppercase, lowercase, and number
          </p>
        </div>
        <div style={{ marginBottom: '15px' }}>
          <label>
            Confirm Password:
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              style={{ width: '100%', padding: '8px', marginTop: '5px', boxSizing: 'border-box' }}
            />
          </label>
        </div>
        <button type="submit" disabled={isLoading || !resetToken} style={{ width: '100%', padding: '10px', marginBottom: '15px' }}>
          {isLoading ? 'Resetting...' : 'Reset Password'}
        </button>
      </form>
      <p style={{ marginTop: '15px', textAlign: 'center' }}>
        <Link to="/login">Back to Login</Link>
      </p>
    </div>
  );
};

