import React, { useState } from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { useOnboarding, Goal } from '@/hooks/useOnboarding';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLanguage } from '@/hooks/useLanguage';

export default function GoalScreen() {
  const router = useRouter();
  const { data, setData } = useOnboarding();
  const [goal, setGoal] = useState<Goal | undefined>(data.goal);
  const insets = useSafeAreaInsets();
  const { t } = useLanguage();

  const onNext = () => {
    if (!goal) return;
    setData({ goal });
    router.push('/(onboarding)/step-4-activity');
  };

  const goals: { id: Goal; label: string; icon: string }[] = [
    { id: 'lose', label: t('options.goals.lose'), icon: 'trending-down' },
    { id: 'maintain', label: t('options.goals.maintain'), icon: 'minus' },
    { id: 'gain', label: t('options.goals.gain'), icon: 'trending-up' },
  ];

  return (
    <View 
      className="flex-1 bg-gray-50 dark:bg-slate-900"
      style={{
        paddingTop: insets.top,
        paddingBottom: insets.bottom,
        paddingLeft: insets.left,
        paddingRight: insets.right,
      }}
    >
      <View className="flex-1 px-6 pt-10">
        <Text className="text-sm font-bold text-indigo-600 dark:text-indigo-400 mb-2">{t('onboarding.step3')}</Text>
        <Text className="text-3xl font-bold text-gray-900 dark:text-white mb-4">{t('onboarding.goal')}</Text>
        <Text className="text-gray-500 dark:text-gray-400 mb-8">{t('onboarding.goalSubtitle')}</Text>

        <View className="mb-6">
          {goals.map((item) => (
            <TouchableOpacity
              key={item.id}
              onPress={() => setGoal(item.id)}
              className={`mb-3 p-4 rounded-xl border flex-row items-center ${
                goal === item.id 
                  ? 'bg-indigo-50 dark:bg-indigo-900/30 border-indigo-500 dark:border-indigo-400' 
                  : 'bg-white dark:bg-slate-800 border-gray-300 dark:border-gray-700'
              }`}
            >
              <View className="ml-2">
                 <Text className={`font-semibold text-lg ${
                  goal === item.id ? 'text-indigo-600 dark:text-indigo-400' : 'text-gray-900 dark:text-white'
                }`}>
                  {item.label}
                </Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>

        <View className="flex-1 justify-end mb-64">
           <TouchableOpacity 
            onPress={onNext}
            disabled={!goal}
          >
            <LinearGradient
              colors={['#4F46E5', '#4338CA']}
              className={`rounded-xl p-4 items-center ${(!goal) ? 'opacity-50' : ''}`}
            >
              <Text className="text-white font-semibold text-lg">{t('onboarding.next')}</Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
}
