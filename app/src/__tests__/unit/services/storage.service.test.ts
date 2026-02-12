import * as SecureStore from 'expo-secure-store';

// Mock expo-secure-store
const store: Record<string, string> = {};
jest.mock('expo-secure-store', () => ({
  setItemAsync: jest.fn(async (key: string, value: string) => { store[key] = value; }),
  getItemAsync: jest.fn(async (key: string) => store[key] ?? null),
  deleteItemAsync: jest.fn(async (key: string) => { delete store[key]; }),
}));

import { storageService } from '../../../services/storage.service';

beforeEach(() => {
  Object.keys(store).forEach(k => delete store[k]);
  jest.clearAllMocks();
});

describe('storageService', () => {
  describe('AccessToken', () => {
    it('sets and gets access token', async () => {
      await storageService.setAccessToken('token-abc');
      const result = await storageService.getAccessToken();
      expect(result).toBe('token-abc');
    });

    it('returns null when no token set', async () => {
      const result = await storageService.getAccessToken();
      expect(result).toBeNull();
    });
  });

  describe('RefreshToken', () => {
    it('sets and gets refresh token', async () => {
      await storageService.setRefreshToken('refresh-abc');
      const result = await storageService.getRefreshToken();
      expect(result).toBe('refresh-abc');
    });

    it('returns null when no token set', async () => {
      expect(await storageService.getRefreshToken()).toBeNull();
    });
  });

  describe('UserId', () => {
    it('sets and gets user id', async () => {
      await storageService.setUserId('user-123');
      expect(await storageService.getUserId()).toBe('user-123');
    });
  });

  describe('Theme', () => {
    it('sets and gets theme', async () => {
      await storageService.setTheme('dark');
      expect(await storageService.getTheme()).toBe('dark');
    });
  });

  describe('Language', () => {
    it('sets and gets language', async () => {
      await storageService.setLanguage('pl');
      expect(await storageService.getLanguage()).toBe('pl');
    });
  });

  describe('clearAll', () => {
    it('clears all stored values', async () => {
      await storageService.setAccessToken('a');
      await storageService.setRefreshToken('b');
      await storageService.setUserId('c');
      await storageService.setTheme('dark');
      await storageService.setLanguage('pl');

      await storageService.clearAll();

      expect(await storageService.getAccessToken()).toBeNull();
      expect(await storageService.getRefreshToken()).toBeNull();
      expect(await storageService.getUserId()).toBeNull();
      expect(await storageService.getTheme()).toBeNull();
      expect(await storageService.getLanguage()).toBeNull();
    });

    it('calls deleteItemAsync for each key', async () => {
      await storageService.clearAll();
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledTimes(5);
    });
  });
});
