import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, ScrollView, Platform, KeyboardAvoidingView, TouchableWithoutFeedback, Keyboard } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { registerSchema, RegisterInput } from '@/utils/validators';
import { useAuth } from '@/hooks/useAuth';
import { ControlledInput } from '@/components/ui/ControlledInput';
import { LinearGradient } from 'expo-linear-gradient';
import { isAxiosError } from 'axios';
import { useLanguage } from '@/hooks/useLanguage';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { SettingsModal } from '@/components/profile/SettingsModal';

export default function RegisterScreen() {
  const router = useRouter();
  const { signUp, isLoading } = useAuth();
  const { t } = useLanguage();
  const insets = useSafeAreaInsets();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const { colorScheme } = useColorScheme();
  const [settingsVisible, setSettingsVisible] = useState(false);
  
  const { control, handleSubmit, formState: { errors } } = useForm<RegisterInput>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterInput) => {
    setErrorMsg(null);
    try {
      await signUp(data);
    } catch (error: any) {
      if (isAxiosError(error)) {
        const responseData = error.response?.data;
        const detail = responseData?.detail;

        if (detail === 'REGISTER_USER_ALREADY_EXISTS') {
            setErrorMsg(t('auth.accountExists'));
        } else if (typeof detail === 'string') {
            setErrorMsg(detail);
        } else if (Array.isArray(detail)) {
            const messages = detail.map((err: any) => err.msg || 'Invalid input').join('\n');
            setErrorMsg(messages);
        } else if (error.response?.status === 400) {
            setErrorMsg(t('auth.invalidData'));
        } else {
            setErrorMsg(t('auth.networkError'));
        }
      } else {
          setErrorMsg(t('auth.unexpectedError'));
      }
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
      <View style={{ position: 'absolute', top: insets.top + 10, right: 20, zIndex: 10 }}>
        <TouchableOpacity 
          onPress={() => setSettingsVisible(true)} 
          className="p-2 bg-white/80 dark:bg-slate-800/80 rounded-full border border-gray-200 dark:border-gray-700 shadow-sm"
        >
          <IconSymbol name="gear" size={24} color={colorScheme === 'dark' ? '#fff' : '#4B5563'} />
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'} 
        style={{ flex: 1 }}
      >
        <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
          <ScrollView contentContainerStyle={{ flexGrow: 1, justifyContent: 'center' }} className="px-6" keyboardShouldPersistTaps="handled">
            <View className="mb-8">
              <Text className="text-3xl font-bold text-gray-900 dark:text-white">{t('auth.createAccount')}</Text>
              <Text className="text-gray-500 dark:text-gray-400 mt-2">{t('auth.signUpSubtitle')}</Text>
            </View>

            {errorMsg && (
                <View className="mb-4 p-3 bg-red-100 border border-red-400 rounded-lg">
                    <Text className="text-red-700 text-center">{errorMsg}</Text>
                </View>
            )}

            <ControlledInput
              control={control}
              name="email"
              label={t('auth.email')}
              placeholder={t('auth.emailPlaceholder')}
              keyboardType="email-address"
              autoCapitalize="none"
              error={errors.email?.message}
            />

            <ControlledInput
              control={control}
              name="password"
              label={t('auth.password')}
              placeholder={t('auth.minPasswordPlaceholder')}
              secureTextEntry
              error={errors.password?.message}
            />

            <ControlledInput
              control={control}
              name="confirmPassword"
              label={t('auth.confirmPassword')}
              placeholder={t('auth.confirmPasswordPlaceholder')}
              secureTextEntry
              error={errors.confirmPassword?.message}
            />

            <TouchableOpacity 
              className="mt-6 mb-4"
              onPress={handleSubmit(onSubmit)}
              disabled={isLoading}
            >
              <LinearGradient
                colors={['#4F46E5', '#4338CA']}
                className="rounded-xl p-4 items-center"
              >
               {isLoading ? (
                 <ActivityIndicator color="white" />
               ) : (
                 <Text className="text-white font-semibold text-lg">{t('auth.signUp')}</Text>
               )}
              </LinearGradient>
            </TouchableOpacity>

            <View className="flex-row justify-center mt-4 mb-8">
              <Text className="text-gray-600 dark:text-gray-400">{t('auth.alreadyHaveAccount')} </Text>
              <TouchableOpacity onPress={() => router.push('/(auth)/login')}>
                <Text className="text-indigo-600 dark:text-indigo-400 font-semibold">{t('auth.signIn')}</Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </TouchableWithoutFeedback>
      </KeyboardAvoidingView>

      <SettingsModal 
        visible={settingsVisible} 
        onClose={() => setSettingsVisible(false)} 
        mode="public" 
      />
    </View>
  );
}
