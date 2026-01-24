import React, { Dispatch, SetStateAction } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, Pressable, Alert } from 'react-native';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { VoiceMealSummary } from './VoiceMealSummary';
import { ProcessedMeal, ProcessedFoodItem } from '@/services/ai.service'; 

interface VoiceMealReviewProps {
  localMeal: ProcessedMeal;
  onCancel: () => void;
  textColor: string;
  cycleMealType: () => void;
  getMealTypeLabel: (type: string) => string;
  editingItemIndex: number | null;
  setEditingItemIndex: Dispatch<SetStateAction<number | null>>;
  tempQuantity: string;
  setTempQuantity: Dispatch<SetStateAction<string>>;
  handleUpdateQuantity: (index: number, val: number, unit?: any) => void;
  handleRemoveItem: (index: number) => void;
  setIsSearching: Dispatch<SetStateAction<boolean>>;
  totals: { kcal: number; protein: number; fat: number; carbs: number };
  onConfirm: () => void;
  t: (key: string) => string;
}

export const VoiceMealReview = ({
    localMeal,
    onCancel,
    textColor,
    cycleMealType,
    getMealTypeLabel,
    editingItemIndex,
    setEditingItemIndex,
    tempQuantity,
    setTempQuantity,
    handleUpdateQuantity,
    handleRemoveItem,
    setIsSearching,
    totals,
    onConfirm,
    t
}: VoiceMealReviewProps) => {
   if (!localMeal) return null;
   
   return (
    <View className="flex-1">
        <View className="px-5 pt-6 pb-6 bg-white dark:bg-slate-900">
            <View className="flex-row justify-between items-start mb-4">
                <TouchableOpacity onPress={onCancel} className="p-2 -ml-2 rounded-full">
                    <IconSymbol name="xmark" size={24} color={textColor} />
                </TouchableOpacity>
                <View className="items-end">
                     <Text className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-0.5">Potwierdź posiłek</Text>
                     <TouchableOpacity 
                        className="flex-row items-center gap-1.5 bg-gray-50 dark:bg-slate-800 px-3 py-1.5 rounded-full"
                        onPress={cycleMealType}
                     >
                        <Text className="text-lg font-bold text-gray-900 dark:text-white capitalize">
                            {getMealTypeLabel(localMeal.meal_type)}
                        </Text>
                        <IconSymbol name="chevron.down" size={14} color="#6366f1" />
                     </TouchableOpacity>
                </View>
            </View>

            {localMeal.raw_transcription && (
                <View className="bg-indigo-50/50 dark:bg-slate-800/50 p-3 rounded-lg border-l-4 border-indigo-400">
                    <Text className="text-indigo-900 dark:text-indigo-200 italic leading-relaxed">
                        "{localMeal.raw_transcription}"
                    </Text>
                </View>
            )}
        </View>

        <View className="flex-1 bg-gray-50 dark:bg-slate-950">
            <ScrollView 
                className="flex-1 px-5 pt-6" 
                contentContainerStyle={{ paddingBottom: 40 }}
                keyboardShouldPersistTaps="handled" 
                showsVerticalScrollIndicator={false}
            >
                {(localMeal.items || []).map((item: ProcessedFoodItem, index: number) => { 
                    const isEditing = editingItemIndex === index;
                    return (
                    <Pressable 
                        key={index}
                        onPress={(e) => { e.stopPropagation(); setEditingItemIndex(index); setTempQuantity(item.quantity_unit_value.toString()); }}
                        className="mb-3 p-4 bg-white dark:bg-slate-900 rounded-2xl border"
                        style={{
                            borderColor: isEditing ? '#6366f1' : 'transparent',
                        }}
                    >
                        <View className="flex-row justify-between items-start mb-3">
                            <View className="flex-1">
                                <Text className="text-lg font-bold text-gray-900 dark:text-white leading-tight mb-1">{item.name}</Text>
                                {item.brand && <Text className="text-xs text-gray-400 font-medium">{item.brand}</Text>}
                            </View>
                            <TouchableOpacity 
                                onPress={() => handleRemoveItem(index)}
                                className="p-2 -mr-2 -mt-2 opacity-50"
                            >
                                <IconSymbol name="xmark" size={16} color="#9CA3AF" />
                            </TouchableOpacity>
                        </View>

                        <View className="flex-row items-center justify-between">
                            {isEditing ? (
                                <View className="flex-row items-center gap-2">
                                     <View className="w-20 h-10 bg-gray-50 dark:bg-slate-800 border border-indigo-300 dark:border-indigo-700 rounded-xl justify-center items-center">
                                        <TextInput
                                            className="text-lg font-bold text-center text-gray-900 dark:text-white p-0 h-full w-full"
                                            value={tempQuantity}
                                            onChangeText={setTempQuantity}
                                            keyboardType="decimal-pad"
                                            autoFocus
                                            selectTextOnFocus
                                            textAlignVertical="center" 
                                            onBlur={() => {
                                                const val = parseFloat(tempQuantity.replace(',', '.'));
                                                if (!isNaN(val) && val >= 0) handleUpdateQuantity(index, val);
                                                else setEditingItemIndex(null);
                                            }}
                                            onSubmitEditing={() => {
                                                const val = parseFloat(tempQuantity.replace(',', '.'));
                                                if (!isNaN(val) && val >= 0) handleUpdateQuantity(index, val);
                                            }}
                                        />
                                     </View>
                                     
                                     {item.units && item.units.length > 0 && (
                                         <TouchableOpacity
                                            onPress={() => {
                                                const currentVal = parseFloat(tempQuantity.replace(',', '.'));
                                                const valToUse = (!isNaN(currentVal) && currentVal > 0) ? currentVal : item.quantity_unit_value;

                                                Alert.alert(
                                                    t('foodDetails.selectUnit'), "",
                                                    [
                                                        { text: t('foodDetails.grams'), onPress: () => handleUpdateQuantity(index, valToUse, null) },
                                                        ...item.units!.map((u:any) => ({ text: `${u.label} (${u.grams}g)`, onPress: () => handleUpdateQuantity(index, valToUse, u) })),
                                                        { text: t('settings.cancel'), style: 'cancel' }
                                                    ],
                                                    { cancelable: true }
                                                );
                                            }}
                                            className="px-3 py-2 bg-indigo-50 dark:bg-indigo-900/30 rounded-xl flex-row items-center gap-1"
                                         >
                                            <Text className="text-sm font-semibold text-indigo-700 dark:text-indigo-300">
                                                {item.unit_matched === 'g' ? 'gramy' : item.unit_matched}
                                            </Text>
                                            <IconSymbol name="chevron.down" size={12} color="#6366f1" />
                                         </TouchableOpacity>
                                     )}
                                </View>
                            ) : (
                                <View className="flex-row items-baseline gap-1">
                                    <Text className="text-2xl font-black text-gray-900 dark:text-white">
                                        {item.unit_matched === 'g' || item.unit_matched === 'gram' ? item.quantity_grams : item.quantity_unit_value}
                                    </Text>
                                    <Text className="text-sm font-semibold text-gray-500">
                                        {item.unit_matched === 'g' || item.unit_matched === 'gram' ? 'g' : item.unit_matched}
                                    </Text>
                                </View>
                            )}

                            <View className="items-end">
                                <Text className="text-lg font-bold text-gray-900 dark:text-white">
                                    {Math.round(item.kcal)} <Text className="text-xs text-gray-400 font-normal">kcal</Text>
                                </Text>
                            </View>
                        </View>
                    </Pressable>
                )})}

                <TouchableOpacity 
                    onPress={() => setIsSearching(true)}
                    className="mt-2 mb-8 flex-row items-center justify-center p-4 border-2 border-dashed border-gray-200 dark:border-slate-800 rounded-2xl"
                >
                    <IconSymbol name="plus" size={20} color="#9CA3AF" />
                    <Text className="text-gray-500 font-semibold ml-2">{t('addFood.searchToConfirm') || 'Dodaj kolejny produkt'}</Text>
                </TouchableOpacity>
            </ScrollView>
            
            <VoiceMealSummary totals={totals} onConfirm={onConfirm} t={t} />
        </View>
    </View>
   );
};
