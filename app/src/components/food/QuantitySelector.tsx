import React, { useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, Alert } from 'react-native';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { useColorScheme } from '@/hooks/useColorScheme';
import { useLanguage } from '@/hooks/useLanguage';
import { UnitInfo } from '@/types/food';
import { Colors } from '@/constants/theme';

interface QuantitySelectorProps {
  quantity: string;
  onChangeQuantity: (quantity: string) => void;
  selectedUnit: UnitInfo | null;
  units: UnitInfo[] | undefined;
  onSelectUnit: (unit: UnitInfo | null) => void;
}

export function QuantitySelector({
  quantity,
  onChangeQuantity,
  selectedUnit,
  units,
  onSelectUnit
}: QuantitySelectorProps) {
  const { colorScheme } = useColorScheme();
  const { t } = useLanguage();
  const theme = colorScheme ?? 'light';

  const handleIncrement = () => {
    const current = parseFloat(quantity) || 0;
    const step = selectedUnit ? 1 : 10;
    onChangeQuantity(String(current + step));
  };

  const handleDecrement = () => {
    const current = parseFloat(quantity) || 0;
    const step = selectedUnit ? 1 : 10;
    const newValue = Math.max(1, current - step);
    onChangeQuantity(String(newValue));
  };

  const handleUnitChangeWithConversion = (newUnit: UnitInfo | null) => {
    const currentVal = parseFloat(quantity) || 0;
    if (currentVal <= 0) {
      onSelectUnit(newUnit);
      return;
    }

    const oldGramsPerUnit = selectedUnit ? selectedUnit.grams : 1;
    const newGramsPerUnit = newUnit ? newUnit.grams : 1;

    const totalGrams = currentVal * oldGramsPerUnit;
    const newVal = Math.round((totalGrams / newGramsPerUnit) * 100) / 100;

    onChangeQuantity(String(newVal));
    onSelectUnit(newUnit);
  };

  return (
    <View className="bg-card rounded-2xl p-4 mb-4 shadow-sm border border-border z-50">
      <Text className="text-sm font-medium text-muted-foreground mb-2">{t('manualEntry.quantity')}</Text>
      
      {/* Quantity Input Row */}
      <View className="flex-row items-stretch gap-2 h-14">
        <TouchableOpacity
          testID="quantity-minus"
          className="w-12 bg-muted/50 rounded-xl items-center justify-center"
          onPress={handleDecrement}
          accessibilityLabel={t('accessibility.decreaseQuantity')}
          accessibilityRole="button"
        >
          <IconSymbol name="minus" size={20} color={Colors[theme].mutedForeground} />
        </TouchableOpacity>
        
        <TextInput
          testID="quantity-input"
          className="flex-1 font-bold text-foreground px-4 bg-background border border-border rounded-xl text-center"
          style={{ fontSize: 20 }}
          value={quantity}
          onChangeText={(text) => {
             onChangeQuantity(text);
          }}
          keyboardType="numeric"
          placeholder="0"
          placeholderTextColor={Colors[theme].placeholder}
          accessibilityLabel={t('accessibility.quantityInput')}
        />
        
        <TouchableOpacity
          testID="quantity-plus"
          className="w-12 bg-muted/50 rounded-xl items-center justify-center"
          onPress={handleIncrement}
          accessibilityLabel={t('accessibility.increaseQuantity')}
          accessibilityRole="button"
        >
          <IconSymbol name="plus" size={20} color={Colors[theme].mutedForeground} />
        </TouchableOpacity>
      </View>

      {/* Unit Selector - Full Width Below */}
      <View className="mt-3">
        {units && units.length > 0 ? (
          <TouchableOpacity
            className="bg-background px-4 py-3.5 rounded-xl flex-row items-center justify-between border border-border active:border-primary"
            accessibilityLabel={t('accessibility.selectUnit')}
            accessibilityRole="button"
            onPress={() => {
              Alert.alert(
                t('foodDetails.selectUnit'),
                "",
                [
                  {
                    text: t('foodDetails.grams'),
                    onPress: () => handleUnitChangeWithConversion(null)
                  },
                  ...(units?.map(u => ({
                    text: `${u.label} (${u.grams}g)`,
                    onPress: () => handleUnitChangeWithConversion(u)
                  })) || []),
                  { text: t('settings.cancel'), style: "cancel" }
                ],
                { cancelable: true }
              );
            }}
          >
            <Text className="text-foreground font-medium text-base flex-1">
              {selectedUnit ? `${selectedUnit.label} (${selectedUnit.grams}g)` : t('foodDetails.grams')}
            </Text>
            <IconSymbol name="chevron.down" size={14} color={Colors[theme].mutedForeground} />
          </TouchableOpacity>
        ) : (
          <View className="bg-background px-4 py-3.5 rounded-xl border border-border">
            <Text className="text-muted-foreground font-medium text-base">{t('foodDetails.grams')}</Text>
          </View>
        )}
      </View>

      {selectedUnit && (
        <Text className="text-sm text-muted-foreground mt-2 text-right">
          = {(parseFloat(quantity) || 0) * selectedUnit.grams} g
        </Text>
      )}
    </View>
  );
}
