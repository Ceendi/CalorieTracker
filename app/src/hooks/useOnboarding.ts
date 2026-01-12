import { create } from 'zustand';
import { apiClient } from '@/services/api.client';

export type Gender = 'Male' | 'Female' | 'Other';
export type Goal = 'lose' | 'maintain' | 'gain';
export type ActivityLevel = 'sedentary' | 'light' | 'moderate' | 'high' | 'very_high';

export interface OnboardingData {
  age?: number;
  gender?: Gender;
  height?: number; // cm
  weight?: number; // kg
  goal?: Goal;
  activityLevel?: ActivityLevel;
}

interface OnboardingState {
  data: OnboardingData;
  setData: (data: Partial<OnboardingData>) => void;
  submitOnboarding: () => Promise<void>;
  isLoading: boolean;
}

export const useOnboarding = create<OnboardingState>((set, get) => ({
  data: {},
  isLoading: false,
  setData: (newData) => {
    set((state) => ({ data: { ...state.data, ...newData } }));
  },
  submitOnboarding: async () => {
    try {
      set({ isLoading: true });
      const { data } = get();
      
      const { activityLevel, ...otherData } = data;

      await apiClient.patch('/users/me', {
        ...otherData,
        activity_level: activityLevel,
        is_onboarded: true
      });
      
      const { checkSession } = require('./useAuth').useAuth.getState();
      await checkSession();
      
      set({ isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  }
}));
