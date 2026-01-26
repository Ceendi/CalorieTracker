import { create } from 'zustand';
import { storageService } from '../services/storage.service';
import { authService } from '../services/auth.service';
import { User, LoginInput, RegisterInput } from '../utils/validators';
import { setOnUnauthorizedCallback } from '../services/api.client';

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
      const { access_token, refresh_token } = await authService.login(data);
      
      await storageService.setAccessToken(access_token);
      if (refresh_token) {
        await storageService.setRefreshToken(refresh_token);
      }

      const user = await authService.getMe();
      set({ user, isSignout: false });
    } catch (error) {
      throw error;
    }
  },

  signUp: async (data) => {
    try {
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
    } catch (error) {
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

setOnUnauthorizedCallback(() => {
  const { user } = useAuth.getState();
  if (user) {
    useAuth.setState({ user: null, isSignout: true });
  }
});
