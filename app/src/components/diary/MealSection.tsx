import React from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { MealType, MealEntry } from '@/types/food';
import { FoodEntryItem } from './FoodEntryItem';
import { useLanguage } from '@/hooks/useLanguage';
import { IconSymbol } from '@/components/ui/IconSymbol';

interface MealSectionProps {
  type: MealType;
  entries: MealEntry[];
  onAdd: (type: MealType) => void;
  onDeleteEntry: (id: string) => void;
  onEditEntry: (entry: MealEntry) => void;
}

export function MealSection({ type, entries, onAdd, onDeleteEntry, onEditEntry }: MealSectionProps) {
  const { t } = useLanguage();
  
  const totalCalories = entries.reduce((sum, e) => sum + e.calories, 0);

  return (
    <View className="mb-6">
      <View className="flex-row justify-between items-center mb-3">
        <Text className="text-lg font-bold text-gray-900 dark:text-white capitalize">
            {t(`meals.${type}`)}
        </Text>
        <Text className="text-sm font-medium text-gray-500 dark:text-gray-400">
            {Math.round(totalCalories)} kcal
        </Text>
      </View>

      {entries.map(entry => (
          <FoodEntryItem 
            key={entry.id} 
            entry={entry} 
            onDelete={onDeleteEntry}
            onPress={onEditEntry}
          />
      ))}

      <TouchableOpacity 
        onPress={() => onAdd(type)}
        className="flex-row items-center py-2"
      >
        <IconSymbol name="plus.circle.fill" size={20} color="#4F46E5" />
        <Text className="text-indigo-600 font-medium ml-2">{t('dashboard.quickAdd')}</Text>
      </TouchableOpacity>
    </View>
  );
}
