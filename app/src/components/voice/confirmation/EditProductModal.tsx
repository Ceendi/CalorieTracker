import React, { useState, useEffect, useMemo } from 'react';
import {
  View,
  Text,
  Modal,
  TextInput,
  TouchableOpacity,
  Pressable,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { IconSymbol } from '@/components/ui/IconSymbol';
import * as Haptics from 'expo-haptics';
import { ProcessedFoodItem } from '@/services/ai.service';
import { calculateItemMacros } from '@/utils/calculations';

interface EditProductModalProps {
  visible: boolean;
  item: ProcessedFoodItem | null;
  onClose: () => void;
  onSave: (quantity: number, unit: any) => void;
  t: (key: string) => string;
}

export function EditProductModal({
  visible,
  item,
  onClose,
  onSave,
  t,
}: EditProductModalProps) {
  const [quantity, setQuantity] = useState('');
  const [selectedUnit, setSelectedUnit] = useState<any>(null);

  useEffect(() => {
    if (item && visible) {
      setQuantity(item.quantity_unit_value.toString());
      
      const currentUnitLabel = item.unit_matched;
      if (!currentUnitLabel || ['g', 'gram', 'gramy'].includes(currentUnitLabel.toLowerCase())) {
        setSelectedUnit(null);
      } else {
        const found = item.units?.find(u => 
            u.label === currentUnitLabel || 
            u.label.toLowerCase() === currentUnitLabel.toLowerCase()
        );
        setSelectedUnit(found || null);
      }
    }
  }, [item, visible]);

  const calculatedValues = useMemo(() => {
    if (!item) return { kcal: 0, protein: 0, fat: 0, carbs: 0 };
    const val = parseFloat(quantity.replace(',', '.'));
    if (isNaN(val) || val < 0) return { kcal: 0, protein: 0, fat: 0, carbs: 0 };

    const gramsPerUnit = selectedUnit === null ? 1 : selectedUnit.grams;
    
    return calculateItemMacros(
        { kcal: item.kcal, protein: item.protein, fat: item.fat, carbs: item.carbs },
        item.quantity_grams || 100,
        val,
        gramsPerUnit
    );
  }, [item, quantity, selectedUnit]);

  const handleUnitChange = (newUnit: any) => {
    const currentVal = parseFloat(quantity.replace(',', '.'));
    if (isNaN(currentVal) || currentVal <= 0) {
      setSelectedUnit(newUnit);
      return;
    }

    const gramsPerOldUnit = selectedUnit === null ? 1 : selectedUnit.grams;
    const gramsPerNewUnit = newUnit === null ? 1 : newUnit.grams;
    
    const totalGrams = currentVal * gramsPerOldUnit;
    const newVal = totalGrams / gramsPerNewUnit;
    
    const formattedVal = Math.round(newVal * 100) / 100;
    setQuantity(formattedVal.toString());
    setSelectedUnit(newUnit);
    Haptics.selectionAsync();
  };

  const handleSave = () => {
    const val = parseFloat(quantity.replace(',', '.'));
    if (!isNaN(val) && val > 0) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      onSave(val, selectedUnit);
      onClose();
    }
  };

  if (!item) return null;

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <Pressable 
        className="flex-1 bg-black/50 justify-end"
        onPress={onClose}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          className="w-full"
        >
          <Pressable 
            className="bg-card rounded-t-[32px] overflow-hidden"
            onPress={(e) => e.stopPropagation()}
          >
            <ScrollView 
                keyboardShouldPersistTaps="always"
                contentContainerStyle={{ padding: 24, paddingBottom: 48 }}
                bounces={false}
            >
                <View className="mb-6">
                  <Text className="text-2xl font-black text-foreground mb-1">
                    {item.name}
                  </Text>
                  <View className="flex-row items-center gap-2">
                    {item.brand && (
                      <Text className="text-sm font-bold text-muted-foreground">
                        {item.brand}
                      </Text>
                    )}
                    <Text className="text-sm font-bold text-indigo-500">
                      {Math.round((item.kcal / item.quantity_grams) * 100)} kcal / 100g
                    </Text>
                  </View>
                </View>

                <View className="flex-row gap-4 mb-8 bg-secondary/50 dark:bg-black/20 p-4 rounded-2xl">
                    <View className="flex-1">
                        <Text className="text-[10px] font-bold text-sky-500 uppercase mb-0.5">{t('foodDetails.protein')}</Text>
                        <Text className="text-sm font-black text-foreground">
                            {calculatedValues.protein.toFixed(1)}g
                        </Text>
                    </View>
                    <View className="flex-1">
                        <Text className="text-[10px] font-bold text-amber-500 uppercase mb-0.5">{t('foodDetails.fat')}</Text>
                        <Text className="text-sm font-black text-foreground">
                            {calculatedValues.fat.toFixed(1)}g
                        </Text>
                    </View>
                    <View className="flex-1">
                        <Text className="text-[10px] font-bold text-orange-500 uppercase mb-0.5">{t('foodDetails.carbs')}</Text>
                        <Text className="text-sm font-black text-foreground">
                            {calculatedValues.carbs.toFixed(1)}g
                        </Text>
                    </View>
                </View>

                <View className="mb-6">
                  <Text className="text-sm font-bold text-muted-foreground mb-2 ml-1">
                    {t('foodDetails.quantity')}
                  </Text>
                  <View className="flex-row items-center gap-4">
                    <View className="flex-1 h-16 bg-secondary/50 dark:bg-black/20 rounded-2xl border border-border px-4 justify-center">
                      <TextInput
                        className="text-3xl font-black text-foreground p-0"
                        value={quantity}
                        onChangeText={setQuantity}
                        keyboardType="decimal-pad"
                        autoFocus
                        selectTextOnFocus
                        placeholder="0"
                        placeholderTextColor="#9CA3AF"
                      />
                    </View>
                  </View>
                </View>

                <View className="mb-8">
                  <Text className="text-sm font-bold text-muted-foreground mb-3 ml-1">
                    Jednostka
                  </Text>
                  <ScrollView 
                      horizontal 
                      showsHorizontalScrollIndicator={false}
                      className="flex-row gap-2"
                      keyboardShouldPersistTaps="always"
                  >
                    <TouchableOpacity
                      onPress={() => handleUnitChange(null)}
                      className={`mr-2 px-5 py-3 rounded-xl border ${
                        selectedUnit === null 
                          ? 'bg-indigo-600 border-indigo-600' 
                          : 'bg-muted/50 border-transparent'
                      }`}
                    >
                      <Text className={`font-bold ${selectedUnit === null ? 'text-white' : 'text-foreground'}`}>
                        Gramy (g)
                      </Text>
                    </TouchableOpacity>

                    {item.units?.map((unit, idx) => (
                      <TouchableOpacity
                        key={idx}
                        onPress={() => handleUnitChange(unit)}
                        className={`mr-2 px-5 py-3 rounded-xl border ${
                          selectedUnit?.label === unit.label 
                            ? 'bg-indigo-600 border-indigo-600' 
                            : 'bg-secondary/50 dark:bg-black/20 border-transparent'
                        }`}
                      >
                        <Text className={`font-bold ${selectedUnit?.label === unit.label ? 'text-white' : 'text-foreground'}`}>
                          {unit.label} ({unit.grams}g)
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </ScrollView>
                </View>

                <View className="flex-row items-center justify-between gap-4 mt-2">
                     <View>
                        <Text className="text-xs font-bold text-muted-foreground uppercase mb-0.5">Razem</Text>
                        <View className="flex-row items-baseline gap-1">
                            <Text className="text-3xl font-black text-indigo-600">{calculatedValues.kcal}</Text>
                            <Text className="text-sm font-bold text-indigo-400">kcal</Text>
                        </View>
                     </View>

                     <View className="flex-row gap-3">
                        <TouchableOpacity
                            onPress={onClose}
                            className="px-6 py-4 rounded-2xl bg-secondary"
                        >
                            <Text className="font-bold text-foreground">Anuluj</Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                            onPress={handleSave}
                            className="px-8 py-4 rounded-2xl bg-indigo-600 shadow-lg shadow-indigo-300 dark:shadow-none"
                        >
                            <Text className="font-bold text-white">Zapisz</Text>
                        </TouchableOpacity>
                     </View>
                </View>
            </ScrollView>
          </Pressable>
        </KeyboardAvoidingView>
      </Pressable>
    </Modal>
  );
}
