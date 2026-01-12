import { DarkTheme, DefaultTheme, ThemeProvider } from '@react-navigation/native';
import { Stack, useRouter, useSegments } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import 'react-native-reanimated';
import '../global.css';

import { cssInterop } from 'nativewind';
import { LinearGradient } from 'expo-linear-gradient';

cssInterop(LinearGradient, {
  className: {
    target: 'style',
  },
});

import { useColorScheme } from '@/hooks/use-color-scheme';
import { useAuth } from '@/hooks/useAuth';
import { View, ActivityIndicator } from 'react-native';

function RootLayoutNav() {
  const { colorScheme } = useColorScheme();
  const { user, isLoading, checkSession } = useAuth();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    checkSession();
  }, []);

  useEffect(() => {
    if (isLoading) return;
    
    if (!segments || (segments as string[]).length === 0) return;

    const inAuthGroup = segments[0] === '(auth)';
    const inOnboardingGroup = segments[0] === '(onboarding)';
    const inTabsGroup = segments[0] === '(tabs)';

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
  }, [user, isLoading, segments]);

  return (
    <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
      <Stack>
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="(auth)" options={{ headerShown: false }} />
        <Stack.Screen name="(onboarding)" options={{ headerShown: false }} />
      </Stack>
      <StatusBar style="auto" />
      
      {isLoading && (
        <View className="absolute inset-0 bg-white/80 dark:bg-black/80 justify-center items-center z-50">
           <ActivityIndicator size="large" color="#4F46E5" />
        </View>
      )}
    </ThemeProvider>
  );
}

export default function RootLayout() {
  return <RootLayoutNav />;
}
