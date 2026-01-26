import { Tabs } from 'expo-router';
import React from 'react';
import { TouchableOpacity, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

import { HapticTab } from '@/components/HapticTab';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { useLanguage } from '@/hooks/useLanguage';

export default function TabLayout() {
  const { colorScheme } = useColorScheme();
  const { t } = useLanguage();

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: Colors[colorScheme === 'dark' ? 'dark' : 'light'].tint,
        headerShown: false,
        tabBarButton: HapticTab,
        tabBarStyle: {
          position: 'absolute',
          borderTopWidth: 0,
          elevation: 0,
          height: 90,
          paddingBottom: 30,
          backgroundColor: colorScheme === 'dark' ? '#1e293b' : '#ffffff',
        },
      }}>
      <Tabs.Screen
        name="index"
        options={{
          title: t('tabs.home'),
          tabBarIcon: ({ color }) => <IconSymbol size={28} name="house.fill" color={color} />,
        }}
      />
      <Tabs.Screen
        name="plan"
        options={{
          title: t('tabs.plan'),
          tabBarIcon: ({ color }) => <IconSymbol size={28} name="calendar" color={color} />,
        }}
      />
      <Tabs.Screen
        name="add"
        options={{
          title: '',
          tabBarButton: (props) => {
            const { delayLongPress, disabled, ...rest } = props;
            return (
              <TouchableOpacity
                {...rest as any}
                delayLongPress={delayLongPress ?? undefined}
                disabled={disabled ?? undefined}
                style={styles.customButtonContainer}
              >
                <LinearGradient
                  colors={[Colors.light.tint, '#4338CA']}
                  style={styles.customButton}
                >
                  <IconSymbol size={30} name="plus" color="#FFFFFF" />
                </LinearGradient>
              </TouchableOpacity>
            );
          },
        }}
      />
      <Tabs.Screen
        name="stats"
        options={{
          title: t('tabs.stats'),
          tabBarIcon: ({ color }) => <IconSymbol size={28} name="chart.bar.fill" color={color} />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: t('tabs.profile'),
          tabBarIcon: ({ color }) => <IconSymbol size={28} name="person.fill" color={color} />,
        }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  customButtonContainer: {
    top: -20,
    justifyContent: 'center',
    alignItems: 'center',
    width: 70, 
    height: 70,
  },
  customButton: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 5,
  },
});
