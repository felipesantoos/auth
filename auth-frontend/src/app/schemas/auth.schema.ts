/**
 * Auth Form Schemas
 * Zod schemas for authentication form validation
 */

import { z } from 'zod';

export const loginSchema = z.object({
  email: z.string().email('Email inválido'),
  password: z.string().min(8, 'Senha deve ter no mínimo 8 caracteres'),
  client_id: z.string().optional(),
});

export type LoginFormData = z.infer<typeof loginSchema>;

export const registerSchema = z.object({
  username: z.string().min(3, 'Username deve ter no mínimo 3 caracteres'),
  email: z.string().email('Email inválido'),
  password: z.string().min(8, 'Senha deve ter no mínimo 8 caracteres'),
  name: z.string().min(2, 'Nome deve ter no mínimo 2 caracteres'),
  client_id: z.string().optional(),
});

export type RegisterFormData = z.infer<typeof registerSchema>;

export const forgotPasswordSchema = z.object({
  email: z.string().email('Email inválido'),
  client_id: z.string().optional(),
});

export type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

export const resetPasswordSchema = z.object({
  reset_token: z.string().min(1, 'Token é obrigatório'),
  new_password: z.string().min(8, 'Nova senha deve ter no mínimo 8 caracteres'),
  confirm_password: z.string().min(8, 'Confirmação de senha é obrigatória'),
  client_id: z.string().optional(),
}).refine((data) => data.new_password === data.confirm_password, {
  message: 'As senhas não conferem',
  path: ['confirm_password'],
});

export type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;
