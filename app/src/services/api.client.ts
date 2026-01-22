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
        
        if (refreshToken) {
           const response = await axios.post(`${CONFIG.API_URL}/auth/refresh`, {
               refresh_token: refreshToken
           });
           
           const { access_token, refresh_token: new_refresh_token } = response.data;
           
           await storageService.setAccessToken(access_token);
           if (new_refresh_token) {
               await storageService.setRefreshToken(new_refresh_token);
           }
           
           originalRequest.headers.Authorization = `Bearer ${access_token}`;
           return apiClient(originalRequest);
        }
      } catch (refreshError) {
        await storageService.clearAll();
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);
