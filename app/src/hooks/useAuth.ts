import { create } from 'zustand';
import { storageService } from '../services/storage.service';
import { authService } from '../services/auth.service';
import { User, LoginInput, RegisterInput } from '../utils/validators';
import { setOnUnauthorizedCallback } from '../services/api.client';
import { isNetworkError, isAuthError, toAppError } from '../utils/errors';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isSignout: boolean;

  signIn: (data: LoginInput) => Promise<void>;
  signUp: (data: RegisterInput) => Promise<void>;
  signOut: () => Promise<void>;
  checkSession: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  isSignout: false,

  signIn: async (data) => {
    const { access_token, refresh_token } = await authService.login(data);

    await storageService.setAccessToken(access_token);
    if (refresh_token) {
      await storageService.setRefreshToken(refresh_token);
    }

    const user = await authService.getMe();
    set({ user, isSignout: false });
  },

  signUp: async (data) => {
    await authService.register(data);

    const { access_token, refresh_token } = await authService.login({
      username: data.email,
      password: data.password
    });

    await storageService.setAccessToken(access_token);
    if (refresh_token) {
      await storageService.setRefreshToken(refresh_token);
    }

    const user = await authService.getMe();
    set({ user });
  },

  signOut: async () => {
    await authService.logout();
    await storageService.clearAll();
    set({ user: null, isSignout: true });
  },

  checkSession: async () => {
    try {
      set({ isLoading: true });
      const token = await storageService.getAccessToken();

      if (!token) {
        set({ user: null, isLoading: false });
        return;
      }

      const user = await authService.getMe();
      set({ user, isLoading: false });
    } catch (error) {
      const appError = toAppError(error);

      if (isAuthError(error)) {
        // Token expired or invalid - clear storage and logout
        await storageService.clearAll();
        set({ user: null, isLoading: false });
      } else if (isNetworkError(error)) {
        // Network error - keep session, user might be offline
        set({ isLoading: false });
      } else {
        // Other error - log and stop loading without clearing session
        console.error('Session check failed:', appError.message);
        set({ isLoading: false });
      }
    }
  },

  refreshUser: async () => {
    try {
      const user = await authService.getMe();
      set({ user });
    } catch (error) {
      // Silently fail on refresh - user data will be stale but app continues
      console.warn('User refresh failed:', toAppError(error).message);
    }
  }
}));

setOnUnauthorizedCallback(() => {
  const { user } = useAuth.getState();
  if (user) {
    useAuth.setState({ user: null, isSignout: true });
  }
});
