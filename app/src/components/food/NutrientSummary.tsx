import React from 'react';
import { View, Text } from 'react-native';
import { useLanguage } from '@/hooks/useLanguage';

interface NutrientSummaryProps {
  calories: number;
  protein: number;
  fat: number;
  carbs: number;
  gl?: number;
}

export function NutrientSummary({ calories, protein, fat, carbs, gl }: NutrientSummaryProps) {
  const { t } = useLanguage();

  return (
    <View className="flex-row bg-card rounded-2xl p-5 mb-8 justify-between items-center shadow-sm border border-border">
      <View className="items-center flex-1">
        <Text className="text-xl font-bold text-primary mb-1">{Math.round(calories)}</Text>
        <Text className="text-xs text-muted-foreground">{t('manualEntry.calories')}</Text>
      </View>
      <View className="w-px h-10 bg-border" />
      <View className="items-center flex-1">
        <Text className="text-lg font-bold text-foreground mb-1">{protein.toFixed(1)}g</Text>
        <Text className="text-xs text-muted-foreground">{t('manualEntry.protein')}</Text>
      </View>
      <View className="w-px h-10 bg-border" />
      <View className="items-center flex-1">
        <Text className="text-lg font-bold text-foreground mb-1">{fat.toFixed(1)}g</Text>
        <Text className="text-xs text-muted-foreground">{t('manualEntry.fat')}</Text>
      </View>
      <View className="w-px h-10 bg-border" />
      <View className="items-center flex-1">
        <Text className="text-lg font-bold text-foreground mb-1">{carbs.toFixed(1)}g</Text>
        <Text className="text-xs text-muted-foreground">{t('manualEntry.carbs')}</Text>
      </View>
      {gl !== undefined && (
          <>
            <View className="w-px h-10 bg-border" />
            <View className="items-center flex-1">
              <Text className="text-lg font-black text-indigo-500 mb-1">{gl}</Text>
              <Text className="text-xs font-bold text-muted-foreground uppercase">{t('foodDetails.gl.title')}</Text>
            </View>
          </>
      )}
    </View>
  );
}
