/**
 * Error Boundary Component
 * Catches rendering errors and displays fallback UI
 * 
 * Compliance: 08c-react-best-practices.md Section 5.3
 */

import type { ErrorInfo, ReactNode } from 'react';
import { Component } from 'react';
import { Alert, AlertDescription } from './ui/alert';
import { AlertCircle } from 'lucide-react';
import { Button } from './ui/button';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }
  
  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to console in development
    console.error('Error caught by boundary:', error, errorInfo);
    
    // In production, send to error tracking service (Sentry, LogRocket, etc)
    // if (env.environment === 'production') {
    //   sendToErrorTracker(error, errorInfo);
    // }
    
    this.setState({ errorInfo });
  }
  
  handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };
  
  render() {
    if (this.state.hasError) {
      // If custom fallback provided, use it
      if (this.props.fallback) {
        return this.props.fallback;
      }
      
      // Default fallback UI
      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
          <div className="w-full max-w-2xl">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <div className="space-y-4">
                  <h2 className="text-lg font-semibold">Algo deu errado</h2>
                  <p className="text-sm">{this.state.error?.message || 'Erro inesperado'}</p>
                  <details className="text-xs">
                    <summary className="cursor-pointer hover:underline">
                      Detalhes do erro (clique para expandir)
                    </summary>
                    <pre className="mt-2 p-2 bg-slate-100 rounded overflow-auto text-xs">
                      {this.state.error?.stack}
                    </pre>
                    {this.state.errorInfo && (
                      <pre className="mt-2 p-2 bg-slate-100 rounded overflow-auto text-xs">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    )}
                  </details>
                  <div className="flex gap-2">
                    <Button onClick={this.handleReset}>
                      Tentar Novamente
                    </Button>
                    <Button 
                      variant="outline" 
                      onClick={() => window.location.href = '/'}
                    >
                      Ir para Início
                    </Button>
                  </div>
                </div>
              </AlertDescription>
            </Alert>
          </div>
        </div>
      );
    }
    
    return this.props.children;
  }
}

