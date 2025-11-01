/**
 * Current User Query Hook
 * Custom hook for fetching current user using React Query
 */

import { useQuery } from '@tanstack/react-query';
import DIContainer from '../dicontainer/container';

export const useCurrentUser = () => {
  const authService = DIContainer.getAuthService();

  return useQuery({
    queryKey: ['currentUser'],
    queryFn: () => authService.getCurrentUser(),
    enabled: authService.isAuthenticated(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

