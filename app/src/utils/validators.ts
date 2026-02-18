import { z } from "zod";

import { User } from "@/types/user";

export const createLoginSchema = (t: (key: string) => string) =>
  z.object({
    username: z
      .string()
      .min(1, { message: t("auth.validation.emailRequired") })
      .email({ message: t("auth.validation.invalidEmail") }),
    password: z
      .string()
      .min(1, { message: t("auth.validation.passwordRequired") }),
  });

export const createRegisterSchema = (t: (key: string) => string) =>
  z
    .object({
      email: z
        .string()
        .min(1, { message: t("auth.validation.emailRequired") })
        .email({ message: t("auth.validation.invalidEmail") }),
      password: z
        .string()
        .min(1, { message: t("auth.validation.passwordRequired") })
        .min(8, { message: t("auth.validation.passwordMin") })
        .regex(/[A-Z]/, { message: t("auth.validation.passwordUppercase") })
        .regex(/[0-9]/, { message: t("auth.validation.passwordNumber") }),
      confirmPassword: z
        .string()
        .min(1, { message: t("auth.validation.passwordRequired") }),
    })
    .refine((data) => data.password === data.confirmPassword, {
      message: t("auth.validation.passwordMatch"),
      path: ["confirmPassword"],
    });

export const createVerificationSchema = (t: (key: string) => string) =>
  z.object({
    code: z
      .string()
      .min(1, { message: t("auth.validation.invalidCode") })
      .length(6, { message: t("auth.validation.invalidCode") }),
  });

export const createForgotPasswordSchema = (t: (key: string) => string) =>
  z.object({
    email: z
      .string()
      .min(1, { message: t("auth.validation.emailRequired") })
      .email({ message: t("auth.validation.invalidEmail") }),
  });

export const createChangePasswordSchema = (t: (key: string) => string) =>
  z
    .object({
      oldPassword: z
        .string()
        .min(1, { message: t("auth.validation.currentPasswordRequired") }),
      newPassword: z
        .string()
        .min(1, { message: t("auth.validation.passwordRequired") })
        .min(8, { message: t("auth.validation.passwordMin") })
        .regex(/[A-Z]/, { message: t("auth.validation.passwordUppercase") })
        .regex(/[0-9]/, { message: t("auth.validation.passwordNumber") }),
      confirmPassword: z
        .string()
        .min(1, { message: t("auth.validation.passwordRequired") }),
    })
    .refine((data) => data.newPassword === data.confirmPassword, {
      message: t("auth.validation.passwordMatch"),
      path: ["confirmPassword"],
    });

export const createResetPasswordSchema = (t: (key: string) => string) =>
  z
    .object({
      password: z
        .string()
        .min(1, { message: t("auth.validation.passwordRequired") })
        .min(8, { message: t("auth.validation.passwordMin") })
        .regex(/[A-Z]/, { message: t("auth.validation.passwordUppercase") })
        .regex(/[0-9]/, { message: t("auth.validation.passwordNumber") }),
      confirmPassword: z
        .string()
        .min(1, { message: t("auth.validation.passwordRequired") }),
    })
    .refine((data) => data.password === data.confirmPassword, {
      message: t("auth.validation.passwordMatch"),
      path: ["confirmPassword"],
    });

export { User };

export type LoginInput = z.infer<ReturnType<typeof createLoginSchema>>;
export type RegisterInput = z.infer<ReturnType<typeof createRegisterSchema>>;
export type VerificationInput = z.infer<
  ReturnType<typeof createVerificationSchema>
>;
export type ForgotPasswordInput = z.infer<
  ReturnType<typeof createForgotPasswordSchema>
>;
export type ChangePasswordInput = z.infer<
  ReturnType<typeof createChangePasswordSchema>
>;
export type ResetPasswordInput = z.infer<
  ReturnType<typeof createResetPasswordSchema>
>;
