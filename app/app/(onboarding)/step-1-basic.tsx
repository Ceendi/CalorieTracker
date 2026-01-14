import React, { useState } from 'react';
import { View, Text, TouchableOpacity, TextInput, KeyboardAvoidingView, Platform, TouchableWithoutFeedback, Keyboard, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { useOnboarding, Gender } from '@/hooks/useOnboarding';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLanguage } from '@/hooks/useLanguage';

export default function BasicInfoScreen() {
  const router = useRouter();
  const { data, setData } = useOnboarding();
  const [age, setAge] = useState(data.age?.toString() || '');
  const [gender, setGender] = useState<Gender | undefined>(data.gender);
  const insets = useSafeAreaInsets();
  const { t } = useLanguage();

  const onNext = () => {
    if (!age || !gender) return;
    setData({ age: parseInt(age), gender });
    router.push('/(onboarding)/step-2-measurements');
  };

  const genders: Gender[] = ['Male', 'Female', 'Other'];
  
  const getGenderLabel = (g: Gender) => {
    switch(g) {
      case 'Male': return t('onboarding.male');
      case 'Female': return t('onboarding.female');
      case 'Other': return t('onboarding.other');
    }
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
              <Text className="text-sm font-bold text-indigo-600 dark:text-indigo-400 mb-2">{t('onboarding.step1')}</Text>
              <Text className="text-3xl font-bold text-gray-900 dark:text-white mb-4">{t('onboarding.basicDetails')}</Text>
              <Text className="text-gray-500 dark:text-gray-400 mb-8">{t('onboarding.basicDetailsSubtitle')}</Text>

              <View className="mb-6">
                <Text className="text-gray-700 dark:text-gray-300 font-medium mb-2">{t('profile.age')}</Text>
                <View className="bg-white dark:bg-slate-800 border border-gray-300 dark:border-gray-700 rounded-lg h-14 justify-center px-3">
                  <TextInput
                    className="text-gray-900 dark:text-white flex-1 h-full"
                    style={{ fontSize: 18, paddingVertical: 0, includeFontPadding: false }}
                    placeholder={t('onboarding.agePlaceholder')}
                    placeholderTextColor="#9CA3AF"
                    keyboardType="number-pad"
                    value={age}
                    onChangeText={setAge}
                  />
                </View>
              </View>

              <View className="mb-10">
                <Text className="text-gray-700 dark:text-gray-300 font-medium mb-2">{t('onboarding.gender')}</Text>
                <View className="flex-row justify-between">
                  {genders.map((g) => (
                    <TouchableOpacity
                      key={g}
                      onPress={() => setGender(g)}
                      className={`flex-1 mx-1 p-3 rounded-xl border ${
                        gender === g 
                          ? 'bg-indigo-50 dark:bg-indigo-900/30 border-indigo-500 dark:border-indigo-400' 
                          : 'bg-white dark:bg-slate-800 border-gray-300 dark:border-gray-700'
                      } items-center`}
                    >
                      <Text
                        className={`font-semibold ${
                          gender === g ? 'text-indigo-600 dark:text-indigo-400' : 'text-gray-600 dark:text-gray-300'
                        }`}
                      >
                        {getGenderLabel(g)}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            </ScrollView>

            <View className="py-6 pb-10">
              <TouchableOpacity 
                onPress={onNext}
                disabled={!age || !gender}
              >
                <LinearGradient
                  colors={['#4F46E5', '#4338CA']}
                  className={`rounded-xl p-4 items-center ${(!age || !gender) ? 'opacity-50' : ''}`}
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
