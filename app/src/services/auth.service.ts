import { apiClient } from './api.client';
import { storageService } from './storage.service';
import { LoginInput, RegisterInput, User, ChangePasswordInput } from '@/utils/validators';
import { TokenResponseSchema, UserResponseSchema, TokenResponse } from '@/schemas/api';

/**
 * Map API user response to frontend User type
 */
function mapUser(apiUser: ReturnType<typeof UserResponseSchema.parse>): User {
  return {
    id: apiUser.id,
    email: apiUser.email,
    is_active: apiUser.is_active,
    is_verified: apiUser.is_verified,
    is_onboarded: apiUser.is_onboarded,
    weight: apiUser.weight ?? undefined,
    height: apiUser.height ?? undefined,
    age: apiUser.age ?? undefined,
    gender: apiUser.gender ?? undefined,
    activity_level: apiUser.activity_level ?? undefined,
    goal: apiUser.goal ?? undefined,
  };
}

export const authService = {
  async login(data: LoginInput): Promise<TokenResponse> {
    const formData = new URLSearchParams();
    formData.append('username', data.username);
    formData.append('password', data.password);

    const response = await apiClient.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return TokenResponseSchema.parse(response.data);
  },

  async register(data: RegisterInput): Promise<{ id: string; email: string }> {
    const response = await apiClient.post('/auth/register', {
      email: data.email,
      password: data.password,
    });
    return response.data;
  },

  async verify(token: string): Promise<TokenResponse> {
    const response = await apiClient.post('/auth/verify', { token });
    return TokenResponseSchema.parse(response.data);
  },

  async requestVerifyToken(email: string): Promise<void> {
    await apiClient.post('/auth/request-verify-token', { email });
  },

  async getMe(): Promise<User> {
    const response = await apiClient.get('/users/me');
    const validated = UserResponseSchema.parse(response.data);
    return mapUser(validated);
  },

  async logout(): Promise<void> {
    try {
      const refreshToken = await storageService.getRefreshToken();
      if (refreshToken) {
        await apiClient.post('/auth/logout', { refresh_token: refreshToken });
      }
    } catch (e) {
      // Logout errors are non-critical - user is logging out anyway
      console.warn('Logout request failed:', e);
    }
  },

  async forgotPassword(email: string): Promise<void> {
    await apiClient.post('/auth/forgot-password', { email });
  },

  async resetPassword(token: string, password: string): Promise<void> {
    await apiClient.post('/auth/reset-password', { token, password });
  },

  async changePassword(data: ChangePasswordInput): Promise<void> {
    await apiClient.post('/users/change-password', {
      old_password: data.oldPassword,
      new_password: data.newPassword,
    });
  },
};
