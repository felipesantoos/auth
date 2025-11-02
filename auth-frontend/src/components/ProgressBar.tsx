/**
 * ProgressBar Component
 * Displays real-time progress updates via SSE
 * Compliant with 25-real-time-streaming.md guide
 */

import { useEffect, useState } from 'react';
import { useSSE } from '../hooks/useSSE';

interface ProgressData {
  task_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  message?: string;
}

interface ProgressBarProps {
  taskId: string;
  onComplete?: (data: ProgressData) => void;
  onError?: (error: any) => void;
  autoClose?: boolean;
  autoCloseDelay?: number;
}

export function ProgressBar({
  taskId,
  onComplete,
  onError,
  autoClose = true,
  autoCloseDelay = 2000
}: ProgressBarProps) {
  const [isVisible, setIsVisible] = useState(true);
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
  const sseUrl = `${apiBaseUrl}/sse/progress/${taskId}`;
  
  const { data, error, isConnected } = useSSE<ProgressData>(sseUrl, 'message', {
    onError: (err) => {
      console.error('SSE Progress error:', err);
      onError?.(err);
    }
  });
  
  useEffect(() => {
    if (data) {
      // Check if task is complete
      if (data.status === 'completed') {
        onComplete?.(data);
        
        // Auto-close after delay
        if (autoClose) {
          setTimeout(() => {
            setIsVisible(false);
          }, autoCloseDelay);
        }
      } else if (data.status === 'failed') {
        onError?.(data);
      }
    }
  }, [data, onComplete, onError, autoClose, autoCloseDelay]);
  
  if (!isVisible) {
    return null;
  }
  
  const progress = data?.progress || 0;
  const status = data?.status || 'pending';
  const message = data?.message || 'Initializing...';
  
  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return 'bg-green-600';
      case 'failed':
        return 'bg-red-600';
      case 'cancelled':
        return 'bg-gray-600';
      case 'in_progress':
        return 'bg-blue-600';
      default:
        return 'bg-gray-400';
    }
  };
  
  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return (
          <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'failed':
        return (
          <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'in_progress':
        return (
          <svg className="w-5 h-5 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        );
      default:
        return null;
    }
  };
  
  return (
    <div className="w-full max-w-md mx-auto p-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <span className="text-sm font-medium text-gray-900 dark:text-white">
            {status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ')}
          </span>
        </div>
        
        {/* Connection status */}
        {!isConnected && (
          <span className="text-xs text-yellow-600 dark:text-yellow-400">
            Reconnecting...
          </span>
        )}
        
        {/* Close button */}
        <button
          onClick={() => setIsVisible(false)}
          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          aria-label="Close"
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      </div>
      
      {/* Message */}
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
        {message}
      </p>
      
      {/* Progress Bar */}
      <div className="relative w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${getStatusColor()} transition-all duration-300 ease-out`}
          style={{ width: `${Math.min(Math.max(progress, 0), 100)}%` }}
        />
      </div>
      
      {/* Progress Percentage */}
      <div className="mt-2 flex items-center justify-between">
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {Math.round(progress)}%
        </span>
        {error && (
          <span className="text-xs text-red-600 dark:text-red-400">
            Error occurred
          </span>
        )}
      </div>
    </div>
  );
}

