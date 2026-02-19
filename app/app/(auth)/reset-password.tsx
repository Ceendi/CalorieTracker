import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, Platform, KeyboardAvoidingView, TouchableWithoutFeedback, Keyboard, Alert } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { createResetPasswordSchema, ResetPasswordInput } from '@/utils/validators';
import { authService } from '@/services/auth.service';
import { ControlledInput } from '@/components/ui/ControlledInput';
import { LinearGradient } from 'expo-linear-gradient';
import { useLanguage } from '@/hooks/useLanguage';
import { useColorScheme } from '@/hooks/useColorScheme';
import { Colors } from '@/constants/theme';

export default function ResetPasswordScreen() {
  const router = useRouter();
  const { token } = useLocalSearchParams<{ token: string }>();
  const { t } = useLanguage();
  const insets = useSafeAreaInsets();
  const { colorScheme } = useColorScheme();
  
  const [isLoading, setIsLoading] = useState(false);

  const resetPasswordSchema = React.useMemo(() => createResetPasswordSchema(t), [t]);

  const { control, handleSubmit, formState: { errors } } = useForm<ResetPasswordInput>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      password: '',
      confirmPassword: '',
    },
  });

  const onSubmit = async (data: ResetPasswordInput) => {
    if (!token) {
        Alert.alert(t('profile.error'), 'Missing reset token');
        return;
    }

    try {
      setIsLoading(true);
      await authService.resetPassword(token, data.password);
      setIsLoading(false);
      Alert.alert(t('profile.success'), t('auth.resetSuccess'), [
          { text: 'OK', onPress: () => router.replace('/(auth)/login') }
      ]);
    } catch {
      setIsLoading(false);
      Alert.alert(t('profile.error'), t('auth.unexpectedError'));
    }
  };

  if (!token) {
    return (
        <View className="flex-1 bg-background justify-center items-center px-6">
            <Text className="text-muted-foreground text-center mb-6">Invalid or missing reset token.</Text>
            <TouchableOpacity onPress={() => router.replace('/(auth)/login')}>
                <Text className="text-primary font-bold">Back to Login</Text>
            </TouchableOpacity>
        </View>
    );
  }

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
          <View className="flex-1 px-6 justify-center">
            <View className="mb-8">
              <Text className="text-3xl font-bold text-foreground">{t('auth.resetPasswordTitle')}</Text>
              <Text className="text-muted-foreground mt-2">{t('changePassword.description')}</Text>
            </View>

            <ControlledInput
              control={control}
              name="password"
              label={t('changePassword.newPassword')}
              placeholder={t('changePassword.newPasswordPlaceholder')}
              secureTextEntry
              error={errors.password?.message}
            />

            <ControlledInput
              control={control}
              name="confirmPassword"
              label={t('changePassword.confirmNewPassword')}
              placeholder={t('changePassword.confirmNewPasswordPlaceholder')}
              secureTextEntry
              error={errors.confirmPassword?.message}
            />

            <TouchableOpacity 
              className="mt-6"
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
                 <Text className="text-white font-semibold text-lg">{t('changePassword.updatePassword')}</Text>
               )}
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </TouchableWithoutFeedback>
      </KeyboardAvoidingView>
    </View>
  );
}
