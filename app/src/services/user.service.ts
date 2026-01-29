import { apiClient } from './api.client';
import { UserProfileUpdate } from '@/schemas/user';

export const userService = {
  async updateProfile(data: UserProfileUpdate) {
    const response = await apiClient.patch('/users/me', data);
    return response.data;
  }
};
