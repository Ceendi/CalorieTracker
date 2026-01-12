import * as SecureStore from 'expo-secure-store';

const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_ID_KEY = 'user_id';
const THEME_KEY = 'theme_preference';
const LANGUAGE_KEY = 'language_preference';

export const storageService = {
  async setAccessToken(token: string) {
    await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, token, { requireAuthentication: false });
  },

  async getAccessToken() {
    return await SecureStore.getItemAsync(ACCESS_TOKEN_KEY, { requireAuthentication: false });
  },

  async setRefreshToken(token: string) {
    await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, token, { requireAuthentication: false });
  },

  async getRefreshToken() {
    return await SecureStore.getItemAsync(REFRESH_TOKEN_KEY, { requireAuthentication: false });
  },

  async setUserId(id: string) {
    await SecureStore.setItemAsync(USER_ID_KEY, id, { requireAuthentication: false });
  },

  async getUserId() {
    return await SecureStore.getItemAsync(USER_ID_KEY, { requireAuthentication: false });
  },

  async clearAll() {
    await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY, { requireAuthentication: false });
    await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY, { requireAuthentication: false });
    await SecureStore.deleteItemAsync(USER_ID_KEY, { requireAuthentication: false });
    await SecureStore.deleteItemAsync(THEME_KEY, { requireAuthentication: false });
    await SecureStore.deleteItemAsync(LANGUAGE_KEY, { requireAuthentication: false });
  },

  async setTheme(theme: 'light' | 'dark' | 'system') {
    await SecureStore.setItemAsync(THEME_KEY, theme, { requireAuthentication: false });
  },

  async getTheme() {
    return await SecureStore.getItemAsync(THEME_KEY, { requireAuthentication: false });
  },

  async setLanguage(language: 'en' | 'pl') {
    await SecureStore.setItemAsync(LANGUAGE_KEY, language, { requireAuthentication: false });
  },

  async getLanguage() {
    return await SecureStore.getItemAsync(LANGUAGE_KEY, { requireAuthentication: false });
  },
};
