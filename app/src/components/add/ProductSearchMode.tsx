import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  TouchableWithoutFeedback,
  Keyboard,
} from 'react-native';
import { useFoodSearch } from '@/hooks/useFood';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { useLanguage } from '@/hooks/useLanguage';
import { FoodProduct } from '@/types/food';

interface ProductSearchModeProps {
  onItemPress: (item: FoodProduct) => void;
  onManualPress: () => void;
}

export function ProductSearchMode({ onItemPress, onManualPress }: ProductSearchModeProps) {
  const { t } = useLanguage();
  const { colorScheme } = useColorScheme();
  const [searchQuery, setSearchQuery] = useState('');
  const { data: searchResults, isLoading, refetch, isRefetching } = useFoodSearch(searchQuery);

  const dismissKeyboard = () => Keyboard.dismiss();

  const renderItem = ({ item }: { item: FoodProduct }) => (
    <TouchableOpacity
      className="bg-white dark:bg-[#283548] p-3 rounded-2xl mb-2 shadow-sm border border-gray-100 dark:border-slate-700/50"
      onPress={() => onItemPress(item)}
    >
      <View className="flex-row items-center justify-between mb-1">
        <View className="flex-1 mr-2">
          <Text className="text-base font-semibold text-gray-900 dark:text-white" numberOfLines={2}>
            {item.name}
            {item.source === 'fineli' && (
              <>
                {' '}
                <IconSymbol name="checkmark.seal.fill" size={16} color="#6366f1" style={{ transform: [{ translateY: 4 }] }} />
              </>
            )}
          </Text>
          {item.brand && item.brand.length > 0 && (
            <Text className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{item.brand}</Text>
          )}
        </View>
        <IconSymbol name="plus.circle.fill" size={28} color="#4F46E5" />
      </View>

      <View className="flex-row items-baseline pt-1 border-t border-gray-50 dark:border-slate-700/50">
        <Text className="text-base font-bold text-indigo-600 dark:text-indigo-400">
          {Math.round(item.nutrition?.calories_per_100g || 0)} {t('addFood.summary.kcal')} <Text className="text-xs font-normal text-gray-400">/ 100g</Text>
        </Text>
        <Text className="text-sm text-gray-400 ml-3">
          {t('foodDetails.macroP')}:{(item.nutrition?.protein_per_100g || 0).toFixed(1)} {t('foodDetails.macroF')}:{(item.nutrition?.fat_per_100g || 0).toFixed(1)} {t('foodDetails.macroC')}:{(item.nutrition?.carbs_per_100g || 0).toFixed(1)}
        </Text>
      </View>
    </TouchableOpacity>
  );

  return (
    <View className="flex-1 px-5 mt-4">
      <View className="flex-row items-center bg-white dark:bg-slate-800 rounded-xl px-4 border border-gray-200 dark:border-slate-700 shadow-sm mb-4 h-14">
        <IconSymbol name="magnifyingglass" size={20} color={colorScheme === 'dark' ? '#9CA3AF' : '#6B7280'} />
        <TextInput
          className="flex-1 ml-3 text-gray-900 dark:text-white text-base h-full py-0"
          placeholder={t('addFood.searchPlaceholder')}
          value={searchQuery}
          onChangeText={setSearchQuery}
          placeholderTextColor={colorScheme === 'dark' ? '#6B7280' : '#9CA3AF'}
          autoCapitalize="none"
          returnKeyType="search"
          onSubmitEditing={dismissKeyboard}
        />
        {searchQuery.length > 0 ? (
          <TouchableOpacity onPress={() => { setSearchQuery(''); dismissKeyboard(); }}>
            <IconSymbol name="xmark.circle.fill" size={20} color={colorScheme === 'dark' ? '#6B7280' : '#9CA3AF'} />
          </TouchableOpacity>
        ) : (
          <TouchableOpacity onPress={onManualPress}>
            <IconSymbol name="pencil.circle.fill" size={24} color="#4F46E5" />
          </TouchableOpacity>
        )}
      </View>

      {isLoading && (
        <TouchableWithoutFeedback onPress={dismissKeyboard}>
          <View className="mt-12 items-center flex-1">
            <ActivityIndicator size="large" color="#4F46E5" />
          </View>
        </TouchableWithoutFeedback>
      )}

      {!isLoading && searchResults && searchResults.length > 0 && (
        <FlatList
          data={searchResults}
          keyExtractor={(item, index) => item.id || index.toString() + item.name}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ paddingBottom: 100 }}
          keyboardDismissMode="on-drag"
          keyboardShouldPersistTaps="handled"
          renderItem={renderItem}
          onRefresh={refetch}
          refreshing={Boolean(isRefetching)}
          ListEmptyComponent={
            <TouchableWithoutFeedback onPress={dismissKeyboard}>
              <View className="flex-1 items-center justify-center pt-16 h-full">
                <Text className="text-gray-400 text-base">{t('addFood.noResults')}</Text>
              </View>
            </TouchableWithoutFeedback>
          }
        />
      )}

      {!isLoading && (!searchResults || searchResults.length === 0) && searchQuery.length < 3 && (
        <TouchableWithoutFeedback onPress={dismissKeyboard}>
          <View className="flex-1 items-center justify-center pt-20 px-10">
            <IconSymbol name="magnifyingglass" size={48} color={colorScheme === 'dark' ? '#334155' : '#E2E8F0'} />
            <Text className="text-gray-400 dark:text-gray-500 text-center mt-4">
              {t('addFood.emptyState')}
            </Text>
          </View>
        </TouchableWithoutFeedback>
      )}
    </View>
  );
}
