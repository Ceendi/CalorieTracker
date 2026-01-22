import { View, Text, TextInput, TouchableOpacity, FlatList, ActivityIndicator, Platform, Keyboard, TouchableWithoutFeedback } from 'react-native';
import { useState } from 'react';
import { useRouter } from 'expo-router';
import { useFoodSearch } from '@/hooks/useFood';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { FoodProduct } from '@/types/food';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLanguage } from '@/hooks/useLanguage';

type EntryMode = 'product' | 'audio' | 'photo' | 'barcode';

export default function AddScreen() {
    const router = useRouter();
    const { colorScheme } = useColorScheme();
    const { t, language } = useLanguage();
    const [activeMode, setActiveMode] = useState<EntryMode>('product');
    const [searchQuery, setSearchQuery] = useState('');
    
    const { data: searchResults, isLoading, refetch, isRefetching } = useFoodSearch(searchQuery);

    const handleItemPress = (item: FoodProduct) => {
        router.push({
            pathname: '/food-details',
            params: { item: JSON.stringify(item) }
        });
    };

    const handleManualPress = () => {
        router.push('/manual-entry');
    };

    const dismissKeyboard = () => {
        Keyboard.dismiss();
    };

    const modes: { id: EntryMode; icon: string; label: string }[] = [
        { id: 'product', icon: 'magnifyingglass', label: t('addFood.modes.product') },
        { id: 'barcode', icon: 'barcode.viewfinder', label: t('addFood.modes.scan') },
        { id: 'audio', icon: 'mic.fill', label: t('addFood.modes.audio') },
        { id: 'photo', icon: 'camera.fill', label: t('addFood.modes.photo') },
    ];

    const renderProductMode = () => (
        <View className="flex-1 px-5 mt-4">
            <View className="flex-row items-center bg-white dark:bg-slate-800 rounded-xl px-4 border border-gray-200 dark:border-slate-700 shadow-sm mb-4 h-14">
                <IconSymbol name="magnifyingglass" size={20} color={colorScheme === 'dark' ? '#9CA3AF' : '#6B7280'} />
                <TextInput
                    className="flex-1 ml-3 text-gray-900 dark:text-white p-0"
                    style={{ fontSize: 16, paddingVertical: 0, height: '100%' }}
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
                     <TouchableOpacity onPress={handleManualPress}>
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
                    renderItem={({ item }) => (
                         <TouchableOpacity 
                             className="bg-white dark:bg-[#283548] p-3 rounded-2xl mb-2 shadow-sm border border-gray-100 dark:border-slate-700/50"
                             onPress={() => handleItemPress(item)}
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
                                    {Math.round(item.nutrition?.calories_per_100g || 0)} kcal <Text className="text-xs font-normal text-gray-400">/ 100g</Text>
                                </Text>
                                <Text className="text-sm text-gray-400 ml-3">
                                   {t('foodDetails.macroP')}:{(item.nutrition?.protein_per_100g || 0).toFixed(1)} {t('foodDetails.macroF')}:{(item.nutrition?.fat_per_100g || 0).toFixed(1)} {t('foodDetails.macroC')}:{(item.nutrition?.carbs_per_100g || 0).toFixed(1)}
                                </Text>
                            </View>
                         </TouchableOpacity>
                    )}
                    onRefresh={refetch}
                    refreshing={isRefetching}
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

    const renderPlaceholderMode = (title: string, icon: string, description: string, action?: () => void) => (
         <View className="flex-1 items-center justify-center px-8 -mt-20">
             <View className="w-32 h-32 bg-indigo-50 dark:bg-slate-800 rounded-full items-center justify-center mb-8 shadow-sm">
                 <IconSymbol name={icon as any} size={56} color="#4F46E5" />
             </View>
             <Text className="text-2xl font-bold text-gray-900 dark:text-white mb-4 text-center">{title}</Text>
             <Text className="text-base text-gray-500 dark:text-gray-400 text-center leading-6 mb-8">
                 {description}
             </Text>
             
             {action && (
                 <TouchableOpacity 
                    className="bg-indigo-600 px-8 py-4 rounded-full shadow-lg shadow-indigo-200 dark:shadow-none"
                    onPress={action}
                 >
                     <Text className="text-white text-lg font-bold">{t('addFood.startScanning')}</Text>
                 </TouchableOpacity>
             )}
         </View>
    );


    return (
        <SafeAreaView className="flex-1 bg-gray-50 dark:bg-slate-900" edges={['top']}> 

            <View className="px-5 pt-2 pb-4">
                 <Text className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight">{t('addFood.title')}</Text>
                 <Text className="text-gray-500 dark:text-gray-400 text-sm mt-1 font-medium">
                     {new Date().toLocaleDateString(language === 'pl' ? 'pl-PL' : 'en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
                 </Text>
            </View>

            <View className="px-5 mb-2">
                <View className="flex-row bg-gray-200 dark:bg-slate-800 p-1 rounded-2xl h-12">
                    {modes.map((mode) => {
                        const isActive = activeMode === mode.id;
                        return (
                            <TouchableOpacity
                                key={mode.id}
                                style={{ flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', borderRadius: 12, gap: 8, backgroundColor: isActive ? (colorScheme === 'dark' ? '#334155' : 'white') : 'transparent' }}
                                onPress={() => setActiveMode(mode.id)}
                            >
                                <IconSymbol 
                                    name={mode.icon as any} 
                                    size={16} 
                                    color={isActive ? (colorScheme === 'dark' ? '#fff' : '#4F46E5') : '#9CA3AF'} 
                                />
                                {isActive && (
                                    <Text className="text-xs font-bold text-gray-900 dark:text-white">
                                        {mode.label}
                                    </Text>
                                )}
                            </TouchableOpacity>
                        );
                    })}
                </View>
            </View>

            <View className="flex-1">
                {activeMode === 'product' && renderProductMode()}
                {activeMode === 'audio' && renderPlaceholderMode(t('addFood.placeholders.voiceTitle'), "mic.fill", t('addFood.placeholders.voiceDesc'))}
                {activeMode === 'photo' && renderPlaceholderMode(t('addFood.placeholders.photoTitle'), "camera.fill", t('addFood.placeholders.photoDesc'))}
                {activeMode === 'barcode' && renderPlaceholderMode(t('addFood.placeholders.barcodeTitle'), "barcode.viewfinder", t('addFood.placeholders.barcodeDesc'), () => router.push('/scanner'))}
            </View>

        </SafeAreaView>
    );
}
