// We need to mock storage and config before importing api.client
jest.mock('../../../services/storage.service', () => {
  const store: Record<string, string | null> = {};
  return {
    storageService: {
      getAccessToken: jest.fn(async () => store['access_token'] ?? null),
      setAccessToken: jest.fn(async (token: string) => { store['access_token'] = token; }),
      getRefreshToken: jest.fn(async () => store['refresh_token'] ?? null),
      setRefreshToken: jest.fn(async (token: string) => { store['refresh_token'] = token; }),
      clearAll: jest.fn(async () => {
        store['access_token'] = null;
        store['refresh_token'] = null;
      }),
      _store: store,
    },
  };
});

jest.mock('../../../constants/config', () => ({
  CONFIG: { API_URL: 'http://localhost:8000' },
}));

import { apiClient, setOnUnauthorizedCallback } from '../../../services/api.client';
import { storageService } from '../../../services/storage.service';

const mockStore = (storageService as any)._store as Record<string, string | null>;

beforeEach(() => {
  jest.clearAllMocks();
  mockStore['access_token'] = null;
  mockStore['refresh_token'] = null;
});

describe('apiClient', () => {
  describe('defaults', () => {
    it('has correct baseURL', () => {
      expect(apiClient.defaults.baseURL).toBe('http://localhost:8000');
    });

    it('has JSON content type', () => {
      expect(apiClient.defaults.headers['Content-Type']).toBe('application/json');
    });

    it('has 10s timeout', () => {
      expect(apiClient.defaults.timeout).toBe(10000);
    });
  });

  describe('request interceptor', () => {
    it('adds Authorization header when token exists', async () => {
      mockStore['access_token'] = 'my-token';
      // The interceptor is async so we test via the interceptor directly
      const config = { headers: {} as any };
      // Get the request interceptor handler
      const interceptors = (apiClient.interceptors.request as any).handlers;
      const requestInterceptor = interceptors[0].fulfilled;
      const result = await requestInterceptor(config);
      expect(result.headers.Authorization).toBe('Bearer my-token');
    });

    it('does not add Authorization when no token', async () => {
      mockStore['access_token'] = null;
      const config = { headers: {} as any };
      const interceptors = (apiClient.interceptors.request as any).handlers;
      const requestInterceptor = interceptors[0].fulfilled;
      const result = await requestInterceptor(config);
      expect(result.headers.Authorization).toBeUndefined();
    });
  });

  describe('setOnUnauthorizedCallback', () => {
    it('accepts a callback', () => {
      const callback = jest.fn();
      expect(() => setOnUnauthorizedCallback(callback)).not.toThrow();
    });
  });
});
