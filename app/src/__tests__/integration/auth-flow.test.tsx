import { renderHook, act } from '@testing-library/react-native';

// --- Service mocks ---
const mockLogin = jest.fn();
const mockRegister = jest.fn();
const mockLogout = jest.fn();
const mockGetMe = jest.fn();

jest.mock('@/services/auth.service', () => ({
  authService: {
    login: (...args: any[]) => mockLogin(...args),
    register: (...args: any[]) => mockRegister(...args),
    loginGoogle: jest.fn(),
    logout: (...args: any[]) => mockLogout(...args),
    getMe: (...args: any[]) => mockGetMe(...args),
  },
}));

jest.mock('@/services/storage.service', () => ({
  storageService: {
    setAccessToken: jest.fn(),
    setRefreshToken: jest.fn(),
    setUserId: jest.fn(),
    getAccessToken: jest.fn(async () => null),
    getRefreshToken: jest.fn(async () => null),
    clearAll: jest.fn(),
    getLanguage: jest.fn(async () => null),
  },
}));

jest.mock('@/services/api.client', () => ({
  setOnUnauthorizedCallback: jest.fn(),
  apiClient: {
    defaults: { headers: { common: {} } },
    interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } },
  },
}));

jest.mock('expo-router', () => ({
  useRouter: jest.fn(() => ({ replace: jest.fn(), push: jest.fn(), back: jest.fn(), dismissAll: jest.fn() })),
  useSegments: jest.fn(() => []),
}));

jest.mock('@/hooks/useLanguage', () => ({
  useLanguage: () => ({ t: (k: string) => k, language: 'en', setLanguage: jest.fn() }),
}));

import { useAuth } from '@/hooks/useAuth';
import { storageService } from '@/services/storage.service';

describe('Auth Flow Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset Zustand store
    useAuth.setState({ user: null, isLoading: true, isSignout: false });
  });

  it('signIn stores tokens and sets user', async () => {
    mockLogin.mockResolvedValue({
      access_token: 'at-123',
      refresh_token: 'rt-456',
    });
    mockGetMe.mockResolvedValue({
      id: 'user-1',
      email: 'test@test.com',
      is_verified: true,
    });

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      // signIn takes a LoginInput object
      await result.current.signIn({ email: 'test@test.com', password: 'password123' } as any);
    });

    expect(mockLogin).toHaveBeenCalledWith({ email: 'test@test.com', password: 'password123' });
    expect(storageService.setAccessToken).toHaveBeenCalledWith('at-123');
    expect(storageService.setRefreshToken).toHaveBeenCalledWith('rt-456');
    expect(result.current.user).toBeTruthy();
  });

  it('signIn error does not store tokens', async () => {
    mockLogin.mockRejectedValue(new Error('Invalid credentials'));

    const { result } = renderHook(() => useAuth());

    await expect(
      act(async () => {
        await result.current.signIn({ email: 'bad@test.com', password: 'wrong' } as any);
      }),
    ).rejects.toThrow();

    expect(storageService.setAccessToken).not.toHaveBeenCalled();
  });

  it('signUp calls register then login', async () => {
    mockRegister.mockResolvedValue({ id: 'new-user' });
    mockLogin.mockResolvedValue({
      access_token: 'at-new',
      refresh_token: 'rt-new',
    });
    mockGetMe.mockResolvedValue({
      id: 'new-user',
      email: 'new@test.com',
      is_verified: false,
    });

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.signUp({ email: 'new@test.com', password: 'Password1', confirmPassword: 'Password1' } as any);
    });

    expect(mockRegister).toHaveBeenCalledWith({ email: 'new@test.com', password: 'Password1', confirmPassword: 'Password1' });
    expect(mockLogin).toHaveBeenCalledWith({ username: 'new@test.com', password: 'Password1' });
  });

  it('signOut clears storage on success', async () => {
    mockLogout.mockResolvedValue(undefined);

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.signOut();
    });

    expect(mockLogout).toHaveBeenCalled();
    expect(storageService.clearAll).toHaveBeenCalled();
    expect(result.current.isSignout).toBe(true);
  });

  it('checkSession restores user from valid token', async () => {
    (storageService.getAccessToken as jest.Mock).mockResolvedValue('valid-token');
    mockGetMe.mockResolvedValue({
      id: 'user-1',
      email: 'test@test.com',
      is_verified: true,
    });

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.checkSession();
    });

    expect(mockGetMe).toHaveBeenCalled();
    expect(result.current.user).toBeTruthy();
    expect(result.current.isLoading).toBe(false);
  });

  it('checkSession with no token does not call API', async () => {
    (storageService.getAccessToken as jest.Mock).mockResolvedValue(null);

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.checkSession();
    });

    expect(mockGetMe).not.toHaveBeenCalled();
    expect(result.current.user).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('refreshUser updates user silently', async () => {
    mockGetMe.mockResolvedValue({
      id: 'user-1',
      email: 'updated@test.com',
      is_verified: true,
    });

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.refreshUser();
    });

    expect(result.current.user?.email).toBe('updated@test.com');
  });
});
