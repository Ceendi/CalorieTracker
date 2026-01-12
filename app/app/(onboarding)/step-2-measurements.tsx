import React, { useState } from 'react';
import { View, Text, TouchableOpacity, TextInput, KeyboardAvoidingView, Platform, TouchableWithoutFeedback, Keyboard, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { useOnboarding } from '@/hooks/useOnboarding';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLanguage } from '@/hooks/useLanguage';

export default function MeasurementsScreen() {
  const router = useRouter();
  const { data, setData } = useOnboarding();
  const [height, setHeight] = useState(data.height?.toString() || '');
  const [weight, setWeight] = useState(data.weight?.toString() || '');
  const insets = useSafeAreaInsets();
  const { t } = useLanguage();

  const onNext = () => {
    if (!height || !weight) return;
    setData({ height: parseFloat(height), weight: parseFloat(weight) });
    router.push('/(onboarding)/step-3-goal');
  };

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
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'} 
        style={{ flex: 1 }}
      >
        <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
          <View className="flex-1 px-6 pt-10">
            <ScrollView showsVerticalScrollIndicator={false} className="flex-1">
              <Text className="text-sm font-bold text-indigo-600 dark:text-indigo-400 mb-2">{t('onboarding.step2')}</Text>
              <Text className="text-3xl font-bold text-gray-900 dark:text-white mb-4">{t('onboarding.measurements')}</Text>
              <Text className="text-gray-500 dark:text-gray-400 mb-8">{t('onboarding.measurementsSubtitle')}</Text>

              <View className="mb-6">
                <Text className="text-gray-700 dark:text-gray-300 font-medium mb-2">{t('profile.height')}</Text>
                <View className="flex-row items-center">
                  <TextInput
                    className="flex-1 bg-white dark:bg-slate-800 border border-gray-300 dark:border-gray-700 rounded-lg p-3 text-lg text-gray-900 dark:text-white"
                    placeholder="175"
                    placeholderTextColor="#9CA3AF"
                    keyboardType="number-pad"
                    value={height}
                    onChangeText={setHeight}
                  />
                  <Text className="ml-3 text-gray-500 dark:text-gray-400 font-medium text-lg">cm</Text>
                </View>
              </View>

              <View className="mb-6">
                <Text className="text-gray-700 dark:text-gray-300 font-medium mb-2">{t('profile.weight')}</Text>
                <View className="flex-row items-center">
                  <TextInput
                    className="flex-1 bg-white dark:bg-slate-800 border border-gray-300 dark:border-gray-700 rounded-lg p-3 text-lg text-gray-900 dark:text-white"
                    placeholder="70"
                    placeholderTextColor="#9CA3AF"
                    keyboardType="number-pad"
                    value={weight}
                    onChangeText={setWeight}
                  />
                  <Text className="ml-3 text-gray-500 dark:text-gray-400 font-medium text-lg">kg</Text>
                </View>
              </View>
            </ScrollView>

            <View className="py-6 pb-10">
              <TouchableOpacity 
                onPress={onNext}
                disabled={!height || !weight}
              >
                <LinearGradient
                  colors={['#4F46E5', '#4338CA']}
                  className={`rounded-xl p-4 items-center ${(!height || !weight) ? 'opacity-50' : ''}`}
                >
                  <Text className="text-white font-semibold text-lg">{t('onboarding.next')}</Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>
          </View>
        </TouchableWithoutFeedback>
      </KeyboardAvoidingView>
    </View>
  );
}
