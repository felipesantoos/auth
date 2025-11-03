/**
 * React Query Provider
 * Configures React Query for server state management
 * 
 * Performance optimizations:
 * - Longer staleTime for rarely-changing data (reduces network requests)
 * - Aggressive caching for user profile and settings
 * - Disabled refetchOnWindowFocus to prevent unnecessary requests
 * - Smart retry strategy
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import type { ReactNode } from 'react';

// ⚡ PERFORMANCE: Optimized React Query configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Default cache settings (for general data)
      staleTime: 5 * 60 * 1000, // 5 minutes - data is considered fresh for this duration
      gcTime: 10 * 60 * 1000, // 10 minutes - cache persists even when unused
      
      // Network optimization
      retry: (failureCount, error: any) => {
        // Don't retry on 4xx errors (client errors)
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          return false;
        }
        // Retry up to 2 times for 5xx errors (server errors)
        return failureCount < 2;
      },
      
      // UX optimization - don't refetch on window focus
      // This prevents unnecessary requests when user switches tabs
      refetchOnWindowFocus: false,
      
      // Don't refetch on mount if data is still fresh
      refetchOnMount: false,
      
      // Refetch on reconnect (when internet connection is restored)
      refetchOnReconnect: true,
    },
    mutations: {
      // Don't retry mutations by default (they often have side effects)
      retry: 0,
      
      // Optimistic updates timeout
      networkMode: 'online',
    },
  },
  
  // Query-specific overrides
  // You can override these in individual useQuery calls using queryKey patterns
});

interface QueryProviderProps {
  children: ReactNode;
}

export const QueryProvider = ({ children }: QueryProviderProps) => (
  <QueryClientProvider client={queryClient}>
    {children}
    <ReactQueryDevtools initialIsOpen={false} />
  </QueryClientProvider>
);

export { queryClient };
