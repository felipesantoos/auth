/**
 * OAuth Callback Page
 * Handles OAuth provider redirects and stores tokens
 */
import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

export const OAuthCallback: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Get tokens from URL query params
        const accessToken = searchParams.get('access_token');
        const refreshToken = searchParams.get('refresh_token');
        const tokenType = searchParams.get('token_type');

        if (!accessToken || !refreshToken) {
          setError('OAuth authentication failed: Missing tokens');
          setLoading(false);
          setTimeout(() => navigate('/login'), 3000);
          return;
        }

        // Store tokens
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
        if (tokenType) {
          localStorage.setItem('token_type', tokenType);
        }

        // Fetch user data using the access token
        const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
        const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch user data');
        }

        const user = await response.json();

        // Store user data
        localStorage.setItem('user', JSON.stringify(user));
        
        if (user.client_id) {
          localStorage.setItem('client_id', user.client_id);
        }

        // Redirect to dashboard
        navigate('/dashboard');
      } catch (err: any) {
        console.error('OAuth callback error:', err);
        setError(err.message || 'OAuth authentication failed');
        setLoading(false);
        setTimeout(() => navigate('/login'), 3000);
      }
    };

    handleCallback();
  }, [searchParams, navigate]);

  if (loading) {
    return (
      <div style={{ maxWidth: '400px', margin: '100px auto', padding: '20px', textAlign: 'center' }}>
        <h2>Completing authentication...</h2>
        <p>Please wait while we complete your login.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ maxWidth: '400px', margin: '100px auto', padding: '20px', textAlign: 'center' }}>
        <h2>Authentication Error</h2>
        <p style={{ color: 'red' }}>{error}</p>
        <p>Redirecting to login page...</p>
      </div>
    );
  }

  return null;
};

