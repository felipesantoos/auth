/**
 * Register Page
 * User registration form with React Hook Form + Zod + React Query
 */

import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { registerSchema, RegisterFormData } from '../schemas/auth.schema';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Alert, AlertDescription } from '../components/ui/alert';
import { AlertCircle } from 'lucide-react';

export const Register: React.FC = () => {
  const [clientId, setClientId] = useState('');
  const navigate = useNavigate();
  const { register: registerUser, registering, error, clearError } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      username: '',
      email: '',
      password: '',
      name: '',
    },
  });

  const onSubmit = async (data: RegisterFormData) => {
    try {
      await registerUser(data.username, data.email, data.password, data.name, clientId || undefined);
      navigate('/dashboard');
    } catch (error) {
      // Error is handled by Context and shown below
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">Criar Conta</CardTitle>
          <CardDescription>Preencha os dados abaixo para criar sua conta</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  <div className="flex items-center justify-between">
                    <span>{error}</span>
                    <button
                      type="button"
                      onClick={clearError}
                      className="ml-2 text-sm underline hover:no-underline"
                    >
                      Dismiss
                    </button>
                  </div>
                </AlertDescription>
              </Alert>
            )}

            <Input
              label="Client ID (opcional)"
              type="text"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              placeholder="client_id ou deixe em branco"
            />

            <Input
              label="Nome"
              type="text"
              {...register('name')}
              error={errors.name?.message}
              placeholder="João Silva"
            />

            <Input
              label="Username"
              type="text"
              {...register('username')}
              error={errors.username?.message}
              placeholder="joaosilva"
            />

            <Input
              label="Email"
              type="email"
              {...register('email')}
              error={errors.email?.message}
              placeholder="seu@email.com"
            />

            <Input
              label="Senha"
              type="password"
              {...register('password')}
              error={errors.password?.message}
              placeholder="••••••••"
            />

            <Button type="submit" className="w-full" loading={registering}>
              Criar Conta
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex justify-center">
          <p className="text-sm text-slate-600">
            Já tem uma conta?{' '}
            <Link to="/login" className="font-medium text-slate-900 hover:underline">
              Faça login
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
};

export default Register;
