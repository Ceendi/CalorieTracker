import React, { Dispatch, SetStateAction } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { FoodProduct } from '@/types/food';

interface VoiceMealSearchProps {
  searchQuery: string;
  setSearchQuery: Dispatch<SetStateAction<string>>;
  setIsSearching: Dispatch<SetStateAction<boolean>>;
  isSearchLoading: boolean;
  searchResults: FoodProduct[] | undefined;
  handleAddManualItem: (item: FoodProduct) => void;
  t: (key: string) => string;
}

export const VoiceMealSearch = ({ 
    searchQuery, setSearchQuery, setIsSearching, isSearchLoading, searchResults, handleAddManualItem, t 
}: VoiceMealSearchProps) => (
    <View className="flex-1 bg-gray-50 dark:bg-slate-950">
        <View className="px-4 pt-6 pb-4 bg-white dark:bg-slate-900 border-b border-gray-100 dark:border-slate-800 shadow-sm z-10">
             <View className="flex-row items-center gap-3">
                 <View className="flex-1 flex-row items-center bg-gray-100 dark:bg-slate-800 rounded-2xl px-3 h-12 border border-transparent">
                    <IconSymbol name="magnifyingglass" size={20} color="#9CA3AF" />
                    <TextInput
                        className="flex-1 ml-3 text-base text-gray-900 dark:text-white h-full"
                        placeholder={t('addFood.searchPlaceholder')}
                        value={searchQuery}
                        onChangeText={setSearchQuery}
                        autoFocus
                        placeholderTextColor="#9CA3AF"
                    />
                    {searchQuery.length > 0 && (
                        <TouchableOpacity onPress={() => setSearchQuery('')}>
                            <IconSymbol name="xmark.circle.fill" size={18} color="#9CA3AF" />
                        </TouchableOpacity>
                    )}
                 </View>
                 <TouchableOpacity onPress={() => setIsSearching(false)}>
                    <Text className="text-indigo-600 font-semibold text-base">{t('settings.cancel')}</Text>
                 </TouchableOpacity>
             </View>
        </View>

        {isSearchLoading ? (
            <View className="flex-1 items-center justify-center">
                <ActivityIndicator size="large" color="#4F46E5" />
            </View>
        ) : (
            <ScrollView 
                className="flex-1 px-4" 
                keyboardShouldPersistTaps="handled" 
                contentContainerStyle={{ paddingTop: 16, paddingBottom: 40 }}
            >
                {searchResults?.map((item, index) => (
                    <TouchableOpacity 
                        key={index}
                        onPress={() => handleAddManualItem(item)}
                        className="flex-row items-center bg-white dark:bg-slate-900 p-4 rounded-xl mb-3 shadow-sm border border-gray-100 dark:border-slate-800/50"
                    >
                        <View className="flex-1 gap-1">
                            <View className="flex-row items-center gap-1.5">
                                <Text className="text-base font-semibold text-gray-900 dark:text-white flex-shrink" numberOfLines={1}>
                                    {item.name}
                                </Text>
                                {item.source === 'fineli' && (
                                     <IconSymbol name="checkmark.seal.fill" size={14} color="#6366f1" />
                                )}
                            </View>
                            <View className="flex-row items-center gap-2">
                                <Text className="text-sm font-medium text-gray-500">{Math.round(item.nutrition.calories_per_100g)} kcal</Text>
                                {item.brand && (
                                    <>
                                        <Text className="text-gray-300">•</Text>
                                        <Text className="text-sm text-gray-400 ml-0.5" numberOfLines={1}>{item.brand}</Text>
                                    </>
                                )}
                            </View>
                        </View>
                        <View className="w-8 h-8 rounded-full bg-indigo-50 dark:bg-indigo-900/20 items-center justify-center">
                            <IconSymbol name="plus" size={18} color="#4F46E5" />
                        </View>
                    </TouchableOpacity>
                ))}
            </ScrollView>
        )}
    </View>
);
