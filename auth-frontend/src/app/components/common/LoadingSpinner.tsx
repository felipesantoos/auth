/**
 * Loading Spinner Component (Dumb Component)
 * Reusable loading indicator with accessible attributes
 * 
 * Compliance: 08c-react-best-practices.md Section 2.1, 7.2
 */

import React from 'react';

interface LoadingSpinnerProps {
  message?: string;
}

/**
 * LoadingSpinner - Dumb Component
 * Only receives props and renders UI
 * Memoized to prevent unnecessary re-renders
 */
export const LoadingSpinner: React.FC<LoadingSpinnerProps> = React.memo(({ message = 'Carregando...' }) => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center">
        <div 
          className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]"
          role="status"
          aria-label="Carregando"
        >
          <span className="sr-only">Carregando</span>
        </div>
        <p className="mt-4 text-slate-600">{message}</p>
      </div>
    </div>
  );
});

LoadingSpinner.displayName = 'LoadingSpinner';

