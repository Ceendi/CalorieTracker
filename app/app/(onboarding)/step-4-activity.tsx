import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, ScrollView } from 'react-native';
import { useOnboarding, ActivityLevel } from '@/hooks/useOnboarding';
import { useAuth } from '@/hooks/useAuth';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useColorScheme } from '@/hooks/useColorScheme';
import { useLanguage } from '@/hooks/useLanguage';
import { Colors } from '@/constants/theme';

export default function ActivityScreen() {
  const { data, setData, submitOnboarding, isLoading } = useOnboarding();
  const { checkSession } = useAuth();
  const [level, setLevel] = useState<ActivityLevel | undefined>(data.activityLevel);
  const insets = useSafeAreaInsets();
  const { t } = useLanguage();
  const { colorScheme } = useColorScheme();

  const onComplete = async () => {
    if (!level) return;
    setData({ activityLevel: level });
    try {
        await submitOnboarding(checkSession);
    } catch (e) {
        console.error(e);
    }
  };

  const activities: { id: ActivityLevel; label: string; desc: string }[] = [
    { id: 'sedentary', label: t('options.activities.sedentary'), desc: t('options.activityDescriptions.sedentary') },
    { id: 'light', label: t('options.activities.light'), desc: t('options.activityDescriptions.light') },
    { id: 'moderate', label: t('options.activities.moderate'), desc: t('options.activityDescriptions.moderate') },
    { id: 'high', label: t('options.activities.high'), desc: t('options.activityDescriptions.high') },
    { id: 'very_high', label: t('options.activities.very_high'), desc: t('options.activityDescriptions.very_high') },
  ];

  return (
    <View 
      className="flex-1 bg-background"
      style={{
        paddingTop: insets.top,
        paddingBottom: insets.bottom,
        paddingLeft: insets.left,
        paddingRight: insets.right,
      }}
    >
      <ScrollView contentContainerStyle={{ padding: 24, paddingTop: 40 }}>
        <Text className="text-sm font-bold text-primary mb-2">{t('onboarding.step4')}</Text>
        <Text className="text-3xl font-bold text-foreground mb-4">{t('onboarding.activity')}</Text>
        <Text className="text-muted-foreground mb-8">{t('onboarding.activitySubtitle')}</Text>

        <View className="mb-6">
          {activities.map((item) => (
            <TouchableOpacity
              key={item.id}
              onPress={() => setLevel(item.id)}
              className={`mb-3 p-4 rounded-xl border ${
                level === item.id 
                  ? 'bg-primary/10 border-primary' 
                  : 'bg-card border-border'
              }`}
            >
               <Text className={`font-semibold text-lg ${
                  level === item.id ? 'text-primary' : 'text-foreground'
                }`}>
                  {item.label}
                </Text>
                <Text className="text-muted-foreground text-sm mt-1">{item.desc}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <View className="mt-8 mb-10">
          <TouchableOpacity 
            onPress={onComplete}
            disabled={!level || isLoading}
          >
            <LinearGradient
              colors={[Colors[colorScheme ?? 'light'].primary, Colors[colorScheme ?? 'light'].primaryDark]}
              className={`rounded-xl p-4 items-center ${(!level || isLoading) ? 'opacity-50' : ''}`}
            >
              {isLoading ? (
                <ActivityIndicator color="white" />
              ) : (
                <Text className="text-white font-semibold text-lg">{t('onboarding.complete')}</Text>
              )}
            </LinearGradient>
          </TouchableOpacity>
        </View>

      </ScrollView>
    </View>
  );
}
