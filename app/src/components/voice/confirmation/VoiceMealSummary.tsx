import React from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { IconSymbol } from '@/components/ui/IconSymbol';

interface VoiceMealSummaryProps {
  totals: {
    kcal: number;
    protein: number;
    fat: number;
    carbs: number;
  };
  onConfirm: () => void;
  t: (key: string) => string;
}

export const VoiceMealSummary = ({ totals, onConfirm, t }: VoiceMealSummaryProps) => (
    <View 
        className="bg-white dark:bg-slate-900 border-t border-gray-100 dark:border-slate-800 pt-4 px-4 shadow-[0_-4px_10px_rgba(0,0,0,0.03)] dark:shadow-none"
        style={{ paddingBottom: 40 }}
    >
      <View className="flex-row items-center justify-between mb-4 px-1">
         <View>
            <Text className="text-xs text-gray-500 font-medium uppercase tracking-wide mb-0.5">{t('addFood.summaryTitle')}</Text>
            <View className="flex-row items-baseline gap-1">
                <Text className="text-2xl font-black text-gray-900 dark:text-white">{Math.round(totals.kcal)}</Text>
                <Text className="text-sm font-bold text-gray-500">kcal</Text>
            </View>
         </View>
         <View className="flex-row gap-3">
             <View className="items-end">
                <Text className="text-xs text-gray-400 font-medium">B</Text>
                <Text className="font-bold text-sky-500">{totals.protein.toFixed(0)}g</Text>
             </View>
             <View className="items-end">
                <Text className="text-xs text-gray-400 font-medium">T</Text>
                <Text className="font-bold text-amber-500">{totals.fat.toFixed(0)}g</Text>
             </View>
             <View className="items-end">
                <Text className="text-xs text-gray-400 font-medium">W</Text>
                <Text className="font-bold text-orange-500">{totals.carbs.toFixed(0)}g</Text>
             </View>
         </View>
      </View>
      
      <TouchableOpacity 
        className="w-full bg-indigo-600 py-4 rounded-2xl flex-row items-center justify-center shadow-lg shadow-indigo-200 dark:shadow-indigo-900/30"
        onPress={onConfirm}
        activeOpacity={0.8}
      >
         <IconSymbol name="checkmark" size={20} color="white" />
         <Text className="text-white font-bold text-base ml-2">{t('addFood.buttons.addToDiary')}</Text>
      </TouchableOpacity>
    </View>
);
