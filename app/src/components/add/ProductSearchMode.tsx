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
import { useLanguage } from '@/hooks/useLanguage';
import { useColorScheme } from '@/hooks/useColorScheme';
import { Colors } from '@/constants/theme';
import { FoodProduct } from '@/types/food';

interface ProductSearchModeProps {
  onItemPress: (item: FoodProduct) => void;
  onManualPress: () => void;
}

export function ProductSearchMode({ onItemPress, onManualPress }: ProductSearchModeProps) {
  const { t } = useLanguage();
  const { colorScheme } = useColorScheme();
  const theme = colorScheme ?? 'light';
  const tintColor = Colors[theme].tint;
  const iconColor = Colors[theme].icon;
  const placeholderColor = Colors[theme].placeholder;
  const [searchQuery, setSearchQuery] = useState('');
  const { data: searchResults, isLoading, isLoadingExternal, refetch, isRefetching } = useFoodSearch(searchQuery);

  const dismissKeyboard = () => Keyboard.dismiss();

  const renderItem = ({ item }: { item: FoodProduct }) => (
    <TouchableOpacity
      testID={`search-result-${item.id || item.name}`}
      className="bg-card p-3 rounded-2xl mb-2 shadow-sm border border-border"
      onPress={() => onItemPress(item)}
    >
      <View className="flex-row items-center justify-between mb-1">
        <View className="flex-1 mr-2">
          <Text className="text-base font-semibold text-foreground pt-1" numberOfLines={2} style={{ lineHeight: 22 }}>
            {item.name}
            {(item.source === 'fineli' || item.source === 'kunachowicz') && (
              <Text style={{ lineHeight: 22 }}>
                {' '}<IconSymbol name="checkmark.seal.fill" size={16} color={tintColor} />
              </Text>
            )}
          </Text>
          {item.brand && item.brand.length > 0 && (
            <Text className="text-sm text-muted-foreground mt-0.5">{item.brand}</Text>
          )}
        </View>
        <IconSymbol name="plus.circle.fill" size={28} color={tintColor} />
      </View>

      <View className="flex-row items-baseline pt-1 border-t border-gray-200 dark:border-gray-800">
        <Text className="text-base font-bold text-primary">
          {Math.round(item.nutrition?.calories_per_100g || 0)} {t('addFood.summary.kcal')} <Text className="text-xs font-normal text-muted-foreground">/ 100g</Text>
        </Text>
        <Text className="text-sm text-muted-foreground ml-3 flex-1">
          {t('foodDetails.macroP')}: {(item.nutrition?.protein_per_100g || 0).toFixed(1)}  {t('foodDetails.macroF')}: {(item.nutrition?.fat_per_100g || 0).toFixed(1)}  {t('foodDetails.macroC')}: {(item.nutrition?.carbs_per_100g || 0).toFixed(1)}
        </Text>
        {item.glycemic_index != null && (
          <Text className="text-xs font-semibold text-indigo-500 ml-2">
            {t('foodDetails.gl.ig')} {item.glycemic_index}
          </Text>
        )}
      </View>
    </TouchableOpacity>
  );

  return (
    <View className="flex-1 px-5 mt-4">
      <View className="flex-row items-center bg-card rounded-xl px-4 border border-border shadow-sm mb-4 h-14">
        <IconSymbol name="magnifyingglass" size={20} color={iconColor} />
        <TextInput
          testID="search-input"
          className="flex-1 ml-3 text-foreground h-full py-0"
          style={{ fontSize: 16, textAlignVertical: 'center', paddingVertical: 0, includeFontPadding: false, height: '100%' }}
          placeholder={t('addFood.searchPlaceholder')}
          value={searchQuery}
          onChangeText={setSearchQuery}
          placeholderTextColor={placeholderColor}
          autoCapitalize="none"
          returnKeyType="search"
          onSubmitEditing={dismissKeyboard}
        />
        {searchQuery.length > 0 ? (
          <TouchableOpacity onPress={() => { setSearchQuery(''); dismissKeyboard(); }}>
            <IconSymbol name="xmark.circle.fill" size={20} color={iconColor} />
          </TouchableOpacity>
        ) : (
          <TouchableOpacity testID="manual-entry-button" onPress={onManualPress}>
            <IconSymbol name="pencil.circle.fill" size={24} color={tintColor} />
          </TouchableOpacity>
        )}
      </View>

      {isLoading && (
        <TouchableWithoutFeedback onPress={dismissKeyboard}>
          <View className="mt-12 items-center flex-1">
            <ActivityIndicator size="large" color={tintColor} />
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
          ListFooterComponent={isLoadingExternal ? (
            <View className="flex-row items-center justify-center py-4 gap-2">
              <ActivityIndicator size="small" color={tintColor} />
              <Text className="text-muted-foreground text-sm">{t('addFood.searchingExternal')}</Text>
            </View>
          ) : null}
        />
      )}

      {!isLoading && (!searchResults || searchResults.length === 0) && searchQuery.length >= 3 && (
        <TouchableWithoutFeedback onPress={dismissKeyboard}>
          <View className="mt-12 items-center flex-1 gap-2">
            {isLoadingExternal ? (
              <>
                <ActivityIndicator size="large" color={tintColor} />
                <Text className="text-muted-foreground text-sm mt-2">{t('addFood.searchingExternal')}</Text>
              </>
            ) : (
              <Text className="text-muted-foreground text-base">{t('addFood.noResults')}</Text>
            )}
          </View>
        </TouchableWithoutFeedback>
      )}

      {!isLoading && (!searchResults || searchResults.length === 0) && searchQuery.length < 3 && (
        <TouchableWithoutFeedback onPress={dismissKeyboard}>
          <View className="flex-1 items-center justify-center pt-20 px-10">
            <IconSymbol name="magnifyingglass" size={48} color={iconColor} />
            <Text className="text-muted-foreground text-center mt-4">
              {t('addFood.emptyState')}
            </Text>
          </View>
        </TouchableWithoutFeedback>
      )}
    </View>
  );
}
