import { Stack, useLocalSearchParams, useRouter } from 'expo-router';
import { format } from 'date-fns';
import { ScrollView, Text, TextInput, TouchableOpacity, View, ActivityIndicator, Alert, KeyboardAvoidingView, Platform, Keyboard, TouchableWithoutFeedback } from 'react-native';
import { useState, useEffect } from 'react';
import { useFoodBarcode, useLogEntry, useCreateFood, useUpdateEntry } from '@/hooks/useFood';
import { foodService } from '@/services/food.service';
import { FoodProduct, CreateEntryDto, MealType, CreateFoodDto, UnitInfo } from '@/types/food';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { useLanguage } from '@/hooks/useLanguage';

export default function FoodDetailsScreen() {
  const params = useLocalSearchParams();
  const router = useRouter();
  const { colorScheme } = useColorScheme();
  const { t } = useLanguage();
  
  const entryId = params.entryId as string;
  const initialAmount = params.initialAmount as string;
  const initialMealType = params.initialMealType as string;
  const initialUnitLabel = params.initialUnitLabel as string;
  const initialUnitGrams = params.initialUnitGrams as string;
  const initialUnitQuantity = params.initialUnitQuantity as string;

  const barcode = params.barcode as string;
  const itemJson = params.item as string;
  
  const [food, setFood] = useState<FoodProduct | null>(null);
  
  const getInitialUnit = (): UnitInfo | null => {
      if (initialUnitLabel && initialUnitGrams) {
          return {
              label: initialUnitLabel,
              grams: parseFloat(initialUnitGrams),
              unit: initialUnitLabel
          };
      }
      return null;
  };
  
  const [selectedUnit, setSelectedUnit] = useState<UnitInfo | null>(getInitialUnit());
    const [quantity, setQuantity] = useState(
        initialUnitQuantity ? String(initialUnitQuantity) : (initialAmount ? String(initialAmount) : '100')
    );
    
    useEffect(() => {
        if (food && !entryId) {
            setSelectedUnit(null);
            setQuantity('100');
        }
    }, [food, entryId]);

    const getInitialMealType = () => {
        if (initialMealType && Object.values(MealType).includes(initialMealType as MealType)) {
            return initialMealType as MealType;
        }
        const hour = new Date().getHours();
        if (hour < 10) return MealType.BREAKFAST;
        if (hour < 13) return MealType.LUNCH;
        if (hour < 17) return MealType.LUNCH;
        if (hour < 20) return MealType.DINNER;
        return MealType.SNACK;
    };
  
    const [selectedMeal, setSelectedMeal] = useState<MealType>(getInitialMealType());
  
    const { data: barcodeFood, isLoading: isLoadingBarcode, error: barcodeError } = useFoodBarcode(barcode || null);
    const { mutate: logEntry, isPending: isLogging } = useLogEntry();
    const { mutate: updateEntry, isPending: isUpdating } = useUpdateEntry();
    const { mutateAsync: createFood, isPending: isCreating } = useCreateFood();
  
    useEffect(() => {
      if (barcodeFood) {
        setFood(barcodeFood);
      } else if (itemJson) {
        try {
          const parsed = JSON.parse(itemJson);
          setFood(parsed);
          
          if (entryId && parsed.id && (!parsed.units || parsed.units.length === 0)) {
              foodService.getFoodById(parsed.id).then(fullProduct => {
                  if (fullProduct && fullProduct.units) {
                      setFood(prev => prev ? { ...prev, units: fullProduct.units } : prev);
                  }
              }).catch(console.error);
          }
        } catch (e) {
          console.error("Failed to parse item", e);
        }
      }
    }, [barcodeFood, itemJson, entryId]);
  
    useEffect(() => {
        if (barcodeError) {
            Alert.alert(t('foodDetails.errorTitle'), t('foodDetails.notFound'), [
                { text: "OK", onPress: () => router.back() }
            ]);
        }
    }, [barcodeError]);
  
  
    const isBusy = isLogging || isCreating || isUpdating || (isLoadingBarcode && !food);
  
    if (isLoadingBarcode && !food) {
      return (
        <View className="flex-1 justify-center items-center bg-gray-50 dark:bg-slate-900">
          <Stack.Screen options={{ title: t('foodDetails.loading'), headerBackTitle: t('settings.cancel') }} />
          <ActivityIndicator size="large" color="#4F46E5" />
        </View>
      );
    }
    
    if (!food && !isLoadingBarcode && !barcodeError && !itemJson) {
         return (
            <View className="flex-1 justify-center items-center bg-gray-50 dark:bg-slate-900">
                <Stack.Screen options={{ title: t('foodDetails.errorTitle'), headerBackTitle: t('settings.cancel') }} />
                <Text className="text-gray-500 dark:text-gray-400">{t('foodDetails.noData')}</Text>
            </View>
         );
    }
  
    if (!food) return null;
  
    const macros = food.nutrition || { calories_per_100g: 0, protein_per_100g: 0, fat_per_100g: 0, carbs_per_100g: 0 };
    
    let currentWeight = parseFloat(quantity) || 0;
    if (selectedUnit) {
        currentWeight = currentWeight * selectedUnit.grams;
    }

    const ratio = currentWeight / 100;
  
    const calories = Math.round((macros.calories_per_100g || 0) * ratio);
    const protein = (macros.protein_per_100g || 0) * ratio;
    const fats = (macros.fat_per_100g || 0) * ratio;
    const carbs = (macros.carbs_per_100g || 0) * ratio;
  
    const handleSave = async () => {
      try {
          if (entryId) {
               updateEntry({
                   id: entryId,
                   amount_grams: currentWeight,
                   meal_type: selectedMeal,
                   date: params.date as string
               }, {
                   onSuccess: () => {
                       router.dismissAll();
                   },
                   onError: (err) => {
                       Alert.alert(t('foodDetails.errorTitle'), "Failed to update entry.");
                   }
               });
               return;
          }
  
          let productId = food.id;
  
          if (!productId) {
              const newFoodPayload: CreateFoodDto = {
                  name: food.name,
                  barcode: food.barcode,
                  nutrition: food.nutrition
              };
              try {
                  const createdFood = await createFood(newFoodPayload);
                  productId = createdFood.id;
              } catch (createError) {
                  if (food.barcode) {
                       try {
                           const existing = await foodService.getFoodByBarcode(food.barcode);
                           if (existing && existing.id) {
                               productId = existing.id;
                           } else {
                               throw createError;
                           }
                       } catch (fetchError) {
                           throw createError;
                       }
                  } else {
                      throw createError;
                  }
              }
          }
  
          if (!productId) {
               Alert.alert(t('foodDetails.errorTitle'), "Failed to resolve product ID");
               return;
          }
          
          const entry: CreateEntryDto = {
              date: format(new Date(), 'yyyy-MM-dd'),
              meal_type: selectedMeal, 
              product_id: productId,
              amount_grams: currentWeight,
              unit_label: selectedUnit?.label,
              unit_grams: selectedUnit?.grams,
              unit_quantity: selectedUnit ? parseFloat(quantity) : undefined
          };
  
          logEntry(entry, {
              onSuccess: () => {
                  router.dismissAll(); 
                  router.replace('/(tabs)'); 
              },
              onError: (err) => {
                  Alert.alert(t('foodDetails.errorTitle'), "Failed to add entry. Please try again.");
                  console.error(err);
              }
          });
  
      } catch (e) {
          Alert.alert(t('foodDetails.errorTitle'), t('foodDetails.creationFailed'));
          console.error(e);
      }
    };
  
    const mealTypeOptions = [
        { label: t('meals.breakfast'), value: MealType.BREAKFAST },
        { label: t('meals.lunch'), value: MealType.LUNCH },
        { label: t('meals.snack'), value: MealType.SNACK },
        { label: t('meals.dinner'), value: MealType.DINNER },
    ];
    
    const dismissKeyboard = () => {
        Keyboard.dismiss();
    };
  
    return (
      <View className="flex-1 bg-gray-50 dark:bg-slate-900">
        <Stack.Screen options={{ title: entryId ? t('dashboard.edit') : t('foodDetails.title'), headerBackTitle: t('settings.cancel') }} />
        <KeyboardAvoidingView 
          behavior={Platform.OS === "ios" ? "padding" : "height"}
          className="flex-1"
          keyboardVerticalOffset={Platform.OS === "ios" ? 100 : 0}
        >
            <View className="flex-1">
                <ScrollView 
                  contentContainerStyle={{ padding: 20 }}
                  keyboardDismissMode="on-drag"
                  keyboardShouldPersistTaps="handled"
                  showsVerticalScrollIndicator={false}
                >
                  <View className="mb-6">
                      <Text className="text-2xl font-bold text-gray-900 dark:text-white">
                          {food.name}
                          {food.source === 'fineli' && (
                              <>
                                {' '}
                                <IconSymbol name="checkmark.seal.fill" size={20} color="#6366f1" style={{ transform: [{ translateY: 5 }] }} />
                              </>
                          )}
                      </Text>
                      {food.brand && food.brand.length > 0 && (
                          <Text className="text-base text-gray-500 dark:text-gray-400 mt-1">{food.brand}</Text>
                      )}
                  </View>
  
                  <View className="bg-white dark:bg-[#283548] rounded-2xl p-4 mb-4 shadow-sm border border-gray-100 dark:border-slate-700 z-50">
                      <Text className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">{t('manualEntry.quantity')}</Text>
                      
                      <View className="flex-row items-stretch gap-2 h-14">
                        <TouchableOpacity 
                            className="w-12 bg-gray-100 dark:bg-slate-900 rounded-xl items-center justify-center"
                            onPress={() => setQuantity(String(Math.max(1, (parseFloat(quantity) || 0) - (selectedUnit ? 1 : 10))))}
                        >
                            <IconSymbol name="minus" size={20} color="#6B7280" />
                        </TouchableOpacity>
                        
                        <TextInput
                              className="flex-1 font-bold text-gray-900 dark:text-white px-4 bg-gray-50 dark:bg-slate-900 rounded-xl text-center"
                              style={{ fontSize: 20 }}
                              value={quantity}
                              onChangeText={(text) => {
                                  const num = parseFloat(text) || 0;
                                  setQuantity(selectedUnit && num < 1 && text.length > 0 ? '1' : text);
                              }}
                              keyboardType="numeric"
                              placeholder="0"
                          />
                        
                        <TouchableOpacity 
                            className="w-12 bg-gray-100 dark:bg-slate-900 rounded-xl items-center justify-center"
                            onPress={() => setQuantity(String((parseFloat(quantity) || 0) + (selectedUnit ? 1 : 10)))}
                        >
                            <IconSymbol name="plus" size={20} color="#6B7280" />
                        </TouchableOpacity>

                        {food.units && food.units.length > 0 ? (
                            <View className="flex-[1.5]">
                                <TouchableOpacity 
                                    className="bg-gray-50 dark:bg-slate-900 px-4 h-full rounded-xl flex-row items-center justify-between border border-transparent active:border-indigo-500"
                                    onPress={() => {
                                        Alert.alert(
                                            t('foodDetails.selectUnit'),
                                            "",
                                            [
                                                { 
                                                    text: t('foodDetails.grams'), 
                                                    onPress: () => {
                                                        setSelectedUnit(null);
                                                        setQuantity('100');
                                                    }
                                                },
                                                ...(food.units?.map(u => ({
                                                    text: `${u.label} (${u.grams}g)`,
                                                    onPress: () => {
                                                        setSelectedUnit(u);
                                                        setQuantity('1');
                                                    }
                                                })) || []),
                                                { text: t('settings.cancel'), style: "cancel" }
                                            ],
                                            { cancelable: true }
                                        );
                                    }}
                                >
                                    <Text className="text-gray-900 dark:text-white font-medium text-base" numberOfLines={1}>
                                        {selectedUnit ? selectedUnit.label : t('foodDetails.grams')}
                                    </Text>
                                    <IconSymbol name="chevron.down" size={14} color="#9CA3AF" />
                                </TouchableOpacity>
                            </View>
                        ) : (
                            <View className="flex-[1.5] bg-gray-50 dark:bg-slate-900 px-4 h-full rounded-xl justify-center">
                                <Text className="text-gray-500 font-medium text-base">{t('foodDetails.grams')}</Text>
                            </View>
                        )}
                      </View>

                      {selectedUnit && (
                          <Text className="text-sm text-gray-400 mt-2 text-right">
                              = {(parseFloat(quantity) || 0) * selectedUnit.grams} g
                          </Text>
                      )}
                  </View>

                <View className="bg-white dark:bg-[#283548] rounded-2xl p-4 mb-4 shadow-sm border border-gray-100 dark:border-slate-700">
                    <Text className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">{t('manualEntry.mealLabel')}</Text>
                    <View className="flex-row flex-wrap gap-2">
                        {mealTypeOptions.map((option) => (
                            <TouchableOpacity
                                key={option.label}
                                className={`px-4 py-2 rounded-full ${selectedMeal === option.value ? 'bg-indigo-600' : 'bg-gray-100 dark:bg-slate-900'}`}
                                onPress={() => setSelectedMeal(option.value)}
                            >
                                <Text className={`text-sm font-medium ${selectedMeal === option.value ? 'text-white' : 'text-gray-600 dark:text-gray-300'}`}>
                                    {option.label}
                                </Text>
                            </TouchableOpacity>
                        ))}
                    </View>
                </View>

                <View className="flex-row bg-white dark:bg-[#283548] rounded-2xl p-5 mb-8 justify-between items-center shadow-sm border border-gray-100 dark:border-slate-700">
                    <View className="items-center flex-1">
                        <Text className="text-xl font-bold text-indigo-600 dark:text-indigo-400 mb-1">{calories}</Text>
                        <Text className="text-xs text-gray-500 dark:text-gray-400">{t('manualEntry.calories')}</Text>
                    </View>
                    <View className="w-px h-10 bg-gray-200 dark:bg-slate-700" />
                    <View className="items-center flex-1">
                        <Text className="text-lg font-bold text-gray-900 dark:text-white mb-1">{protein.toFixed(1)}g</Text>
                        <Text className="text-xs text-gray-500 dark:text-gray-400">{t('manualEntry.protein')}</Text>
                    </View>
                    <View className="w-px h-10 bg-gray-200 dark:bg-slate-700" />
                    <View className="items-center flex-1">
                        <Text className="text-lg font-bold text-gray-900 dark:text-white mb-1">{fats.toFixed(1)}g</Text>
                        <Text className="text-xs text-gray-500 dark:text-gray-400">{t('manualEntry.fat')}</Text>
                    </View>
                    <View className="w-px h-10 bg-gray-200 dark:bg-slate-700" />
                    <View className="items-center flex-1">
                        <Text className="text-lg font-bold text-gray-900 dark:text-white mb-1">{carbs.toFixed(1)}g</Text>
                        <Text className="text-xs text-gray-500 dark:text-gray-400">{t('manualEntry.carbs')}</Text>
                    </View>
                </View>

              </ScrollView>
              
              <View className="bg-white dark:bg-[#283548] border-t border-gray-200 dark:border-slate-700">
                <SafeAreaView edges={['bottom']}>
                  <View className="p-5">
                      <TouchableOpacity 
                        className={`w-full py-4 rounded-xl items-center ${isBusy ? 'bg-indigo-400' : 'bg-indigo-600'}`}
                        onPress={handleSave}
                        disabled={isBusy}
                      >
                          {isBusy ? (
                              <ActivityIndicator color="white" />
                          ) : (
                              <Text className="text-white text-lg font-bold">
                                  {entryId ? t('manualEntry.save') : t('foodDetails.addToDiary')}
                              </Text>
                          )}
                      </TouchableOpacity>
                  </View>
                </SafeAreaView>
              </View>
          </View>
      </KeyboardAvoidingView>
    </View>
  );
}
