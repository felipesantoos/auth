/**
 * MFASetup Page Tests
 * Component tests for the MFA setup wizard
 * 
 * Tests:
 * - Wizard step progression
 * - QR code display
 * - Code verification
 * - Error handling
 * - Success state
 * - Backup codes display
 * 
 * Compliance: 08e-frontend-testing.md Section 3.5
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { MFASetup } from '../MFASetup';

// Mock MFAService instance
const mockMFAService = {
  setupMFA: vi.fn(),
  enableMFA: vi.fn(),
  verifyMFA: vi.fn(),
  disableMFA: vi.fn(),
};

vi.mock('../../../core/services/mfa/mfaService', () => ({
  MFAService: vi.fn().mockImplementation(() => mockMFAService),
}));

describe('MFASetup Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render initial setup step', () => {
    render(<MFASetup />);

    expect(screen.getByText('Enable Multi-Factor Authentication')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /get started/i })).toBeInTheDocument();
  });

  it('should start MFA setup and display QR code', async () => {
    const user = userEvent.setup();
    
    const mockSetupResponse = {
      qr_code: 'data:image/png;base64,mock-qr-code',
      secret: 'MOCK-SECRET-KEY',
      backup_codes: ['CODE1', 'CODE2', 'CODE3'],
    };

    mockMFAService.setupMFA.mockResolvedValue(mockSetupResponse);

    render(<MFASetup />);

    // Click get started
    await user.click(screen.getByRole('button', { name: /get started/i }));

    // Should call setupMFA
    await waitFor(() => {
      expect(mockMFAService.setupMFA).toHaveBeenCalled();
    });

    // Should show QR code step
    await waitFor(() => {
      expect(screen.getByText('Scan QR Code')).toBeInTheDocument();
    });

    // Should display QR code
    const qrImage = screen.getByAltText('MFA QR Code');
    expect(qrImage).toBeInTheDocument();
    expect(qrImage).toHaveAttribute('src', mockSetupResponse.qr_code);

    // Should display secret
    expect(screen.getByText(mockSetupResponse.secret)).toBeInTheDocument();
  });

  it('should show loading state during setup initialization', async () => {
    const user = userEvent.setup();
    
    mockMFAService.setupMFA.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({
        qr_code: 'mock-qr',
        secret: 'SECRET',
        backup_codes: ['CODE1'],
      }), 100))
    );

    render(<MFASetup />);

    const button = screen.getByRole('button', { name: /get started/i });
    await user.click(button);

    // Should show loading text
    await waitFor(() => {
      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    // Button should be disabled
    expect(button).toBeDisabled();
  });

  it('should handle setup initialization error', async () => {
    const user = userEvent.setup();
    
    mockMFAService.setupMFA.mockRejectedValue({
      response: {
        data: {
          detail: 'Failed to initialize MFA',
        },
      },
    });

    render(<MFASetup />);

    await user.click(screen.getByRole('button', { name: /get started/i }));

    await waitFor(() => {
      expect(screen.getByText(/failed to initialize/i)).toBeInTheDocument();
    });
  });

  it('should progress to verification step', async () => {
    const user = userEvent.setup();
    
    mockMFAService.setupMFA.mockResolvedValue({
      qr_code: 'mock-qr',
      secret: 'SECRET',
      backup_codes: ['CODE1'],
    });

    render(<MFASetup />);

    // Start setup
    await user.click(screen.getByRole('button', { name: /get started/i }));

    // Wait for QR code step
    await waitFor(() => {
      expect(screen.getByText('Scan QR Code')).toBeInTheDocument();
    });

    // Click next
    await user.click(screen.getByRole('button', { name: /next.*verify/i }));

    // Should show verification step
    expect(screen.getByText('Verify Code')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/6-digit code/i)).toBeInTheDocument();
  });

  it('should verify MFA code successfully', async () => {
    const user = userEvent.setup();
    
    mockMFAService.setupMFA.mockResolvedValue({
      qr_code: 'mock-qr',
      secret: 'TEST-SECRET',
      backup_codes: ['CODE1', 'CODE2'],
    });

    mockMFAService.enableMFA.mockResolvedValue({ success: true });

    render(<MFASetup />);

    // Navigate to verification step
    await user.click(screen.getByRole('button', { name: /get started/i }));
    await waitFor(() => expect(screen.getByText('Scan QR Code')).toBeInTheDocument());
    await user.click(screen.getByRole('button', { name: /next.*verify/i }));

    // Enter verification code
    const codeInput = screen.getByPlaceholderText(/6-digit code/i);
    await user.type(codeInput, '123456');

    // Submit
    await user.click(screen.getByRole('button', { name: /verify.*enable/i }));

    // Should call enableMFA with correct params
    await waitFor(() => {
      expect(mockMFAService.enableMFA).toHaveBeenCalledWith({
        secret: 'TEST-SECRET',
        totp_code: '123456',
        backup_codes: ['CODE1', 'CODE2'],
      });
    });

    // Should show completion step
    await waitFor(() => {
      expect(screen.getByText(/mfa.*enabled/i)).toBeInTheDocument();
    });
  });

  it('should handle invalid verification code', async () => {
    const user = userEvent.setup();
    
    mockMFAService.setupMFA.mockResolvedValue({
      qr_code: 'mock-qr',
      secret: 'SECRET',
      backup_codes: ['CODE1'],
    });

    mockMFAService.enableMFA.mockRejectedValue({
      response: {
        data: {
          detail: 'Invalid verification code',
        },
      },
    });

    render(<MFASetup />);

    // Navigate to verification step
    await user.click(screen.getByRole('button', { name: /get started/i }));
    await waitFor(() => expect(screen.getByText('Scan QR Code')).toBeInTheDocument());
    await user.click(screen.getByRole('button', { name: /next.*verify/i }));

    // Enter wrong code
    await user.type(screen.getByPlaceholderText(/6-digit code/i), '000000');
    await user.click(screen.getByRole('button', { name: /verify.*enable/i }));

    // Should show error
    await waitFor(() => {
      expect(screen.getByText(/invalid verification code/i)).toBeInTheDocument();
    });
  });

  it('should only allow numeric input for verification code', async () => {
    const user = userEvent.setup();
    
    mockMFAService.setupMFA.mockResolvedValue({
      qr_code: 'mock-qr',
      secret: 'SECRET',
      backup_codes: ['CODE1'],
    });

    render(<MFASetup />);

    // Navigate to verification step
    await user.click(screen.getByRole('button', { name: /get started/i }));
    await waitFor(() => expect(screen.getByText('Scan QR Code')).toBeInTheDocument());
    await user.click(screen.getByRole('button', { name: /next.*verify/i }));

    // Try to enter non-numeric characters
    const codeInput = screen.getByPlaceholderText(/6-digit code/i) as HTMLInputElement;
    await user.type(codeInput, 'abc123xyz');

    // Should only have numeric characters
    expect(codeInput.value).toBe('123');
  });

  it('should limit verification code to 6 digits', async () => {
    const user = userEvent.setup();
    
    mockMFAService.setupMFA.mockResolvedValue({
      qr_code: 'mock-qr',
      secret: 'SECRET',
      backup_codes: ['CODE1'],
    });

    render(<MFASetup />);

    // Navigate to verification step
    await user.click(screen.getByRole('button', { name: /get started/i }));
    await waitFor(() => expect(screen.getByText('Scan QR Code')).toBeInTheDocument());
    await user.click(screen.getByRole('button', { name: /next.*verify/i }));

    // Try to enter more than 6 digits
    const codeInput = screen.getByPlaceholderText(/6-digit code/i) as HTMLInputElement;
    await user.type(codeInput, '1234567890');

    // Should only have 6 digits
    expect(codeInput.value).toBe('123456');
  });

  it('should display backup codes in complete step', async () => {
    const user = userEvent.setup();
    
    const backupCodes = ['BACKUP1', 'BACKUP2', 'BACKUP3'];
    
    mockMFAService.setupMFA.mockResolvedValue({
      qr_code: 'mock-qr',
      secret: 'SECRET',
      backup_codes: backupCodes,
    });

    mockMFAService.enableMFA.mockResolvedValue({ success: true });

    render(<MFASetup />);

    // Complete the flow
    await user.click(screen.getByRole('button', { name: /get started/i }));
    await waitFor(() => expect(screen.getByText('Scan QR Code')).toBeInTheDocument());
    await user.click(screen.getByRole('button', { name: /next.*verify/i }));
    await user.type(screen.getByPlaceholderText(/6-digit code/i), '123456');
    await user.click(screen.getByRole('button', { name: /verify.*enable/i }));

    // Should show backup codes
    await waitFor(() => {
      backupCodes.forEach(code => {
        expect(screen.getByText(code)).toBeInTheDocument();
      });
    });
  });

  it('should allow copying backup codes', async () => {
    const user = userEvent.setup();
    
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn(),
      },
    });

    mockMFAService.setupMFA.mockResolvedValue({
      qr_code: 'mock-qr',
      secret: 'SECRET',
      backup_codes: ['CODE1', 'CODE2'],
    });

    mockMFAService.enableMFA.mockResolvedValue({ success: true });

    render(<MFASetup />);

    // Complete the flow
    await user.click(screen.getByRole('button', { name: /get started/i }));
    await waitFor(() => expect(screen.getByText('Scan QR Code')).toBeInTheDocument());
    await user.click(screen.getByRole('button', { name: /next.*verify/i }));
    await user.type(screen.getByPlaceholderText(/6-digit code/i), '123456');
    await user.click(screen.getByRole('button', { name: /verify.*enable/i }));

    // Wait for completion
    await waitFor(() => {
      expect(screen.getByText(/mfa.*enabled/i)).toBeInTheDocument();
    });

    // Click copy button
    const copyButton = screen.getByRole('button', { name: /copy.*codes/i });
    await user.click(copyButton);

    // Should copy to clipboard
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('CODE1\nCODE2');
  });
});

