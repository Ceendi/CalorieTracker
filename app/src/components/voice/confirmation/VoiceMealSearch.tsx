import React, { Dispatch, SetStateAction } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { FoodProduct } from '@/types/food';
import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/useColorScheme';

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
}: VoiceMealSearchProps) => {
    const { colorScheme } = useColorScheme();
    const theme = colorScheme ?? 'light';
    
    return (
    <View className="flex-1 bg-background">
        <View className="px-4 pt-4 pb-3 bg-background/50 border-b border-border z-10">
             <View className="flex-row items-center gap-3">
                 <View className="flex-row items-center bg-muted rounded-2xl px-3 h-12 border border-transparent flex-1">
                    <IconSymbol name="magnifyingglass" size={20} color={Colors[theme].icon} />
                    <TextInput
                        className="flex-1 ml-3 text-base text-foreground h-full"
                        placeholder={t('addFood.searchPlaceholder')}
                        value={searchQuery}
                        onChangeText={setSearchQuery}
                        autoFocus
                        placeholderTextColor={Colors[theme].placeholder}
                    />
                    {searchQuery.length > 0 && (
                        <TouchableOpacity onPress={() => setSearchQuery('')}>
                            <IconSymbol name="xmark.circle.fill" size={18} color={Colors[theme].icon} />
                        </TouchableOpacity>
                    )}
                 </View>
                 <TouchableOpacity onPress={() => setIsSearching(false)}>
                    <Text className="text-primary font-semibold text-base">{t('settings.cancel')}</Text>
                 </TouchableOpacity>
             </View>
        </View>

        {isSearchLoading ? (
            <View className="flex-1 items-center justify-center">
                <ActivityIndicator size="large" color={Colors[theme].tint} />
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
                        className="flex-row items-center bg-card p-4 rounded-xl mb-3 shadow-sm border border-border"
                    >
                        <View className="flex-1 gap-1">
                            <View className="flex-row items-center gap-1.5">
                                <Text className="text-base font-semibold text-foreground flex-shrink" numberOfLines={1}>
                                    {item.name}
                                </Text>
                                {item.source === 'fineli' && (
                                     <IconSymbol name="checkmark.seal.fill" size={14} color={Colors[theme].tint} />
                                )}
                            </View>
                            <View className="flex-row items-center gap-2">
                                <Text className="text-sm font-medium text-muted-foreground">{Math.round(item.nutrition.calories_per_100g)} kcal</Text>
                                {item.brand && (
                                    <>
                                        <Text className="text-muted-foreground">•</Text>
                                        <Text className="text-sm text-muted-foreground ml-0.5" numberOfLines={1}>{item.brand}</Text>
                                    </>
                                )}
                            </View>
                        </View>
                        <View className="w-8 h-8 rounded-full bg-primary/10 items-center justify-center">
                            <IconSymbol name="plus" size={18} color={Colors[theme].tint} />
                        </View>
                    </TouchableOpacity>
                ))}
            </ScrollView>
        )}
    </View>
);
};
