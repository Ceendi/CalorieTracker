import { authService } from '../../../services/auth.service';
import { apiClient } from '../../../services/api.client';
import { storageService } from '../../../services/storage.service';

jest.mock('../../../services/api.client', () => ({
  apiClient: {
    post: jest.fn(),
    get: jest.fn(),
  },
}));

jest.mock('../../../services/storage.service', () => ({
  storageService: {
    getRefreshToken: jest.fn(),
  },
}));

const mockPost = apiClient.post as jest.Mock;
const mockGet = apiClient.get as jest.Mock;

beforeEach(() => {
  jest.clearAllMocks();
});

const validUserResponse = {
  id: '550e8400-e29b-41d4-a716-446655440000',
  email: 'user@test.com',
  is_active: true,
  is_verified: true,
  is_onboarded: true,
  weight: 80,
  height: 180,
  age: 30,
  gender: 'male',
  activity_level: 'moderate',
  goal: 'maintain',
};

const validTokenResponse = {
  access_token: 'access-123',
  refresh_token: 'refresh-456',
  token_type: 'bearer',
};

describe('authService', () => {
  describe('login', () => {
    it('sends URLSearchParams and returns parsed tokens', async () => {
      mockPost.mockResolvedValue({ data: validTokenResponse });
      const result = await authService.login({ username: 'user@test.com', password: 'pass' });
      expect(mockPost).toHaveBeenCalledWith('/auth/login', expect.any(URLSearchParams), expect.objectContaining({
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      }));
      expect(result.access_token).toBe('access-123');
    });

    it('throws on API error', async () => {
      mockPost.mockRejectedValue(new Error('Network error'));
      await expect(authService.login({ username: 'u@t.com', password: 'p' })).rejects.toThrow();
    });
  });

  describe('loginGoogle', () => {
    it('sends idToken and returns parsed tokens', async () => {
      mockPost.mockResolvedValue({ data: validTokenResponse });
      const result = await authService.loginGoogle('google-id-token');
      expect(mockPost).toHaveBeenCalledWith('/auth/google', { token: 'google-id-token' });
      expect(result.access_token).toBe('access-123');
    });
  });

  describe('register', () => {
    it('sends email and password', async () => {
      mockPost.mockResolvedValue({ data: { id: 'new-id', email: 'u@t.com' } });
      const result = await authService.register({ email: 'u@t.com', password: 'Pass123', confirmPassword: 'Pass123' });
      expect(mockPost).toHaveBeenCalledWith('/auth/register', { email: 'u@t.com', password: 'Pass123' });
      expect(result.id).toBe('new-id');
    });
  });

  describe('getMe', () => {
    it('maps API response to User type', async () => {
      mockGet.mockResolvedValue({ data: validUserResponse });
      const user = await authService.getMe();
      expect(user.id).toBe(validUserResponse.id);
      expect(user.email).toBe('user@test.com');
      expect(user.weight).toBe(80);
    });

    it('maps nullable fields to undefined', async () => {
      mockGet.mockResolvedValue({
        data: { ...validUserResponse, weight: null, height: null, gender: null },
      });
      const user = await authService.getMe();
      expect(user.weight).toBeUndefined();
      expect(user.height).toBeUndefined();
      expect(user.gender).toBeUndefined();
    });
  });

  describe('verify', () => {
    it('posts token and returns user response', async () => {
      mockPost.mockResolvedValue({ data: validUserResponse });
      const result = await authService.verify('verify-token');
      expect(mockPost).toHaveBeenCalledWith('/auth/verify', { token: 'verify-token' });
      expect(result.id).toBe(validUserResponse.id);
    });
  });

  describe('logout', () => {
    it('posts refresh token', async () => {
      (storageService.getRefreshToken as jest.Mock).mockResolvedValue('refresh-abc');
      mockPost.mockResolvedValue({});
      await authService.logout();
      expect(mockPost).toHaveBeenCalledWith('/auth/logout', { refresh_token: 'refresh-abc' });
    });

    it('does not throw on API error', async () => {
      (storageService.getRefreshToken as jest.Mock).mockResolvedValue('refresh-abc');
      mockPost.mockRejectedValue(new Error('fail'));
      await expect(authService.logout()).resolves.toBeUndefined();
    });

    it('skips post when no refresh token', async () => {
      (storageService.getRefreshToken as jest.Mock).mockResolvedValue(null);
      await authService.logout();
      expect(mockPost).not.toHaveBeenCalled();
    });
  });

  describe('changePassword', () => {
    it('sends old and new password', async () => {
      mockPost.mockResolvedValue({});
      await authService.changePassword({ oldPassword: 'Old1', newPassword: 'New1', confirmPassword: 'New1' });
      expect(mockPost).toHaveBeenCalledWith('/users/change-password', {
        old_password: 'Old1',
        new_password: 'New1',
      });
    });
  });
});
