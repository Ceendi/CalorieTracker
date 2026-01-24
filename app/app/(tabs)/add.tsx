import { View, Text, TouchableOpacity, Alert, Platform, TouchableWithoutFeedback, Keyboard } from 'react-native';
import { useState, useCallback } from 'react';
import { useRouter } from 'expo-router';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { FoodProduct, MealType } from '@/types/food';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLanguage } from '@/hooks/useLanguage';
import { VoiceMealConfirmation } from '@/components/voice/VoiceMealConfirmation';
import { ProcessedMeal } from '@/hooks/useVoiceInput';
import { trackingService } from '@/services/tracking.service';
import { foodService } from '@/services/food.service';
import { ProductSearchMode } from '@/components/add/ProductSearchMode';
import { AudioEntryMode } from '@/components/add/AudioEntryMode';
import { PlaceholderMode } from '@/components/add/PlaceholderMode';

type EntryMode = 'product' | 'audio' | 'photo' | 'barcode';

const MEAL_TYPE_MAP: Record<string, MealType> = {
    'śniadanie': MealType.BREAKFAST,
    'drugie_śniadanie': MealType.SNACK,
    'obiad': MealType.LUNCH,
    'podwieczorek': MealType.SNACK,
    'kolacja': MealType.DINNER,
    'przekąska': MealType.SNACK,
    'breakfast': MealType.BREAKFAST,
    'second_breakfast': MealType.SNACK,
    'lunch': MealType.LUNCH,
    'tea': MealType.SNACK,
    'dinner': MealType.DINNER,
    'snack': MealType.SNACK,
};

export default function AddScreen() {
    const router = useRouter();
    const { colorScheme } = useColorScheme();
    const { t, language } = useLanguage();
    const [activeMode, setActiveMode] = useState<EntryMode>('product');
    
    const [processedMeal, setProcessedMeal] = useState<ProcessedMeal | null>(null);
    const [showConfirmation, setShowConfirmation] = useState(false);
    const [isAddingToDiary, setIsAddingToDiary] = useState(false);

    const handleItemPress = (item: FoodProduct) => {
        router.push({
            pathname: '/food-details',
            params: { item: JSON.stringify(item) }
        });
    };

    const handleManualPress = () => {
        router.push('/manual-entry');
    };

    const handleMealProcessed = useCallback((meal: ProcessedMeal) => {
        setProcessedMeal(meal);
        setShowConfirmation(true);
    }, []);

    const handleVoiceError = useCallback((error: string) => {
        Alert.alert(
            t('addFood.voiceError'),
            error,
            [{ text: 'OK' }]
        );
    }, [t]);

    const handleConfirmMeal = useCallback(async (updatedMeal?: ProcessedMeal) => {
        const mealToLog = updatedMeal || processedMeal;
        if (!mealToLog) return;

        setIsAddingToDiary(true);
        try {
            const mealType = MEAL_TYPE_MAP[mealToLog.meal_type] || MealType.SNACK;
            const today = new Date().toISOString().split('T')[0];

            for (const item of mealToLog.items) {
                if (item.status === 'matched' && item.product_id) {
                    let productId = String(item.product_id);
                    const isUUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(productId);
                    
                    if (!isUUID) {
                        try {
                            if (item.name.length > 2) {
                                const results = await foodService.searchFoods(item.name);
                                const match = results.find(f => f.name.toLowerCase() === item.name.toLowerCase()) || results[0];
                                if (match && match.id) {
                                    productId = match.id;
                                }
                            }
                        } catch (err) {
                            console.warn("Failed to resolve UUID for product", item.name);
                        }
                    }
                    
                    await trackingService.logEntry({
                        date: today,
                        product_id: productId,
                        amount_grams: item.quantity_grams,
                        meal_type: mealType,
                    });
                }
            }

            setShowConfirmation(false);
            setProcessedMeal(null);

            Alert.alert(
                '✅ ' + t('addFood.mealAdded'),
                t('addFood.mealAddedDesc'),
                [{
                    text: 'OK',
                    onPress: () => router.push('/(tabs)')
                }]
            );
        } catch (error) {
            console.error('Failed to add meal:', error);
            const msg = error instanceof Error ? error.message : t('common.errors.unknown');
            Alert.alert(
                t('profile.error'),
                t('manualEntry.error') + ` (${msg})`
            );
        } finally {
            setIsAddingToDiary(false);
        }
    }, [processedMeal, t, router]);

    const handleEditMeal = useCallback(() => {
        setShowConfirmation(false);
        Alert.alert(
            t('addFood.editInfo'),
            t('addFood.editInfoDesc'),
            [{ text: 'OK' }]
        );
    }, [t]);

    const handleCancelConfirmation = useCallback(() => {
        setShowConfirmation(false);
        setProcessedMeal(null);
    }, []);

    const modes: { id: EntryMode; icon: string; label: string }[] = [
        { id: 'product', icon: 'magnifyingglass', label: t('addFood.modes.product') },
        { id: 'barcode', icon: 'barcode.viewfinder', label: t('addFood.modes.scan') },
        { id: 'audio', icon: 'mic.fill', label: t('addFood.modes.audio') },
        { id: 'photo', icon: 'camera.fill', label: t('addFood.modes.photo') },
    ];

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
                                className={`flex-1 flex-row items-center justify-center rounded-[12px] gap-2 ${
                                    isActive 
                                        ? (colorScheme === 'dark' ? 'bg-slate-700' : 'bg-white shadow-sm') 
                                        : 'bg-transparent'
                                }`}
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
                {activeMode === 'product' && (
                    <ProductSearchMode 
                        onItemPress={handleItemPress} 
                        onManualPress={handleManualPress} 
                    />
                )}
                {activeMode === 'audio' && (
                    <AudioEntryMode 
                        onMealProcessed={handleMealProcessed} 
                        onError={handleVoiceError} 
                    />
                )}
                {activeMode === 'photo' && (
                    <PlaceholderMode
                        title={t('addFood.placeholders.photoTitle') || "Zdjęcie"}
                        icon="camera.fill"
                        description={t('addFood.placeholders.photoDesc') || "Zrób zdjęcie posiłku, aby go dodać"}
                    />
                )}
                {activeMode === 'barcode' && (
                    <PlaceholderMode
                        title={t('addFood.placeholders.barcodeTitle') || "Kod kreskowy"}
                        icon="barcode.viewfinder"
                        description={t('addFood.placeholders.barcodeDesc') || "Zeskanuj kod kreskowy produktu"}
                        actionTitle={t('addFood.startScanning')}
                        onAction={() => router.push('/scanner')}
                    />
                )}
            </View>

            <VoiceMealConfirmation
                visible={showConfirmation}
                meal={processedMeal}
                onConfirm={handleConfirmMeal}
                onEdit={handleEditMeal}
                onCancel={handleCancelConfirmation}
            />

            {isAddingToDiary && (
                <View className="absolute inset-0 bg-black/50 items-center justify-center">
                    <View className="bg-white dark:bg-slate-800 p-6 rounded-2xl items-center">
                        <Text className="text-gray-900 dark:text-white mt-4 font-medium">
                            {t('addFood.addingToDiary')}
                        </Text>
                    </View>
                </View>
            )}

        </SafeAreaView>
    );
}
