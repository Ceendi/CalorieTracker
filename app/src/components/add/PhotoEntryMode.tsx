import React, { useEffect } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator } from 'react-native';
import { useLanguage } from '@/hooks/useLanguage';
import { usePhotoInput } from '@/hooks/usePhotoInput';
import { ProcessedMeal } from '@/types/ai';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/useColorScheme';

interface PhotoEntryModeProps {
  onMealProcessed: (meal: ProcessedMeal) => void;
  onError: (error: string) => void;
}

export function PhotoEntryMode({ onMealProcessed, onError }: PhotoEntryModeProps) {
  const { t } = useLanguage();
  const { colorScheme } = useColorScheme();
  const theme = colorScheme ?? 'light';
  
  const {
    state,
    processedMeal,
    error,
    pickImage,
    takePhoto,
    requestPermission,
    reset
  } = usePhotoInput();

  useEffect(() => {
    requestPermission();
  }, [requestPermission]);

  useEffect(() => {
    if (state === 'success' && processedMeal) {
      onMealProcessed(processedMeal);
      // Optional: reset after short delay or let parent handle unmount
      setTimeout(reset, 1000);
    }
  }, [state, processedMeal, onMealProcessed, reset]);

  useEffect(() => {
    if (state === 'error' && error) {
      onError(error);
      reset();
    }
  }, [state, error, onError, reset]);

  const isLoading = state === 'processing' || state === 'picking';
  const iconColor = Colors[theme].text;
  const activeColor = Colors[theme].tint;

  return (
    <View className="flex-1 items-center justify-center px-6 -mt-10">
      <View className="items-center mb-10">
        <Text className="text-2xl font-bold text-foreground mb-3 text-center">
          {t('addFood.placeholders.photoTitle')}
        </Text>
        <Text className="text-base text-muted-foreground text-center leading-6 px-2">
            {t('addFood.photo.description')}
        </Text>
      </View>

      {isLoading ? (
        <View className="items-center justify-center p-8">
            <ActivityIndicator size="large" color={activeColor} />
            <Text className="mt-4 text-muted-foreground font-medium">
                {state === 'processing' ? t('addFood.voiceButton.processing') : t('addFood.photo.preparing')}
            </Text>
        </View>
      ) : (
        <View className="flex-row gap-6">
            <TouchableOpacity 
                onPress={takePhoto}
                className="items-center justify-center bg-card p-6 rounded-3xl shadow-sm border border-border w-36 h-36"
                style={{ elevation: 2 }}
            >
                <View className="bg-muted p-4 rounded-full mb-3">
                     <IconSymbol name="camera.fill" size={32} color={activeColor} />
                </View>
                <Text className="font-semibold text-foreground">{t('addFood.photo.camera')}</Text>
            </TouchableOpacity>

            <TouchableOpacity 
                onPress={pickImage}
                className="items-center justify-center bg-card p-6 rounded-3xl shadow-sm border border-border w-36 h-36"
                 style={{ elevation: 2 }}
            >
                <View className="bg-muted p-4 rounded-full mb-3">
                     <IconSymbol name="photo.fill" size={32} color={activeColor} />
                </View>
                <Text className="font-semibold text-foreground">{t('addFood.photo.gallery')}</Text>
            </TouchableOpacity>
        </View>
      )}

      <View className="mt-12 px-4">
        <Text className="text-sm text-muted-foreground text-center">
          {t('addFood.photo.tip')}
        </Text>
      </View>
    </View>
  );
}
