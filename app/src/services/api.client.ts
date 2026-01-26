import axios from 'axios';
import { CONFIG } from '@/constants/config';
import { storageService } from './storage.service';

const baseURL = CONFIG.API_URL;

let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;
let onUnauthorizedCallback: (() => void) | null = null;

export const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const setOnUnauthorizedCallback = (callback: () => void) => {
  onUnauthorizedCallback = callback;
};

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
        if (!refreshPromise) {
          refreshPromise = (async () => {
            try {
              const refreshToken = await storageService.getRefreshToken();
              if (!refreshToken) return null;

              const response = await axios.post(`${CONFIG.API_URL}/auth/refresh`, {
                  refresh_token: refreshToken
              });
              
              const { access_token, refresh_token: new_refresh_token } = response.data;
              
              await storageService.setAccessToken(access_token);
              if (new_refresh_token) {
                  await storageService.setRefreshToken(new_refresh_token);
              }
              return access_token;
            } catch (err) {
              await storageService.clearAll();
              if (onUnauthorizedCallback) {
                onUnauthorizedCallback();
              }
              return null;
            } finally {
              refreshPromise = null;
            }
          })();
        }

        const newToken = await refreshPromise;
        
        if (newToken) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);
