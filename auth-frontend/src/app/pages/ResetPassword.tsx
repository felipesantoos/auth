/**
 * Reset Password Page
 * Password reset form with token validation
 */

import React, { useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { resetPasswordSchema, ResetPasswordFormData } from '../schemas/auth.schema';
import { useResetPassword } from '../hooks/useAuthMutations';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { AlertCircle } from 'lucide-react';

export const ResetPassword: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [clientId, setClientId] = useState('');
  const navigate = useNavigate();
  const resetPasswordMutation = useResetPassword();
  
  const resetToken = searchParams.get('token') || '';

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      reset_token: resetToken,
      new_password: '',
      confirm_password: '',
    },
  });

  const onSubmit = async (data: ResetPasswordFormData) => {
    try {
      await resetPasswordMutation.mutateAsync({
        reset_token: data.reset_token,
        new_password: data.new_password,
        client_id: clientId || undefined,
      });
      // Success - redirect to login after 2 seconds
      setTimeout(() => navigate('/login'), 2000);
    } catch (error) {
      // Error is handled by React Query and shown below
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">Redefinir Senha</CardTitle>
          <CardDescription>Digite sua nova senha</CardDescription>
        </CardHeader>
        <CardContent>
          {resetPasswordMutation.isSuccess ? (
            <Alert variant="success">
              <AlertTitle>Senha Redefinida!</AlertTitle>
              <AlertDescription>
                Sua senha foi alterada com sucesso. Redirecionando para o login...
              </AlertDescription>
            </Alert>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {resetPasswordMutation.isError && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {(resetPasswordMutation.error as any)?.response?.data?.detail || 'Erro ao redefinir senha. Token pode estar expirado.'}
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
                label="Nova Senha"
                type="password"
                {...register('new_password')}
                error={errors.new_password?.message}
                placeholder="••••••••"
              />

              <Input
                label="Confirmar Senha"
                type="password"
                {...register('confirm_password')}
                error={errors.confirm_password?.message}
                placeholder="••••••••"
              />

              <input type="hidden" {...register('reset_token')} />

              <Button type="submit" className="w-full" loading={resetPasswordMutation.isPending}>
                Redefinir Senha
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

export default ResetPassword;
