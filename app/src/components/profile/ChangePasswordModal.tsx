import React, { useState, useMemo } from 'react';
import { View, Text, TouchableOpacity, Modal, ActivityIndicator, Alert, KeyboardAvoidingView, Platform, TouchableWithoutFeedback, Keyboard, ScrollView } from 'react-native';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { createChangePasswordSchema, ChangePasswordInput } from '@/utils/validators';
import { ControlledInput } from '@/components/ui/ControlledInput';
import { useLanguage } from '@/hooks/useLanguage';
import { useColorScheme } from '@/hooks/useColorScheme';
import { Colors } from '@/constants/theme';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { authService } from '@/services/auth.service';
import { isAxiosError } from 'axios';

interface ChangePasswordModalProps {
  visible: boolean;
  onClose: () => void;
}

export function ChangePasswordModal({ visible, onClose }: ChangePasswordModalProps) {
  const { t } = useLanguage();
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const changePasswordSchema = useMemo(() => createChangePasswordSchema(t), [t]);

  const { control, handleSubmit, formState: { errors }, reset } = useForm<ChangePasswordInput>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: {
      oldPassword: '',
      newPassword: '',
      confirmPassword: '',
    },
  });

  const onSubmit = async (data: ChangePasswordInput) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      await authService.changePassword(data);
      Alert.alert(t('changePassword.successTitle'), t('changePassword.successMessage'), [
        { text: "OK", onPress: handleClose }
      ]);
    } catch (error: any) {
      if (error.response?.data?.detail === 'Invalid old password') {
        setErrorMsg(t('changePassword.errorInvalidOldPassword'));
      } else if (error.response?.status === 400) {
        setErrorMsg(t('changePassword.errorMatch'));
      } else {
        setErrorMsg(t('changePassword.errorGeneric'));
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    reset();
    setErrorMsg(null);
    onClose();
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={handleClose}
    >
      <View className="flex-1 bg-background">
        <View className="flex-row justify-center items-center p-4 border-b border-border bg-background relative">
          <Text className="text-xl font-bold text-foreground">{t('changePassword.title')}</Text>
          <TouchableOpacity 
            onPress={handleClose} 
            className="p-2 bg-muted/50 rounded-full absolute right-4"
          >
            <IconSymbol name="xmark" size={20} color={Colors[useColorScheme().colorScheme ?? 'light'].text} />
          </TouchableOpacity>
        </View>

        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={{ flex: 1 }}
        >
          <ScrollView className="flex-1 p-6">
            <View className="mb-6">
              <Text className="text-muted-foreground">
                {t('changePassword.description')}
              </Text>
            </View>

            {errorMsg && (
              <View className="mb-4 p-3 bg-destructive/15 border border-destructive rounded-lg">
                <Text className="text-destructive text-center">{errorMsg}</Text>
              </View>
            )}

            <ControlledInput
              control={control}
              name="oldPassword"
              label={t('changePassword.currentPassword')}
              placeholder={t('changePassword.currentPasswordPlaceholder')}
              secureTextEntry
              error={errors.oldPassword?.message}
            />

            <ControlledInput
              control={control}
              name="newPassword"
              label={t('changePassword.newPassword')}
              placeholder={t('changePassword.newPasswordPlaceholder')}
              secureTextEntry
              error={errors.newPassword?.message}
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
              className="mt-8 bg-primary p-4 rounded-xl items-center shadow-sm"
              onPress={handleSubmit(onSubmit)}
              disabled={isLoading}
            >
              {isLoading ? (
                <ActivityIndicator color="white" />
              ) : (
                <Text className="text-white font-bold text-lg">{t('changePassword.updatePassword')}</Text>
              )}
            </TouchableOpacity>

          </ScrollView>
        </KeyboardAvoidingView>
      </View>
    </Modal>
  );
}
