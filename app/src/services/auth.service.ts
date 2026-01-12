import { apiClient } from './api.client';
import { LoginInput, RegisterInput, User, ChangePasswordInput } from '@/utils/validators';

export const authService = {
  async login(data: LoginInput) {
    const formData = new URLSearchParams();
    formData.append('username', data.username);
    formData.append('password', data.password);
    
    const response = await apiClient.post('/auth/jwt/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },

  async register(data: RegisterInput) {
    const response = await apiClient.post('/auth/register', {
      email: data.email,
      password: data.password,
    });
    return response.data;
  },

  async verify(token: string) {
    const response = await apiClient.post('/auth/verify', { token }); 
    return response.data;
  },

  async requestVerifyToken(email: string) {
    const response = await apiClient.post('/auth/request-verify-token', { email });
    return response.data;
  },

  async getMe(): Promise<User> {
    const response = await apiClient.get('/users/me');
    return response.data;
  },

  async logout() {
    return await apiClient.post('/auth/jwt/logout');
  },

  async changePassword(data: ChangePasswordInput) {
    const response = await apiClient.post('/users/change-password', {
      old_password: data.oldPassword,
      new_password: data.newPassword,
    });
    return response.data;
  },
};
