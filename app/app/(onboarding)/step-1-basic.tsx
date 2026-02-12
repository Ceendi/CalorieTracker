import React, { useState } from 'react';
import { View, Text, TouchableOpacity, TextInput, KeyboardAvoidingView, Platform, TouchableWithoutFeedback, Keyboard, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { useOnboarding, Gender } from '@/hooks/useOnboarding';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useColorScheme } from '@/hooks/useColorScheme';
import { useLanguage } from '@/hooks/useLanguage';
import { Colors } from '@/constants/theme';

export default function BasicInfoScreen() {
  const router = useRouter();
  const { data, setData } = useOnboarding();
  const [age, setAge] = useState(data.age?.toString() || '');
  const [gender, setGender] = useState<Gender | undefined>(data.gender);
  const insets = useSafeAreaInsets();
  const { t } = useLanguage();
  const { colorScheme } = useColorScheme();

// ... (omitting lines to keep replace call valid, targeting specific blocks)
// I need to split this into chunks because they are far apart.



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
          <View className="flex-1 px-6 pt-10">
            <ScrollView 
              showsVerticalScrollIndicator={false} 
              className="flex-1"
              keyboardShouldPersistTaps="handled"
            >
              <Text className="text-sm font-bold text-primary mb-2">{t('onboarding.step1')}</Text>
              <Text className="text-3xl font-bold text-foreground mb-4">{t('onboarding.basicDetails')}</Text>
              <Text className="text-muted-foreground mb-8">{t('onboarding.basicDetailsSubtitle')}</Text>

              <View className="mb-6">
                <Text className="text-foreground font-medium mb-2">{t('profile.age')}</Text>
                <View className="bg-card border border-border rounded-lg h-14 justify-center px-3">
                  <TextInput
                    testID="onboarding-age"
                    className="text-foreground flex-1 h-full"
                    style={{ fontSize: 18, paddingVertical: 0, includeFontPadding: false }}
                    placeholder={t('onboarding.agePlaceholder')}
                    placeholderTextColor={Colors[colorScheme ?? 'light'].placeholder}
                    keyboardType="number-pad"
                    value={age}
                    onChangeText={setAge}
                  />
                </View>
              </View>

              <View className="mb-10">
                <Text className="text-foreground font-medium mb-2">{t('onboarding.gender')}</Text>
                <View className="flex-row justify-between">
                  {genders.map((g) => (
                    <TouchableOpacity
                      key={g}
                      testID={`onboarding-gender-${g.toLowerCase()}`}
                      onPress={() => setGender(g)}
                      className={`flex-1 mx-1 p-3 rounded-xl border ${
                        gender === g 
                          ? 'bg-primary/10 border-primary' 
                          : 'bg-card border-border'
                      } items-center`}
                    >
                      <Text
                        className={`font-semibold ${
                          gender === g ? 'text-primary' : 'text-muted-foreground'
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
                testID="onboarding-next-1"
                onPress={onNext}
                disabled={!age || !gender}
              >
                <LinearGradient
                  colors={[Colors[colorScheme ?? 'light'].primary, Colors[colorScheme ?? 'light'].primaryDark]}
                  className={`rounded-xl p-4 items-center ${(!age || !gender) ? 'opacity-50' : ''}`}
                >
                  <Text className="text-white font-semibold text-lg">{t('onboarding.next')}</Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>
          </View>
      </KeyboardAvoidingView>
    </View>
  );
}
