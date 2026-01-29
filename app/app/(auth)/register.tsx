import React, { useState, useMemo } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, ScrollView, Platform, KeyboardAvoidingView, TouchableWithoutFeedback, Keyboard } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { createRegisterSchema, RegisterInput } from '@/utils/validators';
import { useAuth } from '@/hooks/useAuth';
import { ControlledInput } from '@/components/ui/ControlledInput';
import { LinearGradient } from 'expo-linear-gradient';
import { isAxiosError } from 'axios';
import { useLanguage } from '@/hooks/useLanguage';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { useColorScheme } from '@/hooks/useColorScheme';
import { SettingsModal } from '@/components/profile/SettingsModal';
import { Colors } from '@/constants/theme';

export default function RegisterScreen() {
  const router = useRouter();
  const { signUp } = useAuth();
  const { t } = useLanguage();
  const insets = useSafeAreaInsets();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const { colorScheme } = useColorScheme();
  const [settingsVisible, setSettingsVisible] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const registerSchema = useMemo(() => createRegisterSchema(t), [t]);

  const { control, handleSubmit, formState: { errors } } = useForm<RegisterInput>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      password: '',
      confirmPassword: '',
    },
  });

  const onSubmit = async (data: RegisterInput) => {
    setErrorMsg(null);
    setIsLoading(true);
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
            const messages = detail.map((err: any) => err.msg || t('auth.invalidData')).join('\n');
            setErrorMsg(messages);
        } else if (error.response?.status === 400) {
            setErrorMsg(t('auth.invalidData'));
        } else {
            setErrorMsg(t('auth.networkError'));
        }
      } else {
          setErrorMsg(t('auth.unexpectedError'));
      }
    } finally {
      setIsLoading(false);
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
      <View style={{ position: 'absolute', top: insets.top + 10, right: 20, zIndex: 10 }}>
        <TouchableOpacity 
          onPress={() => setSettingsVisible(true)} 
          className="p-2 bg-card rounded-full border border-border shadow-sm"
        >
          <IconSymbol name="gear" size={24} color={Colors[colorScheme ?? 'light'].tint} />
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'} 
        style={{ flex: 1 }}
      >
        <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
          <ScrollView contentContainerStyle={{ flexGrow: 1, justifyContent: 'center' }} className="px-6" keyboardShouldPersistTaps="handled">
            <View className="mb-8">
              <Text className="text-3xl font-bold text-foreground">{t('auth.createAccount')}</Text>
              <Text className="text-muted-foreground mt-2">{t('auth.signUpSubtitle')}</Text>
            </View>

            {errorMsg && (
                <View className="mb-4 p-3 bg-destructive/15 border border-destructive rounded-lg">
                    <Text className="text-destructive text-center">{errorMsg}</Text>
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
                colors={[Colors[colorScheme ?? 'light'].primary, Colors[colorScheme ?? 'light'].primaryDark]}
                className="rounded-xl p-4 items-center"
              >
               {isLoading ? (
                 <ActivityIndicator color={Colors.light.tint} />
               ) : (
                 <Text className="text-white font-semibold text-lg">{t('auth.signUp')}</Text>
               )}
              </LinearGradient>
            </TouchableOpacity>

            <View className="flex-row justify-center mt-4 mb-8">
              <Text className="text-muted-foreground">{t('auth.alreadyHaveAccount')} </Text>
              <TouchableOpacity onPress={() => router.push('/(auth)/login')}>
                <Text className="text-primary font-semibold">{t('auth.signIn')}</Text>
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
