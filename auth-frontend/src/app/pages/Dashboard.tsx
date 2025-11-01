/**
 * Dashboard Page
 * Main dashboard after login with modern UI
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLogout } from '../hooks/useAuthMutations';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { LogOut, User, Mail, Shield, Building } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const logoutMutation = useLogout();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logoutMutation.mutateAsync();
      navigate('/login');
    } catch (error) {
      // Even if logout fails, navigate to login
      navigate('/login');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
            <Button variant="outline" onClick={handleLogout} loading={logoutMutation.isPending}>
              <LogOut className="mr-2 h-4 w-4" />
              Sair
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Card>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <User className="h-5 w-5 text-slate-500" />
                <CardTitle>Perfil do Usuário</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              <div>
                <p className="text-sm font-medium text-slate-500">Nome</p>
                <p className="text-lg font-semibold">{user?.name}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500">Username</p>
                <p className="text-lg">{user?.username}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Mail className="h-5 w-5 text-slate-500" />
                <CardTitle>Contato</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              <div>
                <p className="text-sm font-medium text-slate-500">Email</p>
                <p className="text-lg">{user?.email}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500">Status</p>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  user?.active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {user?.active ? 'Ativo' : 'Inativo'}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Shield className="h-5 w-5 text-slate-500" />
                <CardTitle>Permissões</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              <div>
                <p className="text-sm font-medium text-slate-500">Role</p>
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  user?.role === 'admin'
                    ? 'bg-purple-100 text-purple-800'
                    : user?.role === 'manager'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-slate-100 text-slate-800'
                }`}>
                  {user?.role?.toUpperCase()}
                </span>
              </div>
              {user?.clientId && (
                <div>
                  <p className="text-sm font-medium text-slate-500 flex items-center">
                    <Building className="h-4 w-4 mr-1" />
                    Client ID
                  </p>
                  <p className="text-sm font-mono">{user.clientId}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Bem-vindo ao Auth System!</CardTitle>
            <CardDescription>
              Sistema de autenticação multi-tenant com arquitetura hexagonal
            </CardDescription>
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
      </main>
    </div>
  );
};
