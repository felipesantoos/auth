/**
 * MFA Setup Page
 * Wizard for setting up multi-factor authentication
 */
import React, { useState } from 'react';
import { MFAService } from '../../core/services/mfa/mfaService';

const mfaService = new MFAService();

type SetupStep = 'initial' | 'scanning' | 'verifying' | 'complete';

export const MFASetup: React.FC = () => {
  const [step, setStep] = useState<SetupStep>('initial');
  const [qrCode, setQrCode] = useState('');
  const [secret, setSecret] = useState('');
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [verificationCode, setVerificationCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleStartSetup = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await mfaService.setupMFA();
      setQrCode(response.qr_code);
      setSecret(response.secret);
      setBackupCodes(response.backup_codes);
      setStep('scanning');
    } catch (err) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed to initialize MFA setup');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    setLoading(true);
    setError('');
    try {
      await mfaService.enableMFA({
        secret,
        totp_code: verificationCode,
        backup_codes: backupCodes,
      });
      setStep('complete');
    } catch (err) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Invalid verification code');
    } finally {
      setLoading(false);
    }
  };

  const copyBackupCodes = () => {
    const text = backupCodes.join('\n');
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      {/* Initial Step */}
      {step === 'initial' && (
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">Enable Multi-Factor Authentication</h2>
          <p className="text-gray-600 mb-6">
            Add an extra layer of security to your account with MFA
          </p>
          <button
            onClick={handleStartSetup}
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? 'Loading...' : 'Get Started'}
          </button>
          {error && <div className="mt-4 text-red-600">{error}</div>}
        </div>
      )}

      {/* Scanning Step */}
      {step === 'scanning' && (
        <div>
          <h2 className="text-2xl font-bold mb-4">Scan QR Code</h2>
          <p className="text-gray-600 mb-4">
            Scan this QR code with your authenticator app:
            <br />
            Google Authenticator, Authy, Microsoft Authenticator, etc.
          </p>
          
          <div className="bg-white p-4 rounded-lg border mb-4 text-center">
            <img src={qrCode} alt="MFA QR Code" className="mx-auto" style={{ maxWidth: '300px' }} />
          </div>

          <div className="bg-gray-50 p-4 rounded mb-4">
            <p className="text-sm text-gray-600 mb-2">Or enter this code manually:</p>
            <code className="text-sm font-mono bg-gray-200 px-3 py-2 rounded block text-center">
              {secret}
            </code>
          </div>

          <button
            onClick={() => setStep('verifying')}
            className="w-full bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
          >
            Next: Verify Code
          </button>
        </div>
      )}

      {/* Verifying Step */}
      {step === 'verifying' && (
        <div>
          <h2 className="text-2xl font-bold mb-4">Verify Code</h2>
          <p className="text-gray-600 mb-4">
            Enter the 6-digit code from your authenticator app
          </p>

          <input
            type="text"
            value={verificationCode}
            onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
            placeholder="000000"
            className="w-full px-4 py-3 border rounded mb-4 text-center text-2xl tracking-widest font-mono"
            maxLength={6}
            autoFocus
          />

          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded mb-4 text-sm">
              {error}
            </div>
          )}

          <button
            onClick={handleVerify}
            disabled={loading || verificationCode.length !== 6}
            className="w-full bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? 'Verifying...' : 'Verify and Enable MFA'}
          </button>

          <button
            onClick={() => setStep('scanning')}
            className="w-full mt-3 text-blue-600 hover:text-blue-800"
          >
            ← Back to QR Code
          </button>
        </div>
      )}

      {/* Complete Step */}
      {step === 'complete' && (
        <div>
          <div className="text-center mb-6">
            <div className="text-green-600 text-5xl mb-2">✓</div>
            <h2 className="text-2xl font-bold text-green-600">MFA Enabled Successfully!</h2>
          </div>
          
          <div className="bg-yellow-50 border-2 border-yellow-300 p-6 rounded-lg mb-4">
            <p className="font-bold text-lg mb-2">⚠️ Save Your Backup Codes</p>
            <p className="text-sm text-gray-700 mb-4">
              Store these backup codes in a safe place. You can use them to login if you lose your device.
              Each code can only be used once.
            </p>
            
            <div className="grid grid-cols-2 gap-2 bg-white p-4 rounded border">
              {backupCodes.map((code, i) => (
                <code key={i} className="text-sm font-mono bg-gray-100 px-3 py-2 rounded text-center">
                  {code}
                </code>
              ))}
            </div>

            <button
              onClick={copyBackupCodes}
              className="mt-4 w-full text-sm bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              📋 Copy to Clipboard
            </button>
          </div>

          <div className="bg-blue-50 p-4 rounded mb-4 text-sm text-gray-700">
            <p className="font-bold mb-1">Important:</p>
            <ul className="list-disc ml-5 space-y-1">
              <li>Each backup code can only be used once</li>
              <li>Store codes securely (password manager recommended)</li>
              <li>You can regenerate new codes from security settings</li>
              <li>Used codes cannot be reused</li>
            </ul>
          </div>

          <button
            onClick={() => window.location.href = '/dashboard'}
            className="w-full bg-green-600 text-white px-6 py-3 rounded hover:bg-green-700"
          >
            Done - Go to Dashboard
          </button>
        </div>
      )}
    </div>
  );
};

