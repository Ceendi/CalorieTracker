import React, { useState, useMemo } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, Platform, KeyboardAvoidingView, TouchableWithoutFeedback, Keyboard } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { createLoginSchema, LoginInput } from '@/utils/validators';
import { useAuth } from '@/hooks/useAuth';
import { ControlledInput } from '@/components/ui/ControlledInput';
import { LinearGradient } from 'expo-linear-gradient';
import { useLanguage } from '@/hooks/useLanguage';
import { isAxiosError } from 'axios';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { SettingsModal } from '@/components/profile/SettingsModal';

export default function LoginScreen() {
  const router = useRouter();
  const { signIn } = useAuth();
  const { t } = useLanguage();
  const insets = useSafeAreaInsets();
  const { colorScheme } = useColorScheme();
  const [settingsVisible, setSettingsVisible] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  
  const loginSchema = useMemo(() => createLoginSchema(t), [t]);

  const { control, handleSubmit, formState: { errors } } = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: '',
      password: '',
    },
  });

  const onSubmit = async (data: LoginInput) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      await signIn(data);
    } catch (error: any) {
      if (isAxiosError(error) && (error.response?.status === 400 || error.response?.status === 401)) {
        setErrorMsg(t('auth.validation.invalidCredentials'));
      } else {
        setErrorMsg(t('auth.unexpectedError'));
      }
    } finally {
      setIsLoading(false);
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
          <View className="flex-1 px-6 justify-center">
            <View className="mb-8">
              <Text className="text-3xl font-bold text-gray-900 dark:text-white">{t('auth.welcomeBack')}</Text>
              <Text className="text-gray-500 dark:text-gray-400 mt-2">{t('auth.signInSubtitle')}</Text>
            </View>

            {errorMsg && (
              <View className="mb-4 p-3 bg-red-100 border border-red-400 rounded-lg">
                <Text className="text-red-700 text-center">{errorMsg}</Text>
              </View>
            )}

            <ControlledInput
              control={control}
              name="username"
              label={t('auth.email')}
              placeholder={t('auth.emailPlaceholder')}
              keyboardType="email-address"
              autoCapitalize="none"
              error={errors.username?.message}
            />

            <ControlledInput
              control={control}
              name="password"
              label={t('auth.password')}
              placeholder={t('auth.passwordPlaceholder')}
              secureTextEntry
              error={errors.password?.message}
            />

            <TouchableOpacity 
              onPress={() => router.push('/(auth)/forgot-password')}
              className="self-end mt-2"
            >
              <Text className="text-indigo-600 dark:text-indigo-400 font-medium">
                {t('auth.forgotPassword')}
              </Text>
            </TouchableOpacity>

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
                 <Text className="text-white font-semibold text-lg">{t('auth.signIn')}</Text>
               )}
              </LinearGradient>
            </TouchableOpacity>

            <View className="flex-row justify-center mt-4">
              <Text className="text-gray-600 dark:text-gray-400">{t('auth.noAccount')} </Text>
              <TouchableOpacity onPress={() => router.push('/(auth)/register')}>
                <Text className="text-indigo-600 dark:text-indigo-400 font-semibold">{t('auth.signUp')}</Text>
              </TouchableOpacity>
            </View>
          </View>
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
