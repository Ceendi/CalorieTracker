import { View, Text, TouchableOpacity, Alert } from 'react-native';
import { useState, useCallback } from 'react';
import { useRouter } from 'expo-router';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { useColorScheme } from '@/hooks/useColorScheme';
import { FoodProduct, MealType } from '@/types/food';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLanguage } from '@/hooks/useLanguage';
import { VoiceMealConfirmation } from '@/components/voice/VoiceMealConfirmation';
import { ProcessedMeal } from '@/hooks/useVoiceInput';
import { useLogEntriesBulk } from '@/hooks/useFood';
import { foodService } from '@/services/food.service';
import { ProductSearchMode } from '@/components/add/ProductSearchMode';
import { PlaceholderMode } from '@/components/add/PlaceholderMode';
import { AudioEntryMode } from '@/components/add/AudioEntryMode';
import { Colors } from '@/constants/theme';
import { formatDateForApi } from '@/utils/date';

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

    const { mutateAsync: logEntriesBulk, isPending: isAddingToDiary } = useLogEntriesBulk();
    
    const theme = colorScheme ?? 'light';
    const cardColor = Colors[theme].card;
    const tintColor = Colors[theme].tint;
    const iconColor = Colors[theme].icon;

    // Removed dynamic tab bar style modification to prevent navigation context issues.
    
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

        try {
            const mealType = MEAL_TYPE_MAP[mealToLog.meal_type] || MealType.SNACK;
            const today = formatDateForApi();

            const bulkItems = mealToLog.items
                .filter(item => item.status === 'matched' && item.product_id)
                .map(item => {
                    const productId = String(item.product_id);

                    let unitGrams = 1;
                    if (item.unit_matched !== 'g' && item.unit_matched !== 'gram' && item.units) {
                        const unit = item.units.find(u => u.label === item.unit_matched);
                        if (unit) unitGrams = unit.grams;
                    }

                    return {
                        product_id: productId,
                        amount_grams: item.quantity_grams,
                        unit_label: item.unit_matched,
                        unit_grams: unitGrams,
                        unit_quantity: item.quantity_unit_value
                    };
                });

            if (bulkItems.length > 0) {
                await logEntriesBulk({
                    date: today,
                    meal_type: mealType,
                    items: bulkItems,
                });
            }

            setShowConfirmation(false);
            setProcessedMeal(null);
            router.replace('/(tabs)');
        } catch (error) {
            console.error('Failed to add meal:', error);
            const msg = error instanceof Error ? error.message : t('common.errors.unknown');
            Alert.alert(
                t('profile.error'),
                t('manualEntry.error') + ` (${msg})`
            );
        }
    }, [processedMeal, t, router, logEntriesBulk]);

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
        <SafeAreaView className="flex-1 bg-background" edges={['top']}> 
            <View className="px-5 pt-2 pb-4">
                 <Text className="text-3xl font-bold text-foreground tracking-tight">{t('addFood.title')}</Text>
                 <Text className="text-muted-foreground text-sm mt-1 font-medium">
                     {new Date().toLocaleDateString(language === 'pl' ? 'pl-PL' : 'en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
                 </Text>
            </View>

            <View className="px-5 mb-2">
                <View className="flex-row bg-muted p-1 rounded-2xl h-12">
                    {modes.map((mode) => {
                        const isActive = activeMode === mode.id;
                        
                        return (
                            <TouchableOpacity
                                key={mode.id}
                                style={{
                                  flex: 1,
                                  flexDirection: 'row',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  borderRadius: 12,
                                  gap: 8,
                                  backgroundColor: isActive ? tintColor : 'transparent',
                                  shadowColor: isActive ? '#000' : undefined,
                                  shadowOffset: isActive ? { width: 0, height: 2 } : undefined,
                                  shadowOpacity: isActive ? 0.15 : 0,
                                  shadowRadius: isActive ? 4 : 0,
                                  elevation: isActive ? 3 : 0
                                }}
                                onPress={() => setActiveMode(mode.id)}
                            >
                                <IconSymbol 
                                    name={mode.icon as any} 
                                    size={16} 
                                    color={isActive ? 'white' : iconColor} 
                                />
                                {isActive && (
                                    <Text className="text-xs font-bold text-white">
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
                isLoading={isAddingToDiary}
            />

            {isAddingToDiary && (
                <View className="absolute inset-0 bg-black/50 items-center justify-center">
                    <View className="bg-card p-6 rounded-2xl items-center">
                        <Text className="text-foreground mt-4 font-medium">
                            {t('addFood.addingToDiary')}
                        </Text>
                    </View>
                </View>
            )}

        </SafeAreaView>
    );
}
