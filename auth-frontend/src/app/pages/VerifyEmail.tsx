/**
 * Verify Email Page
 * Handles email verification from email link
 */
import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { EmailVerificationService } from '../../core/services/email/emailVerificationService';

const emailService = new EmailVerificationService();

type VerificationStatus = 'verifying' | 'success' | 'error';

export const VerifyEmail: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<VerificationStatus>('verifying');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const verifyEmail = async () => {
      const token = searchParams.get('token');
      const userId = searchParams.get('user_id');
      const clientId = searchParams.get('client_id') || localStorage.getItem('client_id') || undefined;
      
      if (!token || !userId) {
        setStatus('error');
        setMessage('Invalid verification link. Missing required parameters.');
        return;
      }

      try {
        await emailService.verifyEmail({
          user_id: userId,
          token,
          client_id: clientId,
        });
        
        setStatus('success');
        setMessage('Email verified successfully! Redirecting to login...');
        
        // Redirect to login after 3 seconds
        setTimeout(() => navigate('/login'), 3000);
      } catch (error: any) {
        setStatus('error');
        setMessage(error.response?.data?.detail || 'Verification failed. The link may be invalid or expired.');
      }
    };

    verifyEmail();
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-md">
        {/* Verifying State */}
        {status === 'verifying' && (
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Verifying Your Email...</h2>
            <p className="text-gray-600">Please wait while we verify your email address.</p>
          </div>
        )}
        
        {/* Success State */}
        {status === 'success' && (
          <div className="text-center">
            <div className="text-green-600 text-6xl mb-4">✓</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Email Verified!</h2>
            <p className="text-gray-600">{message}</p>
            <div className="mt-6">
              <button
                onClick={() => navigate('/login')}
                className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
              >
                Go to Login
              </button>
            </div>
          </div>
        )}
        
        {/* Error State */}
        {status === 'error' && (
          <div className="text-center">
            <div className="text-red-600 text-6xl mb-4">✕</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Verification Failed</h2>
            <p className="text-gray-600 mb-6">{message}</p>
            <div className="space-y-3">
              <button
                onClick={() => navigate('/resend-verification')}
                className="w-full bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
              >
                Resend Verification Email
              </button>
              <button
                onClick={() => navigate('/login')}
                className="w-full border border-gray-300 text-gray-700 px-6 py-2 rounded hover:bg-gray-50"
              >
                Back to Login
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

