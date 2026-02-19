import { renderHook, act } from '@testing-library/react-native';

import { useAuth } from '@/hooks/useAuth';
import { authService } from '@/services/auth.service';
import { storageService } from '@/services/storage.service';
import { GoogleSignin, statusCodes } from '@react-native-google-signin/google-signin';

// Mock all dependencies before importing the hook
jest.mock('@/services/storage.service', () => ({
  storageService: {
    setAccessToken: jest.fn(),
    getAccessToken: jest.fn(),
    setRefreshToken: jest.fn(),
    getRefreshToken: jest.fn(),
    clearAll: jest.fn(),
  },
}));

jest.mock('@/services/auth.service', () => ({
  authService: {
    login: jest.fn(),
    loginGoogle: jest.fn(),
    register: jest.fn(),
    getMe: jest.fn(),
    logout: jest.fn(),
  },
}));

jest.mock('@/services/api.client', () => ({
  setOnUnauthorizedCallback: jest.fn(),
}));

jest.mock('@react-native-google-signin/google-signin', () => ({
  GoogleSignin: {
    configure: jest.fn(),
    hasPlayServices: jest.fn(),
    signIn: jest.fn(),
    signOut: jest.fn(),
  },
  statusCodes: {
    SIGN_IN_CANCELLED: 'SIGN_IN_CANCELLED',
    IN_PROGRESS: 'IN_PROGRESS',
    PLAY_SERVICES_NOT_AVAILABLE: 'PLAY_SERVICES_NOT_AVAILABLE',
  },
}));

const mockUser = {
  id: 'user-1',
  email: 'test@test.com',
  is_active: true,
  is_verified: true,
  is_onboarded: true,
};

beforeEach(() => {
  jest.clearAllMocks();
  // Reset zustand store
  act(() => {
    useAuth.setState({ user: null, isLoading: false, isSignout: false });
  });
});

describe('useAuth', () => {
  describe('signIn', () => {
    it('stores tokens and sets user', async () => {
      (authService.login as jest.Mock).mockResolvedValue({
        access_token: 'at',
        refresh_token: 'rt',
      });
      (authService.getMe as jest.Mock).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth());
      await act(async () => {
        await result.current.signIn({ username: 'test@test.com', password: 'pass' });
      });

      expect(storageService.setAccessToken).toHaveBeenCalledWith('at');
      expect(storageService.setRefreshToken).toHaveBeenCalledWith('rt');
      expect(result.current.user).toEqual(mockUser);
    });

    it('throws on login error', async () => {
      (authService.login as jest.Mock).mockRejectedValue(new Error('bad creds'));
      const { result } = renderHook(() => useAuth());

      await expect(act(async () => {
        await result.current.signIn({ username: 'u', password: 'p' });
      })).rejects.toThrow('bad creds');
    });
  });

  describe('signUp', () => {
    it('registers then auto-logs in', async () => {
      (authService.register as jest.Mock).mockResolvedValue({ id: 'new', email: 'u@t.com' });
      (authService.login as jest.Mock).mockResolvedValue({ access_token: 'at', refresh_token: 'rt' });
      (authService.getMe as jest.Mock).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth());
      await act(async () => {
        await result.current.signUp({ email: 'u@t.com', password: 'Pass123', confirmPassword: 'Pass123' });
      });

      expect(authService.register).toHaveBeenCalled();
      expect(authService.login).toHaveBeenCalledWith({ username: 'u@t.com', password: 'Pass123' });
      expect(result.current.user).toEqual(mockUser);
    });
  });

  describe('signInWithGoogle', () => {
    it('authenticates via Google and sets user', async () => {
      (GoogleSignin.hasPlayServices as jest.Mock).mockResolvedValue(true);
      (GoogleSignin.signIn as jest.Mock).mockResolvedValue({ data: { idToken: 'gtoken' } });
      (authService.loginGoogle as jest.Mock).mockResolvedValue({ access_token: 'at', refresh_token: 'rt' });
      (authService.getMe as jest.Mock).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth());
      await act(async () => {
        await result.current.signInWithGoogle();
      });

      expect(authService.loginGoogle).toHaveBeenCalledWith('gtoken');
      expect(result.current.user).toEqual(mockUser);
    });

    it('silently returns on SIGN_IN_CANCELLED', async () => {
      (GoogleSignin.hasPlayServices as jest.Mock).mockResolvedValue(true);
      (GoogleSignin.signIn as jest.Mock).mockRejectedValue({ code: statusCodes.SIGN_IN_CANCELLED });

      const { result } = renderHook(() => useAuth());
      await act(async () => {
        await result.current.signInWithGoogle();
      });

      expect(result.current.user).toBeNull();
    });

    it('silently returns on IN_PROGRESS', async () => {
      (GoogleSignin.hasPlayServices as jest.Mock).mockResolvedValue(true);
      (GoogleSignin.signIn as jest.Mock).mockRejectedValue({ code: statusCodes.IN_PROGRESS });

      const { result } = renderHook(() => useAuth());
      await act(async () => {
        await result.current.signInWithGoogle();
      });
      // No throw, no user set
      expect(result.current.user).toBeNull();
    });

    it('throws AppError on PLAY_SERVICES_NOT_AVAILABLE', async () => {
      (GoogleSignin.hasPlayServices as jest.Mock).mockResolvedValue(true);
      (GoogleSignin.signIn as jest.Mock).mockRejectedValue({ code: statusCodes.PLAY_SERVICES_NOT_AVAILABLE });

      const { result } = renderHook(() => useAuth());
      await expect(act(async () => {
        await result.current.signInWithGoogle();
      })).rejects.toThrow('Google Play Services not available');
    });

    it('throws when no idToken returned', async () => {
      (GoogleSignin.hasPlayServices as jest.Mock).mockResolvedValue(true);
      (GoogleSignin.signIn as jest.Mock).mockResolvedValue({ data: { idToken: null } });

      const { result } = renderHook(() => useAuth());
      await expect(act(async () => {
        await result.current.signInWithGoogle();
      })).rejects.toThrow('No ID token returned from Google');
    });
  });

  describe('signOut', () => {
    it('clears storage and state', async () => {
      act(() => {
        useAuth.setState({ user: mockUser });
      });
      (authService.logout as jest.Mock).mockResolvedValue(undefined);

      const { result } = renderHook(() => useAuth());
      await act(async () => {
        await result.current.signOut();
      });

      expect(authService.logout).toHaveBeenCalled();
      expect(storageService.clearAll).toHaveBeenCalled();
      expect(result.current.user).toBeNull();
      expect(result.current.isSignout).toBe(true);
    });
  });

  describe('checkSession', () => {
    it('sets user when valid token exists', async () => {
      (storageService.getAccessToken as jest.Mock).mockResolvedValue('valid-token');
      (authService.getMe as jest.Mock).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth());
      await act(async () => {
        await result.current.checkSession();
      });

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isLoading).toBe(false);
    });

    it('sets user to null when no token', async () => {
      (storageService.getAccessToken as jest.Mock).mockResolvedValue(null);

      const { result } = renderHook(() => useAuth());
      await act(async () => {
        await result.current.checkSession();
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('refreshUser', () => {
    it('updates user on success', async () => {
      (authService.getMe as jest.Mock).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth());
      await act(async () => {
        await result.current.refreshUser();
      });

      expect(result.current.user).toEqual(mockUser);
    });

    it('fails silently on error', async () => {
      (authService.getMe as jest.Mock).mockRejectedValue(new Error('fail'));

      const { result } = renderHook(() => useAuth());
      await act(async () => {
        await result.current.refreshUser();
      });
      // Should not throw
      expect(result.current.user).toBeNull();
    });
  });
});
