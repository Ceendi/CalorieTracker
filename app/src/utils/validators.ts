import { z } from 'zod';

export const loginSchema = z.object({
  username: z.string().email({ message: "Invalid email address" }),
  password: z.string().min(1, { message: "Password is required" }),
});

export const registerSchema = z.object({
  email: z.string().email({ message: "Invalid email address" }),
  password: z.string()
    .min(8, { message: "Password must be at least 8 characters" })
    .regex(/[A-Z]/, { message: "Password must contain at least one uppercase letter" })
    .regex(/[0-9]/, { message: "Password must contain at least one number" }),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

export const verificationSchema = z.object({
  code: z.string().length(6, { message: "Invalid verification code" }),
});

export const changePasswordSchema = z.object({
  oldPassword: z.string().min(1, { message: "Current password is required" }),
  newPassword: z.string()
    .min(8, { message: "Password must be at least 8 characters" })
    .regex(/[A-Z]/, { message: "Password must contain at least one uppercase letter" })
    .regex(/[0-9]/, { message: "Password must contain at least one number" }),
  confirmPassword: z.string(),
}).refine((data) => data.newPassword === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

export interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  is_onboarded?: boolean;
  age?: number;
  gender?: string;
  height?: number;
  weight?: number;
  goal?: string;
  activity_level?: string;
}

export type LoginInput = z.infer<typeof loginSchema>;
export type RegisterInput = z.infer<typeof registerSchema>;
export type VerificationInput = z.infer<typeof verificationSchema>;
export type ChangePasswordInput = z.infer<typeof changePasswordSchema>;
