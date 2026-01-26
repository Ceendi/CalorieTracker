import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, Pressable, Keyboard, Platform } from 'react-native';
import { IconSymbol } from '@/components/ui/IconSymbol';

import { useSafeAreaInsets } from 'react-native-safe-area-context';

interface VoiceMealSummaryProps {
  totals: {
    kcal: number;
    protein: number;
    fat: number;
    carbs: number;
  };
  onConfirm: () => void;
  onPressStats?: () => void;
  isLoading?: boolean;
  t: (key: string) => string;
}

export const VoiceMealSummary = ({ totals, onConfirm, onPressStats, isLoading, t }: VoiceMealSummaryProps) => {
    const insets = useSafeAreaInsets();
    
    return (
    <View 
        className="bg-background/80 border-t border-border px-4"
        style={{ 
            paddingTop: 12,
            paddingBottom: Math.max(insets.bottom + 12, 24) 
        }}
    >
      <View className="flex-row items-center justify-between">
         <Pressable onPress={onPressStats} className="flex-1">
            <View className="flex-row items-baseline gap-1 mb-0.5">
                <Text className="text-xl font-black text-foreground">
                    {Math.round(totals.kcal)}
                </Text>
                <Text className="text-xs font-bold text-muted-foreground">kcal</Text>
            </View>
            <View className="flex-row items-center gap-3">
                <Text className="text-[10px] font-bold text-sky-500 uppercase">
                    B:{totals.protein.toFixed(0)}
                </Text>
                <Text className="text-[10px] font-bold text-amber-500 uppercase">
                    T:{totals.fat.toFixed(0)}
                </Text>
                <Text className="text-[10px] font-bold text-orange-500 uppercase">
                    W:{totals.carbs.toFixed(0)}
                </Text>
            </View>
         </Pressable>
         
         <TouchableOpacity 
            className={`px-6 py-3 rounded-xl flex-row items-center shadow-md ${
                isLoading ? 'bg-indigo-400' : 'bg-indigo-600 shadow-indigo-200 dark:shadow-none'
            }`}
            onPress={onConfirm}
            disabled={isLoading}
            activeOpacity={0.8}
          >
             <IconSymbol name={isLoading ? "clock" : "checkmark"} size={18} color="white" />
             <Text className="text-white font-bold text-sm ml-2">
                {isLoading ? t('addFood.addingToDiary') || 'Dodawanie...' : 'Dodaj'}
             </Text>
          </TouchableOpacity>
      </View>
    </View>
  );
};
