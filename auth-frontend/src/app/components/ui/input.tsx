/**
 * Input Component
 * shadcn/ui style input with Tailwind CSS
 * Enhanced with ARIA attributes for accessibility
 * 
 * Compliance: 08c-react-best-practices.md Section 7.2
 */

import * as React from 'react';
import { cn } from '../../../lib/utils';
import { Label } from './label';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, error, label, id, ...props }, ref) => {
    // Generate unique IDs for accessibility
    const generatedId = React.useId();
    const inputId = id || generatedId;
    const errorId = `${inputId}-error`;
    
    return (
      <div className="w-full space-y-2">
        {label && <Label htmlFor={inputId}>{label}</Label>}
        <input
          id={inputId}
          type={type}
          aria-invalid={!!error}                      // ✅ Indicates invalid state
          aria-describedby={error ? errorId : undefined} // ✅ Links to error message
          aria-required={props.required}               // ✅ Indicates required fields
          className={cn(
            'flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm ring-offset-white file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
            error && 'border-red-500 focus-visible:ring-red-500',
            className
          )}
          ref={ref}
          {...props}
        />
        {error && (
          <span 
            id={errorId} 
            role="alert"                              // ✅ Announces error to screen readers
            className="mt-1 text-sm text-red-600"
          >
            {error}
          </span>
        )}
      </div>
    );
  }
);
Input.displayName = 'Input';

export { Input };
