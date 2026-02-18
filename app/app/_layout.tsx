import {
  DarkTheme,
  DefaultTheme,
  ThemeProvider,
} from "@react-navigation/native";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useEffect } from "react";
import "react-native-reanimated";
import "../global.css";

import { cssInterop } from "nativewind";
import { LinearGradient } from "expo-linear-gradient";

import { useColorScheme } from "@/hooks/useColorScheme";
import { useAuth } from "@/hooks/useAuth";
import { Colors } from "@/constants/theme";
import { View, ActivityIndicator } from "react-native";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { GestureHandlerRootView } from "react-native-gesture-handler";

import { AuthProtection } from "@/components/navigation/AuthProtection";

cssInterop(LinearGradient, {
  className: {
    target: "style",
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
  const { isLoading, checkSession } = useAuth();

  useEffect(() => {
    checkSession();
  }, []);

  return (
    <View
      style={{
        flex: 1,
        backgroundColor: Colors[colorScheme ?? "light"].background,
      }}
    >
      <AuthProtection />
      <ThemeProvider value={colorScheme === "dark" ? DarkTheme : DefaultTheme}>
        <Stack>
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          <Stack.Screen name="(auth)" options={{ headerShown: false }} />
          <Stack.Screen name="(onboarding)" options={{ headerShown: false }} />
          <Stack.Screen
            name="scanner"
            options={{ headerShown: false, presentation: "modal" }}
          />
          <Stack.Screen
            name="food-details"
            options={{ headerShown: true, presentation: "card" }}
          />
          <Stack.Screen
            name="manual-entry"
            options={{ headerShown: true, presentation: "card" }}
          />
        </Stack>
        <StatusBar style="auto" />
        {isLoading && (
          <View
            className="absolute inset-0 bg-background justify-center items-center"
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
            }}
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
