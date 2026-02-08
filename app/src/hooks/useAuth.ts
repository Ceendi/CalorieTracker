import { create } from 'zustand';
import { storageService } from '../services/storage.service';
import { authService } from '../services/auth.service';
import { User, LoginInput, RegisterInput } from '../utils/validators';
import { setOnUnauthorizedCallback } from '../services/api.client';
import { isNetworkError, isAuthError, toAppError, AppError } from '../utils/errors';
import { GoogleSignin, statusCodes } from '@react-native-google-signin/google-signin';

// Initialize Google Sign-In (should essentially be done at app start, but safe here too)
// You need to replace this with your actual Web Client ID from Google Cloud Console
GoogleSignin.configure({
  webClientId: process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID, 
  offlineAccess: true,
});

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isSignout: boolean;

  signIn: (data: LoginInput) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
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

  signInWithGoogle: async () => {
    try {
      await GoogleSignin.hasPlayServices();
      const userInfo = await GoogleSignin.signIn();
      
      if (userInfo.data?.idToken) {
        const { access_token, refresh_token } = await authService.loginGoogle(userInfo.data.idToken);
        
        await storageService.setAccessToken(access_token);
        if (refresh_token) {
          await storageService.setRefreshToken(refresh_token);
        }

        const user = await authService.getMe();
        set({ user, isSignout: false });
      } else {
        throw new Error('No ID token returned from Google');
      }
    } catch (error: any) {
      if (error.code === statusCodes.SIGN_IN_CANCELLED) {
        // user cancelled the login flow
        return;
      } else if (error.code === statusCodes.IN_PROGRESS) {
        // operation (e.g. sign in) is in progress already
        return;
      } else if (error.code === statusCodes.PLAY_SERVICES_NOT_AVAILABLE) {
        // play services not available or outdated
        throw new AppError('Google Play Services not available', 'AUTH_GOOGLE_PLAY_SERVICES');
      } else {
        // some other error happened
        throw error;
      }
    }
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
