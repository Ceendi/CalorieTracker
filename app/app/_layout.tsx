import { DarkTheme, DefaultTheme, ThemeProvider } from '@react-navigation/native';
import { Stack, useRouter, useSegments, useRootNavigationState } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import 'react-native-reanimated';
import '../global.css';

import { cssInterop } from 'nativewind';
import { LinearGradient } from 'expo-linear-gradient';

import { useColorScheme } from '@/hooks/useColorScheme';
import { useAuth } from '@/hooks/useAuth';
import { Colors } from '@/constants/theme';
import { View, ActivityIndicator } from 'react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

cssInterop(LinearGradient, {
  className: {
    target: 'style',
  },
});

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1 minute default
      gcTime: 1000 * 60 * 5, // 5 minutes cache
      retry: 2,
      refetchOnWindowFocus: false, // Important for mobile
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
});

function InitialLayout() {
  const { colorScheme } = useColorScheme();
  const { user, isLoading, checkSession } = useAuth();
  const segments = useSegments();
  const router = useRouter();
  const navigationState = useRootNavigationState();

  useEffect(() => {
    checkSession();
  }, []);

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

  return (
    <View className={`flex-1 ${colorScheme === 'dark' ? 'dark' : ''}`}>
      <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
        <Stack>
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          <Stack.Screen name="(auth)" options={{ headerShown: false }} />
          <Stack.Screen name="(onboarding)" options={{ headerShown: false }} />
          <Stack.Screen name="scanner" options={{ headerShown: false, presentation: 'modal' }} />
          <Stack.Screen name="food-details" options={{ headerShown: true, presentation: 'card' }} />
          <Stack.Screen name="manual-entry" options={{ headerShown: true, presentation: 'card' }} />
        </Stack>
        <StatusBar style="auto" />
        {isLoading && (
          <View 
            className="absolute inset-0 bg-background justify-center items-center"
            style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
          >
            <ActivityIndicator size="large" color={Colors.light.tint} />
          </View>
        )}
      </ThemeProvider>
    </View>
  );
}

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={queryClient}>
        <InitialLayout />
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}
