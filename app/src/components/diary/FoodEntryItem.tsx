import React from 'react';
import { View, Text, TouchableOpacity, Alert } from 'react-native';
import Swipeable from 'react-native-gesture-handler/ReanimatedSwipeable';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { MealEntry } from '@/types/food';
import { useLanguage } from '@/hooks/useLanguage';

interface FoodEntryItemProps {
  entry: MealEntry;
  onDelete: (id: string) => void;
  onPress: (entry: MealEntry) => void;
}

export function FoodEntryItem({ entry, onDelete, onPress }: FoodEntryItemProps) {
    const { t } = useLanguage();

    const renderRightActions = () => (
        <TouchableOpacity 
            className="bg-red-500 justify-center items-center w-20 h-full rounded-xl ml-2"
            onPress={() => onDelete(entry.id)}
        >
            <IconSymbol name="trash.fill" size={24} color="white" />
        </TouchableOpacity>
    );

    return (
        <View className="mb-3">
            <Swipeable renderRightActions={renderRightActions}>
                <TouchableOpacity 
                    activeOpacity={0.7}
                    onPress={() => onPress(entry)}
                    className="flex-row justify-between items-center py-3 bg-white dark:bg-slate-800 px-4 rounded-xl border border-gray-100 dark:border-slate-700"
                >
                    <View className="flex-1">
                        <Text className="text-gray-900 dark:text-white font-medium text-base">
                            {entry.product?.name || t('foodDetails.unknownProduct')}
                        </Text>
                        <Text className="text-gray-500 dark:text-gray-400 text-sm">
                            {entry.amount_grams}g • {Math.round(entry.calories)} kcal
                        </Text>
                    </View>
                    <View>
                        <Text className="text-gray-400 dark:text-gray-500 text-xs">
                            P: {Math.round(entry.protein)} F: {Math.round(entry.fat)} C: {Math.round(entry.carbs)}
                        </Text>
                    </View>
                </TouchableOpacity>
            </Swipeable>
        </View>
    );
}
