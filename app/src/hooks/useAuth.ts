import { create } from 'zustand';
import { storageService } from '../services/storage.service';
import { authService } from '../services/auth.service';
import { User, LoginInput, RegisterInput } from '../utils/validators';
import { router } from 'expo-router';

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

export const useAuth = create<AuthState>((set, get) => ({
  user: null,
  isLoading: true,
  isSignout: false,

  signIn: async (data) => {
    try {
      set({ isLoading: true });
      const { access_token, refresh_token } = await authService.login(data);
      
      await storageService.setAccessToken(access_token);
      if (refresh_token) {
        await storageService.setRefreshToken(refresh_token);
      }

      const user = await authService.getMe();
      set({ user, isSignout: false, isLoading: false });
      
      if (user) { 
        router.replace('/(tabs)'); 
      }
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  signUp: async (data) => {
    try {
      set({ isLoading: true });
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
      set({ user, isLoading: false });
      
      router.replace({ pathname: '/(auth)/verify-email', params: { email: data.email } });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  signOut: async () => {
    try {
      await authService.logout();
    } catch(e) {
      // ignore logout errors
    }
    await storageService.clearAll();
    set({ user: null, isSignout: true });
    router.replace('/(auth)/login');
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
      router.replace('/(tabs)');
    } catch (error) {
      set({ user: null, isLoading: false });
    }
  },

  refreshUser: async () => {
      try {
        const user = await authService.getMe();
        set({ user });
      } catch (error) {
        // silently fail on refresh
      }
  }
}));
