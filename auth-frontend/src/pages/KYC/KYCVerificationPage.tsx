/**
 * KYC Verification Page
 * Allow users to upload identity documents for verification
 */
import React, { useState, useEffect } from 'react';
import { FileUpload } from '../../components/FileUpload/FileUpload';
import { fileService } from '../../infra/services/FileService';
import axios from 'axios';
import './KYCVerificationPage.css';

interface KYCStatus {
  kyc_status: string;
  kyc_verified: boolean;
  kyc_pending: boolean;
  kyc_verified_at: string | null;
}

export const KYCVerificationPage: React.FC = () => {
  const [status, setStatus] = useState<KYCStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchKYCStatus();
  }, []);

  const fetchKYCStatus = async () => {
    try {
      const response = await axios.get('/api/auth/profile/kyc/status');
      setStatus(response.data);
    } catch (err) {
      console.error('Error fetching KYC status:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (files: FileList) => {
    if (files.length === 0) return;

    setUploading(true);
    setError(null);
    setSuccess(null);

    try {
      const formData = new FormData();
      formData.append('document', files[0]);

      const response = await axios.post('/api/auth/profile/kyc/document', formData);
      
      setSuccess('KYC document submitted successfully! Awaiting verification.');
      await fetchKYCStatus();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload KYC document');
    } finally {
      setUploading(false);
    }
  };

  const getStatusBadge = () => {
    if (!status) return null;

    switch (status.kyc_status) {
      case 'approved':
        return <span className="kyc-badge kyc-approved">✓ Verified</span>;
      case 'pending':
        return <span className="kyc-badge kyc-pending">⏳ Pending Review</span>;
      case 'rejected':
        return <span className="kyc-badge kyc-rejected">✗ Rejected</span>;
      default:
        return <span className="kyc-badge kyc-not-submitted">Not Submitted</span>;
    }
  };

  if (loading) {
    return (
      <div className="kyc-page">
        <div className="kyc-loading">Loading KYC status...</div>
      </div>
    );
  }

  return (
    <div className="kyc-page">
      <div className="kyc-container">
        <h1>Identity Verification (KYC)</h1>
        
        <div className="kyc-status-card">
          <h2>Verification Status</h2>
          {getStatusBadge()}
          
          {status?.kyc_verified_at && (
            <p className="kyc-verified-date">
              Verified on: {new Date(status.kyc_verified_at).toLocaleDateString()}
            </p>
          )}
        </div>

        {!status?.kyc_verified && (
          <>
            <div className="kyc-instructions">
              <h3>Document Requirements</h3>
              <ul>
                <li>Upload a clear photo or scan of your government-issued ID</li>
                <li>Accepted documents: Passport, National ID, Driver's License</li>
                <li>Ensure all text is readable and the photo is not blurred</li>
                <li>File formats: JPG, PNG, PDF (max 10MB)</li>
                <li>Your information will be kept secure and confidential</li>
              </ul>
            </div>

            {status?.kyc_status !== 'pending' && (
              <div className="kyc-upload-section">
                <h3>Upload Document</h3>
                
                {error && (
                  <div className="kyc-error">{error}</div>
                )}
                
                {success && (
                  <div className="kyc-success">{success}</div>
                )}

                <FileUpload
                  onFilesSelected={handleFileUpload}
                  accept="image/jpeg,image/png,application/pdf"
                  maxSize={10 * 1024 * 1024}
                  disabled={uploading}
                  multiple={false}
                />

                {uploading && (
                  <div className="kyc-uploading">
                    Uploading document... Please wait.
                  </div>
                )}
              </div>
            )}

            {status?.kyc_status === 'pending' && (
              <div className="kyc-pending-message">
                <h3>Under Review</h3>
                <p>
                  Your document has been submitted and is currently under review.
                  This process typically takes 1-3 business days.
                  We'll notify you once the verification is complete.
                </p>
              </div>
            )}

            {status?.kyc_status === 'rejected' && (
              <div className="kyc-rejected-message">
                <h3>Verification Rejected</h3>
                <p>
                  Unfortunately, your previous submission was rejected.
                  Please ensure your document meets all requirements and try again.
                </p>
              </div>
            )}
          </>
        )}

        {status?.kyc_verified && (
          <div className="kyc-verified-message">
            <h3>✓ Identity Verified</h3>
            <p>
              Your identity has been successfully verified.
              You now have full access to all platform features.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

