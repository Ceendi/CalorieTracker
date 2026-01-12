import axios from 'axios';
import { CONFIG } from '@/constants/config';
import { storageService } from './storage.service';

const baseURL = CONFIG.API_URL;

export const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  async (config) => {
    const token = await storageService.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = await storageService.getRefreshToken();
        // Assuming there is an endpoint to refresh token
        // This part might need adjustment depending on exact backend API for refresh
        // For now, if refresh fails, we just reject.
        // If backend has specific refresh endpoint logic, implement here.
        
        // Example logic if backend is standard fastapi-users:
        // const response = await axios.post(`${baseURL}/auth/jwt/refresh`, {}, { 
        //   headers: { Authorization: `Bearer ${refreshToken}` } 
        // });
        // const { access_token } = response.data;
        // await storageService.setAccessToken(access_token);
        // originalRequest.headers.Authorization = `Bearer ${access_token}`;
        // return apiClient(originalRequest);
        
        // Note: For now, we will simply reject to trigger logout if 401 happens.
        // Full refresh logic requires knowing the exact Refresh implementation of your backend.
        // If it's a standard bearer refresh:
        if (refreshToken) {
             // Logic to be fully implemented when backend refresh endpoint is confirmed
             // For now, we fail safe.
             return Promise.reject(error);
        }
      } catch (refreshError) {
        await storageService.clearAll();
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);
