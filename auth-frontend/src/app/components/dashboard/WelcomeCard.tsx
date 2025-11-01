/**
 * Welcome Card (Dumb Component)
 * Displays welcome message and system features
 * Only receives props and renders UI - no business logic
 * Memoized since content is static - never needs to re-render
 * 
 * Compliance: 08c-react-best-practices.md Section 2.1, 6.1
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';

/**
 * Memoized component - static content, never re-renders
 */
export const WelcomeCard = React.memo(() => {
  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle>Bem-vindo ao Auth System!</CardTitle>
        <CardDescription>Sistema de autenticação multi-tenant com arquitetura hexagonal</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-slate-600">
          Você está autenticado com sucesso. Este é um sistema completo de autenticação com:
        </p>
        <ul className="mt-4 space-y-2 text-sm text-slate-600">
          <li className="flex items-center">
            <span className="mr-2">✅</span>
            Multi-tenant architecture
          </li>
          <li className="flex items-center">
            <span className="mr-2">✅</span>
            JWT com refresh tokens
          </li>
          <li className="flex items-center">
            <span className="mr-2">✅</span>
            Controle de acesso baseado em roles (RBAC)
          </li>
          <li className="flex items-center">
            <span className="mr-2">✅</span>
            Arquitetura hexagonal (frontend + backend)
          </li>
          <li className="flex items-center">
            <span className="mr-2">✅</span>
            React Query + React Hook Form + Zod
          </li>
        </ul>
      </CardContent>
    </Card>
  );
});

WelcomeCard.displayName = 'WelcomeCard';

