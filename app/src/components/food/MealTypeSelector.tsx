import React from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { useLanguage } from '@/hooks/useLanguage';
import { MealType } from '@/types/food';

interface MealTypeSelectorProps {
  selectedMeal: MealType;
  onSelect: (meal: MealType) => void;
}

export function MealTypeSelector({ selectedMeal, onSelect }: MealTypeSelectorProps) {
  const { t } = useLanguage();

  const mealTypeOptions = [
    { label: t('meals.breakfast'), value: MealType.BREAKFAST },
    { label: t('meals.lunch'), value: MealType.LUNCH },
    { label: t('meals.snack'), value: MealType.SNACK },
    { label: t('meals.dinner'), value: MealType.DINNER },
  ];

  return (
    <View className="bg-card rounded-2xl p-4 mb-4 shadow-sm border border-border">
      <Text className="text-sm font-medium text-muted-foreground mb-3">{t('manualEntry.mealLabel')}</Text>
      <View className="flex-row flex-wrap gap-2">
        {mealTypeOptions.map((option) => (
          <TouchableOpacity
            key={option.label}
            testID={`meal-type-${option.value}`}
            className={`px-4 py-2 rounded-full ${selectedMeal === option.value ? 'bg-primary' : 'bg-muted/50'}`}
            onPress={() => onSelect(option.value)}
          >
            <Text className={`text-sm font-medium ${selectedMeal === option.value ? 'text-primary-foreground' : 'text-muted-foreground'}`}>
              {option.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}
