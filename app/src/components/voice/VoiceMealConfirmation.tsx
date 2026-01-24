import React, { useMemo, useState, useEffect } from 'react';
import {
  View,
  Keyboard,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useThemeColor } from '@/hooks/use-theme-color';
import { useLanguage } from '@/hooks/useLanguage';
import { useFoodSearch } from '@/hooks/useFood';
import type { ProcessedMeal, ProcessedFoodItem } from '@/services/ai.service';
import { FoodProduct } from '@/types/food';

import { VoiceMealReview } from './confirmation/VoiceMealReview';
import { VoiceMealSearch } from './confirmation/VoiceMealSearch';

interface VoiceMealConfirmationProps {
  visible: boolean;
  meal: ProcessedMeal | null;
  onConfirm: (meal: ProcessedMeal) => void;
  onEdit: () => void;
  onCancel: () => void;
}

export function VoiceMealConfirmation({
  visible,
  meal,
  onConfirm,
  onEdit,
  onCancel,
}: VoiceMealConfirmationProps) {
  const { t } = useLanguage();
  const textColor = useThemeColor({}, 'text');
  const insets = useSafeAreaInsets();
  
  const [localMeal, setLocalMeal] = useState<ProcessedMeal | null>(meal);
  const [editingItemIndex, setEditingItemIndex] = useState<number | null>(null);
  const [tempQuantity, setTempQuantity] = useState('');
  
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const { data: searchResults, isLoading: isSearchLoading } = useFoodSearch(searchQuery);

  useEffect(() => {
    if (meal) setLocalMeal(JSON.parse(JSON.stringify(meal)));
  }, [meal]);

  const totals = useMemo(() => {
    if (!localMeal?.items) return { kcal: 0, protein: 0, fat: 0, carbs: 0 };
    return localMeal.items.reduce(
      (acc, item) => ({
        kcal: acc.kcal + item.kcal,
        protein: acc.protein + item.protein,
        fat: acc.fat + item.fat,
        carbs: acc.carbs + item.carbs,
      }),
      { kcal: 0, protein: 0, fat: 0, carbs: 0 }
    );
  }, [localMeal]);

  const handleUpdateQuantity = (index: number, newValue: number, newUnit?: any) => {
    if (!localMeal) return;
    const updatedItems = [...localMeal.items];
    const item = { ...updatedItems[index] };

    const currentGrams = item.quantity_grams || 100;
    const kcalPerGram = item.kcal / currentGrams;
    const proteinPerGram = item.protein / currentGrams;
    const fatPerGram = item.fat / currentGrams;
    const carbsPerGram = item.carbs / currentGrams;

    if (newUnit !== undefined) {
       const newGramsPerUnit = newUnit === null ? 1 : newUnit.grams;
       item.unit_matched = newUnit === null ? 'g' : newUnit.label;
       if (newUnit === null) {
          item.quantity_unit_value = item.quantity_grams; 
       } else {
          item.quantity_unit_value = (newValue > 0) ? newValue : 1;
       }
       item.quantity_grams = item.quantity_unit_value * newGramsPerUnit;
    } else {
       if (item.quantity_unit_value <= 0) item.quantity_unit_value = 1; 
       const gramsPerUnit = item.quantity_grams / item.quantity_unit_value;
       item.quantity_unit_value = newValue;
       item.quantity_grams = Math.round(newValue * gramsPerUnit * 10) / 10;
    }

    item.kcal = item.quantity_grams * kcalPerGram;
    item.protein = item.quantity_grams * proteinPerGram;
    item.fat = item.quantity_grams * fatPerGram;
    item.carbs = item.quantity_grams * carbsPerGram;
    
    updatedItems[index] = item;
    setLocalMeal({ ...localMeal, items: updatedItems });
    if (newUnit !== undefined) setEditingItemIndex(null);
  };

  const handleRemoveItem = (index: number) => {
    if (!localMeal) return;
    const updatedItems = localMeal.items.filter((_, i) => i !== index);
    setLocalMeal({ ...localMeal, items: updatedItems });
  };
  
  const cycleMealType = () => {
    if (!localMeal) return;
    const types = ['breakfast', 'second_breakfast', 'lunch', 'tea', 'dinner', 'snack'];
    const currentIdx = types.indexOf(localMeal.meal_type);
    const nextIdx = currentIdx === -1 ? 0 : (currentIdx + 1) % types.length;
    setLocalMeal({ ...localMeal, meal_type: types[nextIdx] });
  };

  const getMealTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      'breakfast': t('meals.breakfast'),
      'second_breakfast': t('meals.second_breakfast'),
      'lunch': t('meals.lunch'),
      'tea': t('meals.tea'),
      'dinner': t('meals.dinner'),
      'snack': t('meals.snack'),
      'śniadanie': t('meals.breakfast'),
      'drugie_śniadanie': t('meals.second_breakfast'),
      'obiad': t('meals.lunch'),
      'podwieczorek': t('meals.tea'),
      'kolacja': t('meals.dinner'),
      'przekąska': t('meals.snack'),
    };
    return labels[type] || type;
  };
  
  const handleConfirm = () => {
    if (localMeal) onConfirm(localMeal);
  };

  const handleAddManualItem = (product: FoodProduct) => {
    if (!localMeal) return;
    const newItem: ProcessedFoodItem = {
      product_id: product.id ? parseInt(product.id) : null,
      name: product.name,
      quantity_grams: 100,
      quantity_unit_value: 1,
      unit_matched: 'g',
      kcal: product.nutrition.calories_per_100g,
      protein: product.nutrition.protein_per_100g,
      fat: product.nutrition.fat_per_100g,
      carbs: product.nutrition.carbs_per_100g,
      confidence: 1.0,
      status: 'matched',
      brand: product.brand,
      units: product.units,
    };

    setLocalMeal({
      ...localMeal,
      items: [...localMeal.items, newItem]
    });
    setIsSearching(false);
    setSearchQuery('');
    Keyboard.dismiss();
  };

  if (!visible) return null;
  if (!localMeal) return null;

  return (
    <View 
        className="absolute top-0 bottom-0 left-0 right-0 z-50 bg-white dark:bg-slate-950"
        style={{ paddingTop: insets.top }}
    >
        <KeyboardAvoidingView 
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            className="flex-1"
            keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 0}
        >
            {isSearching ? (
                <VoiceMealSearch 
                    searchQuery={searchQuery}
                    setSearchQuery={setSearchQuery}
                    setIsSearching={setIsSearching}
                    isSearchLoading={isSearchLoading}
                    searchResults={searchResults}
                    handleAddManualItem={handleAddManualItem}
                    t={t}
                />
            ) : (
                <VoiceMealReview 
                    localMeal={localMeal}
                    onCancel={onCancel}
                    textColor={textColor}
                    cycleMealType={cycleMealType}
                    getMealTypeLabel={getMealTypeLabel}
                    editingItemIndex={editingItemIndex}
                    setEditingItemIndex={setEditingItemIndex}
                    tempQuantity={tempQuantity}
                    setTempQuantity={setTempQuantity}
                    handleUpdateQuantity={handleUpdateQuantity}
                    handleRemoveItem={handleRemoveItem}
                    setIsSearching={setIsSearching}
                    totals={totals}
                    onConfirm={() => handleConfirm()}
                    t={t}
                />
            )}
        </KeyboardAvoidingView>
    </View>
  );
}
