import React from 'react';
import { View, Text, TouchableOpacity, ScrollView, Pressable, Keyboard } from 'react-native';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { VoiceMealSummary } from './VoiceMealSummary';
import { ProcessedMeal, ProcessedFoodItem } from '@/services/ai.service'; 

const FoodItemReview = React.memo(({ 
    item, 
    onPress, 
    onRemove, 
    t 
}: { 
    item: ProcessedFoodItem; 
    onPress: () => void; 
    onRemove: () => void; 
    t: (key: string) => string;
}) => {
    return (
        <Pressable 
            onPress={onPress}
            className="mb-3 p-4 bg-card rounded-2xl border border-border shadow-sm"
        >
            <View className="flex-row justify-between items-start mb-2">
                <View className="flex-1">
                    <View className="flex-row items-center gap-1.5 mb-0.5">
                        <Text className="text-base font-black text-foreground leading-tight">{item.name}</Text>
                        <IconSymbol name="pencil" size={11} color="#6366f1" />
                    </View>
                    {item.brand && <Text className="text-xs text-muted-foreground font-medium">{item.brand}</Text>}
                </View>
                <TouchableOpacity 
                    onPress={onRemove}
                    className="p-2 -mr-2 -mt-2 opacity-50"
                >
                    <IconSymbol name="xmark" size={16} color="#9CA3AF" />
                </TouchableOpacity>
            </View>

            <View className="flex-row items-center justify-between">
                <View className="flex-row items-baseline gap-1">
                    <Text className="text-xl font-black text-foreground">
                        {item.unit_matched === 'g' || item.unit_matched === 'gram' ? item.quantity_grams : item.quantity_unit_value}
                    </Text>
                    <Text className="text-xs font-bold text-muted-foreground uppercase">
                        {item.unit_matched === 'g' || item.unit_matched === 'gram' ? 'g' : item.unit_matched}
                    </Text>
                </View>

                <View className="items-end">
                    <Text className="text-base font-bold text-foreground">
                        {Math.round(item.kcal)} <Text className="text-[10px] text-muted-foreground font-normal">kcal</Text>
                    </Text>
                </View>
            </View>
        </Pressable>
    );
});

FoodItemReview.displayName = 'FoodItemReview';

interface VoiceMealReviewProps {
  localMeal: ProcessedMeal;
  onCancel: () => void;
  textColor: string;
  cycleMealType: () => void;
  getMealTypeLabel: (type: string) => string;
  onEditItem: (index: number) => void;
  handleRemoveItem: (index: number) => void;
  setIsSearching: (val: boolean) => void;
  totals: { kcal: number; protein: number; fat: number; carbs: number };
  onConfirm: () => void;
  isLoading?: boolean;
  t: (key: string) => string;
}

export const VoiceMealReview = ({
    localMeal,
    onCancel,
    textColor,
    cycleMealType,
    getMealTypeLabel,
    onEditItem,
    handleRemoveItem,
    setIsSearching,
    totals,
    onConfirm,
    isLoading,
    t
}: VoiceMealReviewProps) => {
    if (!localMeal) return null;

    return (
     <View className="flex-1 bg-background">
         <View className="px-4 pt-4 pb-4 bg-background/50 border-b border-border/30">
            <View className="flex-row justify-between items-center mb-3">
                <TouchableOpacity onPress={onCancel} className="p-2 -ml-2 rounded-full">
                    <IconSymbol name="xmark" size={22} color={textColor} />
                </TouchableOpacity>
                <View className="items-end">
                     <Text className="text-xs font-semibold text-muted-foreground mb-1">Potwierdź produkty</Text>
                     <TouchableOpacity 
                        className="flex-row items-center gap-1.5 bg-card px-3 py-1.5 rounded-full border border-border"
                        onPress={cycleMealType}
                     >
                        <Text className="text-base font-black text-foreground capitalize">
                            {getMealTypeLabel(localMeal.meal_type)}
                        </Text>
                        <IconSymbol name="chevron.down" size={12} color="#6366f1" />
                     </TouchableOpacity>
                </View>
            </View>

            {localMeal.raw_transcription && (
                <View className="bg-primary/10 p-2.5 rounded-lg border-l-4 border-primary">
                    <Text className="text-indigo-900 dark:text-indigo-200 text-xs italic leading-snug">
                        "{localMeal.raw_transcription}"
                    </Text>
                </View>
            )}
        </View>

        <View className="flex-1">
            <ScrollView 
                className="flex-1" 
                contentContainerStyle={{ flexGrow: 1, paddingBottom: 100, paddingTop: 16, paddingHorizontal: 16 }}
                keyboardShouldPersistTaps="handled" 
                showsVerticalScrollIndicator={false}
            >
                {(localMeal.items || []).map((item: ProcessedFoodItem, index: number) => (
                    <FoodItemReview 
                        key={index}
                        item={item}
                        onPress={() => onEditItem(index)}
                        onRemove={() => handleRemoveItem(index)}
                        t={t}
                    />
                ))}

                <TouchableOpacity 
                    onPress={() => setIsSearching(true)}
                    className="mt-2 mb-8 flex-row items-center justify-center p-4 border-2 border-dashed border-border rounded-2xl"
                >
                    <IconSymbol name="plus" size={20} color="#9CA3AF" />
                    <Text className="text-muted-foreground font-semibold ml-2">{t('addFood.searchToConfirm') || 'Dodaj kolejny produkt'}</Text>
                </TouchableOpacity>
            </ScrollView>
            
            <VoiceMealSummary totals={totals} onConfirm={onConfirm} isLoading={isLoading} t={t} />
        </View>
    </View>
   );
};
