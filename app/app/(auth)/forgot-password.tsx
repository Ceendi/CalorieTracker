import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, Platform, KeyboardAvoidingView, TouchableWithoutFeedback, Keyboard, Alert } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { createForgotPasswordSchema, ForgotPasswordInput } from '@/utils/validators';
import { authService } from '@/services/auth.service';
import { ControlledInput } from '@/components/ui/ControlledInput';
import { LinearGradient } from 'expo-linear-gradient';
import { useLanguage } from '@/hooks/useLanguage';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { useColorScheme } from '@/hooks/use-color-scheme';

export default function ForgotPasswordScreen() {
  const router = useRouter();
  const { t } = useLanguage();
  const insets = useSafeAreaInsets();
  const { colorScheme } = useColorScheme();
  
  const [isLoading, setIsLoading] = useState(false);
  const [isSent, setIsSent] = useState(false);

  const forgotPasswordSchema = React.useMemo(() => createForgotPasswordSchema(t), [t]);

  const { control, handleSubmit, formState: { errors }, getValues } = useForm<ForgotPasswordInput>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: '',
    },
  });

  const onSubmit = async (data: ForgotPasswordInput) => {
    try {
      setIsLoading(true);
      await authService.forgotPassword(data.email);
      setIsSent(true);
      setIsLoading(false);
    } catch (error: any) {
      setIsLoading(false);
      if (error.response?.status === 404) {
          Alert.alert(t('profile.error'), t('auth.errorEmailNotFound'));
      } else {
          Alert.alert(t('profile.error'), t('auth.unexpectedError'));
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
      <View style={{ position: 'absolute', top: insets.top + 10, left: 20, zIndex: 10 }}>
        <TouchableOpacity 
          onPress={() => router.back()} 
          className="p-2 bg-white/80 dark:bg-slate-800/80 rounded-full border border-gray-200 dark:border-gray-700 shadow-sm"
        >
          <IconSymbol name="chevron.left" size={24} color={colorScheme === 'dark' ? '#fff' : '#4B5563'} />
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
      >
        <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
          <View className="flex-1 px-8 justify-center">
            {isSent ? (
              <View className="items-center w-full">
                <View className="w-24 h-24 bg-emerald-100 dark:bg-emerald-900/40 rounded-full items-center justify-center mb-8 shadow-sm">
                    <IconSymbol name="envelope.fill" size={48} color="#10B981" />
                </View>
                <Text className="text-3xl font-bold text-gray-900 dark:text-white text-center mb-3">
                  {t('auth.checkEmail')}
                </Text>
                <View className="px-2">
                  <Text className="text-gray-500 dark:text-gray-400 text-center text-lg leading-6">
                    {t('auth.checkEmailSubtitle')}{'\n'}
                    <Text className="font-bold text-gray-900 dark:text-white">
                      {getValues('email')}
                    </Text>
                  </Text>
                </View>
                
                <TouchableOpacity 
                  className="mt-12 w-full"
                  onPress={() => router.replace('/(auth)/login')}
                >
                   <LinearGradient
                    colors={['#4F46E5', '#4338CA']}
                    className="rounded-xl p-4 items-center shadow-md"
                  >
                    <Text className="text-white font-bold text-lg">
                      {t('auth.backToLogin')}
                    </Text>
                  </LinearGradient>
                </TouchableOpacity>
              </View>
            ) : (
              <>
                <View className="mb-8">
                  <Text className="text-3xl font-bold text-gray-900 dark:text-white">{t('auth.resetPasswordTitle')}</Text>
                  <Text className="text-gray-500 dark:text-gray-400 mt-2">{t('auth.resetPasswordSubtitle')}</Text>
                </View>

                <ControlledInput
                  control={control}
                  name="email"
                  label={t('auth.email')}
                  placeholder={t('auth.emailPlaceholder')}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  error={errors.email?.message}
                />

                <TouchableOpacity 
                  className="mt-6"
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
                     <Text className="text-white font-semibold text-lg">{t('auth.sendResetLink')}</Text>
                   )}
                  </LinearGradient>
                </TouchableOpacity>
              </>
            )}
          </View>
        </TouchableWithoutFeedback>
      </KeyboardAvoidingView>
    </View>
  );
}
