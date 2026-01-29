/**
 * Core User entity
 * Maps to backend UserOutSchema
 */
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
