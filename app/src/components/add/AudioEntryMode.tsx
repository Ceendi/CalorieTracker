import React from 'react';
import { View, Text } from 'react-native';
import { VoiceInputButton } from '@/components/voice/VoiceInputButton';
import { useLanguage } from '@/hooks/useLanguage';
import { ProcessedMeal } from '@/hooks/useVoiceInput';

interface AudioEntryModeProps {
  onMealProcessed: (meal: ProcessedMeal) => void;
  onError: (error: string) => void;
}

export function AudioEntryMode({ onMealProcessed, onError }: AudioEntryModeProps) {
  const { t } = useLanguage();

  return (
    <View className="flex-1 items-center justify-center px-8 -mt-10">
      <View className="items-center mb-8">
        <Text className="text-2xl font-bold text-gray-900 dark:text-white mb-3 text-center">
          {t('addFood.placeholders.voiceTitle')}
        </Text>
        <Text className="text-base text-gray-500 dark:text-gray-400 text-center leading-6 px-4">
          {t('addFood.placeholders.voiceDesc')}
        </Text>
      </View>

      <VoiceInputButton
        size="large"
        onMealProcessed={onMealProcessed}
        onError={onError}
      />

      <View className="mt-8 px-4">
        <Text className="text-sm text-gray-400 dark:text-gray-500 text-center">
          {t('addFood.voiceTip')}
        </Text>
      </View>
    </View>
  );
}
