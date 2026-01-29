import { z } from 'zod';

export const UserProfileSchema = z.object({
  height: z.number().min(50).max(300).nullable().optional(),
  weight: z.number().min(20).max(500).nullable().optional(),
  age: z.number().min(10).max(120).nullable().optional(),
  goal: z.string().optional(),
  activity_level: z.string().optional(),
  gender: z.string().optional(),
});

export type UserProfileUpdate = z.infer<typeof UserProfileSchema>;
