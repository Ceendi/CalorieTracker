import React, { useState } from 'react';
import { View, Text, TouchableOpacity, TextInput, KeyboardAvoidingView, Platform, TouchableWithoutFeedback, Keyboard, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { useOnboarding } from '@/hooks/useOnboarding';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useColorScheme } from '@/hooks/useColorScheme';
import { useLanguage } from '@/hooks/useLanguage';
import { Colors } from '@/constants/theme';

export default function MeasurementsScreen() {
  const router = useRouter();
  const { data, setData } = useOnboarding();
  const [height, setHeight] = useState(data.height?.toString() || '');
  const [weight, setWeight] = useState(data.weight?.toString() || '');
  const insets = useSafeAreaInsets();
  const { t } = useLanguage();
  const { colorScheme } = useColorScheme();

  const onNext = () => {
    if (!height || !weight) return;
    setData({ height: parseFloat(height), weight: parseFloat(weight) });
    router.push('/(onboarding)/step-3-goal');
  };

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
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'} 
        style={{ flex: 1 }}
      >
        <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
          <View className="flex-1 px-6 pt-10">
            <ScrollView showsVerticalScrollIndicator={false} className="flex-1">
              <Text className="text-sm font-bold text-primary mb-2">{t('onboarding.step2')}</Text>
              <Text className="text-3xl font-bold text-foreground mb-4">{t('onboarding.measurements')}</Text>
              <Text className="text-muted-foreground mb-8">{t('onboarding.measurementsSubtitle')}</Text>

              <View className="mb-6">
                <Text className="text-foreground font-medium mb-2">{t('profile.height')}</Text>
                <View className="flex-row items-center">
                  <View className="flex-1 bg-card border border-border rounded-lg h-14 justify-center px-3">
                    <TextInput
                      testID="onboarding-height"
                      className="text-foreground flex-1 h-full"
                      style={{ fontSize: 18, paddingVertical: 0, includeFontPadding: false }}
                      placeholder="175"
                      placeholderTextColor={Colors[colorScheme ?? 'light'].placeholder}
                      keyboardType="number-pad"
                      value={height}
                      onChangeText={setHeight}
                    />
                  </View>
                  <Text className="ml-3 text-muted-foreground font-medium text-lg">cm</Text>
                </View>
              </View>

              <View className="mb-6">
                <Text className="text-foreground font-medium mb-2">{t('profile.weight')}</Text>
                <View className="flex-row items-center">
                  <View className="flex-1 bg-card border border-border rounded-lg h-14 justify-center px-3">
                    <TextInput
                      testID="onboarding-weight"
                      className="text-foreground flex-1 h-full"
                      style={{ fontSize: 18, paddingVertical: 0, includeFontPadding: false }}
                      placeholder="70"
                      placeholderTextColor={Colors[colorScheme ?? 'light'].placeholder}
                      keyboardType="number-pad"
                      value={weight}
                      onChangeText={setWeight}
                    />
                  </View>
                  <Text className="ml-3 text-muted-foreground font-medium text-lg">kg</Text>
                </View>
              </View>
            </ScrollView>

            <View className="py-6 pb-10">
              <TouchableOpacity
                testID="onboarding-next-2"
                onPress={onNext}
                disabled={!height || !weight}
              >
                <LinearGradient
                  colors={[Colors[colorScheme ?? 'light'].primary, Colors[colorScheme ?? 'light'].primaryDark]}
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
