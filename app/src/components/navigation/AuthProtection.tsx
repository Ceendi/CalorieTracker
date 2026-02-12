import { useEffect } from 'react';
import { useRouter, useSegments, useRootNavigationState } from 'expo-router';
import { useAuth } from '@/hooks/useAuth';

export function AuthProtection() {
  const { user, isLoading } = useAuth();
  const segments = useSegments();
  const router = useRouter();
  const navigationState = useRootNavigationState();

  useEffect(() => {
    if (isLoading) return;
    if (!navigationState?.key) return;

    if (!segments || (segments as string[]).length === 0) return;

    const inAuthGroup = segments[0] === '(auth)';
    const inOnboardingGroup = segments[0] === '(onboarding)';

    if (!user && !inAuthGroup) {
      router.replace('/(auth)/login');
    } else if (user && !user.is_verified) {
      const isVerify = segments[0] === '(auth)' && segments[1] === 'verify-email';
      if (!isVerify) {
        router.replace({ pathname: '/(auth)/verify-email', params: { email: user.email } });
      }
    } else if (user && !user.is_onboarded && !inOnboardingGroup) {
      router.replace('/(onboarding)/step-1-basic');
    } else if (user && inAuthGroup) {
      if (!user.is_onboarded) {
        router.replace('/(onboarding)/step-1-basic');
      } else {
        router.replace('/(tabs)');
      }
    } else if (user && inOnboardingGroup && user.is_onboarded) {
      router.replace('/(tabs)');
    }
  }, [user, segments, isLoading, navigationState?.key]);

  return null;
}
