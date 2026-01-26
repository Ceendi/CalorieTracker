import { Stack } from 'expo-router';


export default function OnboardingLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="step-1-basic" />
      <Stack.Screen name="step-2-measurements" />
      <Stack.Screen name="step-3-goal" />
      <Stack.Screen name="step-4-activity" />
    </Stack>
  );
}
