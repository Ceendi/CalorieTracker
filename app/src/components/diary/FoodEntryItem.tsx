import React from 'react';
import { View, Text, TouchableOpacity, Alert } from 'react-native';
import Swipeable from 'react-native-gesture-handler/ReanimatedSwipeable';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { MealEntry } from '@/types/food';
import { useLanguage } from '@/hooks/useLanguage';
import { calculateGL } from '@/utils/glycemicLoad';

interface FoodEntryItemProps {
  entry: MealEntry;
  onDelete: (id: string) => void;
  onPress: (entry: MealEntry) => void;
}

export function FoodEntryItem({ entry, onDelete, onPress }: FoodEntryItemProps) {
    const { t } = useLanguage();

    const handleLongPress = () => {
        Alert.alert(
            t('dashboard.delete'),
            '',
            [
                { text: t('profile.cancel'), style: 'cancel' },
                { text: t('dashboard.delete'), style: 'destructive', onPress: () => onDelete(entry.id) },
            ]
        );
    };

    const renderRightActions = () => (
        <TouchableOpacity
            className="bg-destructive justify-center items-center w-20 h-full rounded-xl ml-2"
            onPress={() => onDelete(entry.id)}
        >
            <IconSymbol name="trash.fill" size={24} color="white" />
        </TouchableOpacity>
    );

    return (
        <View className="mb-3">
            <Swipeable renderRightActions={renderRightActions}>
                <TouchableOpacity
                    testID={`food-entry-${entry.id}`}
                    activeOpacity={0.7}
                    onPress={() => onPress(entry)}
                    onLongPress={handleLongPress}
                    className="flex-row justify-between items-center py-3 bg-card px-4 rounded-xl border border-border"
                >
                    <View className="flex-1">
                        <Text className="text-foreground font-medium text-base">
                            {entry.product?.name || t('foodDetails.unknownProduct')}
                        </Text>
                        <Text className="text-muted-foreground text-sm">
                            {Math.round(entry.amount_grams)}g • {Math.round(entry.calories)} kcal
                        </Text>
                    </View>
                    <View className="items-end gap-1">
                        <Text className="text-muted-foreground text-xs">
                            {t('foodDetails.macroP')}: {Math.round(entry.protein)} {t('foodDetails.macroF')}: {Math.round(entry.fat)} {t('foodDetails.macroC')}: {Math.round(entry.carbs)}
                        </Text>
                        {entry.gi_per_100g != null && (
                            (() => {
                                const gl = calculateGL(entry.gi_per_100g, entry.carbs);
                                const color =
                                    gl.label === 'niski' ? 'text-green-600 dark:text-green-400'
                                    : gl.label === 'średni' ? 'text-amber-600 dark:text-amber-400'
                                    : 'text-red-600 dark:text-red-400';
                                return (
                                    <Text className={`text-xs font-medium ${color}`}>
                                        ŁG {gl.value}
                                    </Text>
                                );
                            })()
                        )}
                    </View>
                </TouchableOpacity>
            </Swipeable>
        </View>
    );
}
