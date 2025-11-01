/**
 * Forgot Password Page
 * Password reset request form with React Hook Form + Zod + React Query
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { forgotPasswordSchema, ForgotPasswordFormData } from '../schemas/auth.schema';
import { useForgotPassword } from '../hooks/useAuthMutations';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { AlertCircle } from 'lucide-react';

export const ForgotPassword: React.FC = () => {
  const [clientId, setClientId] = useState('');
  const forgotPasswordMutation = useForgotPassword();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: '',
    },
  });

  const onSubmit = async (data: ForgotPasswordFormData) => {
    await forgotPasswordMutation.mutateAsync({
      ...data,
      client_id: clientId || undefined,
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">Esqueceu a Senha?</CardTitle>
          <CardDescription>
            Digite seu email e enviaremos um link para redefinir sua senha
          </CardDescription>
        </CardHeader>
        <CardContent>
          {forgotPasswordMutation.isSuccess ? (
            <Alert variant="success">
              <AlertTitle>Email Enviado!</AlertTitle>
              <AlertDescription>
                Verifique sua caixa de entrada. Se o email existir, você receberá um link para redefinir sua senha.
              </AlertDescription>
            </Alert>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {forgotPasswordMutation.isError && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {(forgotPasswordMutation.error as any)?.response?.data?.detail || 'Erro ao enviar email. Tente novamente.'}
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
                label="Email"
                type="email"
                {...register('email')}
                error={errors.email?.message}
                placeholder="seu@email.com"
              />

              <Button type="submit" className="w-full" loading={forgotPasswordMutation.isPending}>
                Enviar Link de Redefinição
              </Button>
            </form>
          )}
        </CardContent>
        <CardFooter className="flex justify-center">
          <Link to="/login" className="text-sm text-slate-600 hover:text-slate-900 underline">
            Voltar para o login
          </Link>
        </CardFooter>
      </Card>
    </div>
  );
};
