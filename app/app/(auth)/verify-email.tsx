import React from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, Platform, KeyboardAvoidingView, TouchableWithoutFeedback, Keyboard } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLocalSearchParams } from 'expo-router';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { createVerificationSchema, VerificationInput } from '@/utils/validators';
import { authService } from '@/services/auth.service';
import { ControlledInput } from '@/components/ui/ControlledInput';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '@/hooks/useAuth';
import { useLanguage } from '@/hooks/useLanguage';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { useColorScheme } from '@/hooks/useColorScheme';
import { SettingsModal } from '@/components/profile/SettingsModal';
import { Colors } from '@/constants/theme';

export default function VerifyEmailScreen() {

  const { email } = useLocalSearchParams<{ email: string }>();
  const { checkSession, signOut, user } = useAuth();
  const { t } = useLanguage();
  
  const targetEmail = email || user?.email;
  
  const [isLoading, setIsLoading] = React.useState(false);
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null);
  const insets = useSafeAreaInsets();
  const { colorScheme } = useColorScheme();
  const [settingsVisible, setSettingsVisible] = React.useState(false);
  
  const verificationSchema = React.useMemo(() => createVerificationSchema(t), [t]);

  const { control, handleSubmit, formState: { errors } } = useForm<VerificationInput>({
    resolver: zodResolver(verificationSchema),
    defaultValues: {
       code: ''
    }
  });

  const onSubmit = async (data: VerificationInput) => {
      if (!targetEmail) {
          setErrorMsg(t('auth.emailMissing'));
          return;
      }
      setErrorMsg(null);
      
      try {
          setIsLoading(true);
          const tokenPayload = `${targetEmail}:${data.code}`;
          const token = btoa(tokenPayload);
          
          await authService.verify(token);
          await checkSession();
          setIsLoading(false);
      } catch (error: any) {
          setIsLoading(false);
          if (error.response?.status === 400) {
              setErrorMsg(t('auth.invalidCode'));
          } else {
              setErrorMsg(t('auth.verificationFailed'));
          }
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
          <View className="flex-1 px-6 justify-center" testID="verify-email-screen">
            <View className="mb-8">
              <Text className="text-3xl font-bold text-foreground">{t('auth.verifyEmail')}</Text>
              <Text className="text-muted-foreground mt-2">
                {t('auth.verifySubtitle')} {targetEmail || 'your email'}
              </Text>
            </View>

            {errorMsg && (
                <View className="mb-4 p-3 bg-destructive/15 border border-destructive rounded-lg">
                    <Text className="text-destructive text-center">{errorMsg}</Text>
                </View>
            )}

            <ControlledInput
              control={control}
              name="code"
              label={t('auth.verificationCode')}
              placeholder={t('auth.codePlaceholder')}
              keyboardType="number-pad"
              maxLength={6}
              error={errors.code?.message}
              style={{ letterSpacing: 8, textAlign: 'center', fontSize: 24 }}
              testID="verify-code"
            />

            <TouchableOpacity
              testID="verify-submit"
              className="mt-6 mb-4"
              onPress={handleSubmit(onSubmit)}
              disabled={isLoading}
            >
              <LinearGradient
                colors={[Colors[colorScheme ?? 'light'].primary, Colors[colorScheme ?? 'light'].primaryDark]}
                className="rounded-xl p-4 items-center"
              >
               {isLoading ? (
                 <ActivityIndicator size="large" color="white" />
               ) : (
                 <Text className="text-white font-semibold text-lg">{t('auth.verifyAccount')}</Text>
               )}
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity 
                onPress={() => {/* resend logic */}}
                className="items-center mt-4"
            >
                <Text className="text-primary font-medium">{t('auth.resendCode')}</Text>
            </TouchableOpacity>

            <TouchableOpacity 
                onPress={() => signOut()}
                className="items-center mt-8"
            >
                <Text className="text-muted-foreground">{t('auth.backToLogin')}</Text>
            </TouchableOpacity>
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
