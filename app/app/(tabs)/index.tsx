import React, { useState, useCallback } from 'react';
import { View, Text, ScrollView, RefreshControl, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { useFocusEffect, useRouter } from 'expo-router';
import { format } from 'date-fns';

import { useAuth } from '@/hooks/useAuth';
import { useDiary } from '@/hooks/useDiary';
import { calculateDailyGoal } from '@/utils/calculations';
import { useLanguage } from '@/hooks/useLanguage';
import { DateStrip } from '@/components/diary/DateStrip';
import { NutrientRing } from '@/components/diary/NutrientRing';
import { MealSection } from '@/components/diary/MealSection';
import { MealType, MealEntry } from '@/types/food';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { ArcProgress } from '@/components/ui/ArcProgress';
import { GaugeProgress } from '@/components/ui/GaugeProgress';

export default function HomeScreen() {
  const { user } = useAuth();
  const userName = user?.email?.split('@')[0] || 'User';
  const router = useRouter();
  const { t } = useLanguage();

  const [date, setDate] = useState(new Date());
  const formattedDate = format(date, 'yyyy-MM-dd');
  
  const { data: dailyLog, isLoading, refetch, deleteEntry } = useDiary(formattedDate);

  useFocusEffect(
    useCallback(() => {
        refetch();
    }, [refetch])
  );

  const calculatedGoal = user ? calculateDailyGoal(user) : { calories: 2000, protein: 160, fat: 70, carbs: 250 };
  const dailyGoal = calculatedGoal.calories;
  const consumed = dailyLog?.total_kcal || 0;
  const remaining = dailyGoal - consumed;
  const isOverGoal = consumed > dailyGoal;
  const progress = Math.min(consumed / dailyGoal, 1);
  const percentage = Math.round((consumed / dailyGoal) * 100);

  const handleAddMeal = (type: MealType) => {
      router.push('/(tabs)/add');
  };

  const handleEditEntry = (entry: MealEntry) => {
       router.push({
           pathname: '/food-details',
           params: {
               entryId: entry.id,
               item: JSON.stringify(entry.product),
               initialAmount: entry.amount_grams.toString(),
               initialMealType: entry.meal_type,
               date: formattedDate,
               initialUnitLabel: entry.unit_label,
               initialUnitGrams: entry.unit_grams?.toString(),
               initialUnitQuantity: entry.unit_quantity?.toString()
           }
       });
  };

  const entriesByType = (type: MealType) => {
      return dailyLog?.entries.filter(e => e.meal_type === type) || [];
  };

  const mealTypes = [MealType.BREAKFAST, MealType.LUNCH, MealType.DINNER, MealType.SNACK];

  return (
    <SafeAreaView className="flex-1 bg-gray-50 dark:bg-slate-900" edges={['top']}>
      <ScrollView 
        contentContainerStyle={{ padding: 20, paddingBottom: 100 }}
        refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} />}
      >
        
        <View className="flex-row justify-between items-center mb-2">
          <View>
            <Text className="text-gray-500 dark:text-gray-400 text-sm font-medium">{t('dashboard.welcome')}</Text>
            <Text className="text-2xl font-bold text-gray-900 dark:text-white capitalize">{userName}</Text>
          </View>
        </View>


        <DateStrip selectedDate={date} onSelectDate={setDate} />

        <LinearGradient
          colors={['#4F46E5', '#4338CA']}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          className="rounded-[32px] p-5 mb-5 shadow-md"
        >
            <View className="flex-row justify-between items-center mb-4">
                 <Text className="text-indigo-100 font-semibold text-base">{t('dashboard.caloriesResult')}</Text>
                 <IconSymbol name="flame.fill" size={20} color="#E0E7FF" />
            </View>

            <View className="items-center mb-4">
                <GaugeProgress 
                    size={180} 
                    strokeWidth={18} 
                    progress={progress} 
                    color={isOverGoal ? '#EF4444' : 'white'} 
                    trackColor="rgba(255,255,255,0.15)"
                >
                    <View className="items-center justify-center">
                        <Text className={`text-4xl font-black tracking-tight leading-tight ${isOverGoal ? 'text-red-300' : 'text-white'}`}>
                            {isOverGoal ? `${Math.abs(Math.round(remaining))}` : Math.round(remaining)}
                        </Text>
                        <Text className={`text-xs font-medium uppercase tracking-widest mt-1 ${isOverGoal ? 'text-red-200' : 'text-indigo-200'}`}>
                            {isOverGoal ? t('dashboard.over') : t('dashboard.remaining')}
                        </Text>
                    </View>
                </GaugeProgress>
            </View>

            <View className="flex-row justify-around px-4 bg-indigo-950/20 rounded-2xl py-3 mx-2 border border-indigo-400/10 mb-1">
                 <View className="items-center">
                     <Text className="text-indigo-200 text-[10px] font-bold uppercase tracking-wider mb-0.5">{t('dashboard.eaten')}</Text>
                     <Text className="text-lg font-black text-white">{Math.round(consumed)}</Text>
                 </View>
                 <View className="w-[1px] bg-indigo-400/30 h-10" />
                 <View className="items-center">
                     <Text className="text-indigo-200 text-[10px] font-bold uppercase tracking-wider mb-0.5">{t('dashboard.goal')}</Text>
                     <Text className="text-lg font-black text-white">{dailyGoal}</Text>
                 </View>
            </View>
        </LinearGradient>

        <View className="flex-row justify-between mb-4 px-1">
            <NutrientRing 
                label={t('manualEntry.protein')} 
                current={dailyLog?.total_protein || 0} 
                total={calculatedGoal.protein} 
                unit="g" 
                color="#8B5CF6" 
                bgColor="#F3E8FF"
            />
            <NutrientRing 
                 label={t('manualEntry.carbs')} 
                 current={dailyLog?.total_carbs || 0} 
                 total={calculatedGoal.carbs} 
                 unit="g" 
                 color="#3B82F6" 
                 bgColor="#DBEAFE"
            />
            <NutrientRing 
                 label={t('manualEntry.fat')} 
                 current={dailyLog?.total_fat || 0} 
                 total={calculatedGoal.fat} 
                 unit="g" 
                 color="#F97316" 
                 bgColor="#FFEDD5"
            />
        </View>

        {isLoading && !dailyLog ? (
            <ActivityIndicator size="large" color="#4F46E5" />
        ) : (
            <>
                {mealTypes.map(type => (
                    <MealSection
                        key={type}
                        type={type}
                        entries={entriesByType(type)}
                        onAdd={handleAddMeal}
                        onDeleteEntry={deleteEntry}
                        onEditEntry={handleEditEntry}
                    />
                ))}
                
                {(!dailyLog?.entries || dailyLog.entries.length === 0) && (
                    <View className="items-center py-10 opacity-50">
                        <IconSymbol name="fork.knife" size={48} color="#9CA3AF" />
                        <Text className="text-gray-500 mt-4 text-center">{t('dashboard.noEntries')}</Text>
                        <Text className="text-gray-400 text-sm text-center">{t('dashboard.addFirst')}</Text>
                    </View>
                )}
            </>
        )}

      </ScrollView>
    </SafeAreaView>
  );
}
