import React from 'react';
import { View } from 'react-native';
import { useColorScheme } from '@/hooks/useColorScheme';

interface ThemeWrapperProps {
  children: React.ReactNode;
}

export function ThemeWrapper({ children }: ThemeWrapperProps) {
  const { colorScheme } = useColorScheme();
  return (
    <View style={{ flex: 1 }} className={colorScheme === 'dark' ? 'dark' : ''}>
      {children}
    </View>
  );
}
