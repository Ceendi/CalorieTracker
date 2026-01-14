import { Stack, useRouter } from 'expo-router';
import { format } from 'date-fns';
import { ScrollView, Text, TextInput, TouchableOpacity, View, ActivityIndicator, Alert, KeyboardAvoidingView, Platform, TouchableWithoutFeedback, Keyboard } from 'react-native';
import { useState } from 'react';
import { useLogEntry, useCreateFood } from '@/hooks/useFood';
import { CreateEntryDto, MealType, CreateFoodDto } from '@/types/food';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { useLanguage } from '@/hooks/useLanguage';

export default function ManualEntryScreen() {
  const router = useRouter();
  const { colorScheme } = useColorScheme();
  const { t } = useLanguage();

  const [name, setName] = useState('');
  const [calories, setCalories] = useState('');
  const [protein, setProtein] = useState('');
  const [fat, setFat] = useState('');
  const [carbs, setCarbs] = useState('');
  const [weight, setWeight] = useState('100');
  const [selectedMeal, setSelectedMeal] = useState<MealType>(MealType.BREAKFAST);

  const { mutate: logEntry, isPending: isLogging } = useLogEntry();
  const { mutateAsync: createFood, isPending: isCreating } = useCreateFood();

  const isBusy = isLogging || isCreating;

  const handleSave = async () => {
      if (!name.trim()) {
          Alert.alert(t('manualEntry.error'), t('manualEntry.validationName'));
          return;
      }

      const caloriesVal = parseFloat(calories) || 0;
      const proteinVal = parseFloat(protein) || 0;
      const fatVal = parseFloat(fat) || 0;
      const carbsVal = parseFloat(carbs) || 0;
      const weightVal = parseFloat(weight) || 100;

      try {
          const newFoodPayload: CreateFoodDto = {
              name: name,
              nutrition: {
                  calories_per_100g: caloriesVal,
                  protein_per_100g: proteinVal,
                  fat_per_100g: fatVal,
                  carbs_per_100g: carbsVal
              }
          };
          
          let productId;
          try {
              const createdFood = await createFood(newFoodPayload);
              productId = createdFood.id;
          } catch (err) {
              console.error("Create manual food failed", err);
              Alert.alert(t('manualEntry.error'), t('manualEntry.createFailed'));
              return;
          }

          if (!productId) {
             Alert.alert(t('manualEntry.error'), "Failed to resolve product ID");
             return;
          }

          const entry: CreateEntryDto = {
              date: format(new Date(), 'yyyy-MM-dd'),
              meal_type: selectedMeal, 
              product_id: productId,
              amount_grams: weightVal
          };

          logEntry(entry, {
              onSuccess: () => {
                  router.dismissAll();
                  router.replace('/(tabs)');
              },
              onError: (err) => {
                  Alert.alert(t('manualEntry.error'), "Failed to add entry. Please try again.");
                  console.error(err);
              }
          });

      } catch (e) {
          Alert.alert(t('manualEntry.error'), t('auth.unexpectedError'));
          console.error(e);
      }
  };

  const mealTypeOptions = [
      { label: t('meals.breakfast'), value: MealType.BREAKFAST },
      { label: t('meals.lunch'), value: MealType.LUNCH },
      { label: t('meals.snack'), value: MealType.SNACK },
      { label: t('meals.dinner'), value: MealType.DINNER },
  ];

  return (
    <View className="flex-1 bg-gray-50 dark:bg-slate-900">
      <Stack.Screen options={{ title: t('manualEntry.title'), headerBackTitle: t('settings.cancel') }} />
      <KeyboardAvoidingView 
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        className="flex-1"
        keyboardVerticalOffset={Platform.OS === 'ios' ? 100 : 0}
      >

          <View className="flex-1">
              <ScrollView 
                contentContainerStyle={{ padding: 20 }} 
                keyboardDismissMode="on-drag" 
                keyboardShouldPersistTaps="handled" 
                showsVerticalScrollIndicator={false}
              >
                
                <View className="bg-white dark:bg-slate-800 rounded-2xl p-4 mb-4 shadow-sm border border-gray-100 dark:border-slate-700">
                    <Text className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">{t('manualEntry.nameLabel')}</Text>
                    <View className="border border-gray-200 dark:border-slate-600 rounded-xl bg-gray-50 dark:bg-slate-900 h-14 justify-center px-4">
                        <TextInput
                            className="text-gray-900 dark:text-white w-full"
                            style={{ fontSize: 18, paddingVertical: 0, includeFontPadding: false }} 
                            placeholder={t('manualEntry.namePlaceholder')}
                            value={name}
                            onChangeText={setName}
                            placeholderTextColor={colorScheme === 'dark' ? '#6B7280' : '#9CA3AF'}
                        />
                    </View>
                </View>

                <View className="bg-white dark:bg-slate-800 rounded-2xl p-4 mb-4 shadow-sm border border-gray-100 dark:border-slate-700">
                    <Text className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">{t('manualEntry.nutritionLabel')}</Text>
                    
                    <View className="flex-row gap-3 mb-3">
                        <View className="flex-1">
                            <Text className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('manualEntry.calories')}</Text>
                            <View className="border border-gray-200 dark:border-slate-600 rounded-xl bg-gray-50 dark:bg-slate-900 h-12 justify-center px-3">
                                <TextInput 
                                    className="text-gray-900 dark:text-white w-full" 
                                    style={{ fontSize: 16, textAlignVertical: 'center', paddingVertical: 0, includeFontPadding: false }}
                                    value={calories} 
                                    onChangeText={setCalories} 
                                    keyboardType="numeric" 
                                    placeholder="0" 
                                    placeholderTextColor="#9CA3AF" 
                                />
                            </View>
                        </View>
                        <View className="flex-1">
                            <Text className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('manualEntry.protein')}</Text>
                            <View className="border border-gray-200 dark:border-slate-600 rounded-xl bg-gray-50 dark:bg-slate-900 h-12 justify-center px-3">
                                <TextInput 
                                    className="text-base text-gray-900 dark:text-white flex-1" 
                                    style={{ textAlignVertical: 'center', paddingVertical: 0, includeFontPadding: false }}
                                    value={protein} 
                                    onChangeText={setProtein} 
                                    keyboardType="numeric" 
                                    placeholder="0" 
                                    placeholderTextColor="#9CA3AF" 
                                />
                            </View>
                        </View>
                    </View>
                     <View className="flex-row gap-3">
                        <View className="flex-1">
                            <Text className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('manualEntry.fat')}</Text>
                            <View className="border border-gray-200 dark:border-slate-600 rounded-xl bg-gray-50 dark:bg-slate-900 h-12 justify-center px-3">
                                <TextInput 
                                    className="text-base text-gray-900 dark:text-white flex-1" 
                                    style={{ textAlignVertical: 'center', paddingVertical: 0, includeFontPadding: false }}
                                    value={fat} 
                                    onChangeText={setFat} 
                                    keyboardType="numeric" 
                                    placeholder="0" 
                                    placeholderTextColor="#9CA3AF" 
                                />
                            </View>
                        </View>
                        <View className="flex-1">
                            <Text className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('manualEntry.carbs')}</Text>
                            <View className="border border-gray-200 dark:border-slate-600 rounded-xl bg-gray-50 dark:bg-slate-900 h-12 justify-center px-3">
                                <TextInput 
                                    className="text-base text-gray-900 dark:text-white flex-1" 
                                    style={{ textAlignVertical: 'center', paddingVertical: 0, includeFontPadding: false }}
                                    value={carbs} 
                                    onChangeText={setCarbs} 
                                    keyboardType="numeric" 
                                    placeholder="0" 
                                    placeholderTextColor="#9CA3AF" 
                                />
                            </View>
                        </View>
                    </View>
                </View>

                <View className="bg-white dark:bg-slate-800 rounded-2xl p-4 mb-4 shadow-sm border border-gray-100 dark:border-slate-700">
                    <Text className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">{t('manualEntry.portionLabel')}</Text>
                    <View className="flex-row items-baseline">
                        <TextInput
                            className="flex-1 text-2xl font-bold text-gray-900 dark:text-white p-2 border-b border-gray-200 dark:border-slate-600"
                            value={weight}
                            onChangeText={setWeight}
                            keyboardType="numeric"
                        />
                        <Text className="text-lg text-gray-500 ml-2">g</Text>
                    </View>
                </View>

                <View className="bg-white dark:bg-slate-800 rounded-2xl p-4 mb-4 shadow-sm border border-gray-100 dark:border-slate-700">
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

              </ScrollView>
              
              <View className="bg-white dark:bg-slate-800 border-t border-gray-200 dark:border-slate-700">
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
                              <Text className="text-white text-lg font-bold">{t('manualEntry.save')}</Text>
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
