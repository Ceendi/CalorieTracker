import { DarkTheme, DefaultTheme, ThemeProvider } from '@react-navigation/native';
import { Stack, useRouter, useSegments } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import 'react-native-reanimated';
import '../global.css';

import { cssInterop } from 'nativewind';
import { LinearGradient } from 'expo-linear-gradient';

import { useColorScheme } from '@/hooks/use-color-scheme';
import { useAuth } from '@/hooks/useAuth';
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

  useEffect(() => {
    if (isLoading) return;
    
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
  }, [user, isLoading, segments]);

  if (isLoading) {
    return (
      <View className="flex-1 bg-white dark:bg-black justify-center items-center">
         <ActivityIndicator size="large" color="#4F46E5" />
      </View>
    );
  }

  return <>{children}</>;
}

function RootNavigation() {
  const { colorScheme } = useColorScheme();
  
  return (
    <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
      <Stack>
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="(auth)" options={{ headerShown: false }} />
        <Stack.Screen name="(onboarding)" options={{ headerShown: false }} />
      </Stack>
      <StatusBar style="auto" />
    </ThemeProvider>
  );
}

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={queryClient}>
        <AuthGuard>
          <RootNavigation />
        </AuthGuard>
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}
