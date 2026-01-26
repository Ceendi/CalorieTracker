import { DarkTheme, DefaultTheme, ThemeProvider } from '@react-navigation/native';
import { Stack, useRouter, useSegments, useRootNavigationState } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import 'react-native-reanimated';
import '../global.css';

import { cssInterop } from 'nativewind';
import { LinearGradient } from 'expo-linear-gradient';

import { useColorScheme } from '@/hooks/use-color-scheme';
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

const queryClient = new QueryClient();

function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, isLoading, checkSession } = useAuth();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    checkSession();
  }, []);

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

  if (isLoading) {
    return (
      <View className="flex-1 bg-background justify-center items-center">
         <ActivityIndicator size="large" color={Colors.light.tint} />
      </View>
    );
  }

  return <>{children}</>;
}

function ThemeLayout({ children }: { children: React.ReactNode }) {
  const { colorScheme } = useColorScheme();
  return (
    <View className={`flex-1 ${colorScheme === 'dark' ? 'dark' : ''}`}>
      <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
        {children}
        <StatusBar style="auto" />
      </ThemeProvider>
    </View>
  );
}

function RootNavigation() {
  return (
    <Stack>
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen name="(auth)" options={{ headerShown: false }} />
      <Stack.Screen name="(onboarding)" options={{ headerShown: false }} />
      <Stack.Screen name="scanner" options={{ headerShown: false, presentation: 'modal' }} />
      <Stack.Screen name="food-details" options={{ headerShown: true, presentation: 'card' }} />
      <Stack.Screen name="manual-entry" options={{ headerShown: true, presentation: 'card' }} />
    </Stack>
  );
}

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={queryClient}>
        <AuthGuard>
          <ThemeLayout>
             <RootNavigation />
          </ThemeLayout>
        </AuthGuard>
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}
