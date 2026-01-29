import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { Stack, useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { format } from 'date-fns';

import { useMealPlan } from '@/hooks/useMealPlan';
import { useLanguage } from '@/hooks/useLanguage';
import { useColorScheme } from '@/hooks/useColorScheme';
import { Colors } from '@/constants/theme';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { Day, Meal, Ingredient } from '@/schemas/meal-plan';

// Meal type icons and colors
const MEAL_TYPE_CONFIG: Record<string, { icon: string; color: string }> = {
  breakfast: { icon: 'sun.horizon.fill', color: '#F59E0B' },
  second_breakfast: { icon: 'cup.and.saucer.fill', color: '#F97316' },
  lunch: { icon: 'fork.knife', color: '#22C55E' },
  snack: { icon: 'carrot.fill', color: '#8B5CF6' },
  dinner: { icon: 'moon.fill', color: '#6366F1' },
};

export default function PlanDetailsScreen() {
  const params = useLocalSearchParams<{ planId: string }>();
  const router = useRouter();
  const { t } = useLanguage();
  const { colorScheme } = useColorScheme();

  const { data: plan, isLoading, error } = useMealPlan(params.planId || null);

  const [expandedDays, setExpandedDays] = useState<Set<string>>(new Set());
  const [expandedMeals, setExpandedMeals] = useState<Set<string>>(new Set());

  const toggleDay = (dayId: string) => {
    setExpandedDays(prev => {
      const newSet = new Set(prev);
      if (newSet.has(dayId)) {
        newSet.delete(dayId);
      } else {
        newSet.add(dayId);
      }
      return newSet;
    });
  };

  const toggleMeal = (mealId: string) => {
    setExpandedMeals(prev => {
      const newSet = new Set(prev);
      if (newSet.has(mealId)) {
        newSet.delete(mealId);
      } else {
        newSet.add(mealId);
      }
      return newSet;
    });
  };

  // Expand all by default on first load
  React.useEffect(() => {
    if (plan && plan.days.length > 0 && expandedDays.size === 0) {
      // Expand first day by default
      setExpandedDays(new Set([plan.days[0].id]));
    }
  }, [plan]);

  const renderIngredient = (ingredient: Ingredient) => (
    <View key={ingredient.id} className="flex-row justify-between py-2 border-b border-border/50">
      <View className="flex-1 pr-4">
        <Text className="text-foreground text-sm">{ingredient.name}</Text>
        <Text className="text-muted-foreground text-xs">
          {Math.round(ingredient.amount_grams)}g
          {ingredient.unit_label && ` (${ingredient.unit_label})`}
        </Text>
      </View>
      <View className="items-end">
        <Text className="text-foreground text-sm font-medium">
          {Math.round(ingredient.kcal ?? 0)} kcal
        </Text>
      </View>
    </View>
  );

  const renderMeal = (meal: Meal) => {
    const isExpanded = expandedMeals.has(meal.id);
    const mealConfig = MEAL_TYPE_CONFIG[meal.meal_type] || MEAL_TYPE_CONFIG.snack;

    return (
      <View key={meal.id} className="bg-card rounded-xl mb-3 border border-border overflow-hidden">
        <TouchableOpacity
          onPress={() => toggleMeal(meal.id)}
          className="p-4"
        >
          <View className="flex-row items-center gap-3">
            <View
              className="w-10 h-10 rounded-full items-center justify-center"
              style={{ backgroundColor: `${mealConfig.color}20` }}
            >
              <IconSymbol name={mealConfig.icon as any} size={20} color={mealConfig.color} />
            </View>
            <View className="flex-1">
              <Text className="text-muted-foreground text-xs uppercase tracking-wider">
                {t(`meals.${meal.meal_type}`)}
              </Text>
              <Text className="text-foreground font-semibold" numberOfLines={1}>
                {meal.name}
              </Text>
            </View>
            <View className="items-end">
              <Text className="text-primary font-bold">
                {Math.round(meal.total_kcal ?? 0)} kcal
              </Text>
              <IconSymbol
                name={isExpanded ? 'chevron.up' : 'chevron.down'}
                size={16}
                color={Colors[colorScheme ?? 'light'].mutedForeground}
              />
            </View>
          </View>
        </TouchableOpacity>

        {isExpanded && (
          <View className="px-4 pb-4 border-t border-border">
            {/* Macros */}
            <View className="flex-row justify-around py-3 mb-3 bg-muted/50 rounded-lg mt-3">
              <View className="items-center">
                <Text className="text-xs text-muted-foreground">P</Text>
                <Text className="text-sm font-semibold text-foreground">
                  {Math.round(meal.total_protein ?? 0)}g
                </Text>
              </View>
              <View className="items-center">
                <Text className="text-xs text-muted-foreground">F</Text>
                <Text className="text-sm font-semibold text-foreground">
                  {Math.round(meal.total_fat ?? 0)}g
                </Text>
              </View>
              <View className="items-center">
                <Text className="text-xs text-muted-foreground">C</Text>
                <Text className="text-sm font-semibold text-foreground">
                  {Math.round(meal.total_carbs ?? 0)}g
                </Text>
              </View>
            </View>

            {/* Preparation time */}
            {meal.preparation_time_minutes && (
              <View className="flex-row items-center gap-2 mb-3">
                <IconSymbol name="clock" size={14} color={Colors[colorScheme ?? 'light'].mutedForeground} />
                <Text className="text-muted-foreground text-sm">
                  {t('mealPlan.details.prepTime')}: {meal.preparation_time_minutes} {t('mealPlan.details.minutes')}
                </Text>
              </View>
            )}

            {/* Ingredients */}
            <Text className="text-foreground font-semibold mb-2">
              {t('mealPlan.details.ingredients')}
            </Text>
            {meal.ingredients.map(renderIngredient)}

            {/* Description / Preparation */}
            {meal.description && (
              <View className="mt-4">
                <Text className="text-foreground font-semibold mb-2">
                  {t('mealPlan.details.preparation')}
                </Text>
                <Text className="text-muted-foreground text-sm leading-5">
                  {meal.description}
                </Text>
              </View>
            )}
          </View>
        )}
      </View>
    );
  };

  const renderDay = (day: Day) => {
    const isExpanded = expandedDays.has(day.id);
    const dayDate = day.date ? new Date(day.date) : null;

    // Calculate day totals
    const dayTotals = day.meals.reduce(
      (acc, meal) => ({
        kcal: acc.kcal + (meal.total_kcal ?? 0),
        protein: acc.protein + (meal.total_protein ?? 0),
        fat: acc.fat + (meal.total_fat ?? 0),
        carbs: acc.carbs + (meal.total_carbs ?? 0),
      }),
      { kcal: 0, protein: 0, fat: 0, carbs: 0 }
    );

    return (
      <View key={day.id} className="mb-4">
        <TouchableOpacity
          onPress={() => toggleDay(day.id)}
          className="flex-row items-center justify-between bg-card rounded-xl p-4 border border-border"
        >
          <View className="flex-row items-center gap-3">
            <View className="w-12 h-12 bg-primary/10 rounded-xl items-center justify-center">
              <Text className="text-primary font-bold text-lg">{day.day_number}</Text>
            </View>
            <View>
              <Text className="text-foreground font-bold text-base">
                {t('mealPlan.day')} {day.day_number}
              </Text>
              {dayDate && (
                <Text className="text-muted-foreground text-sm">
                  {format(dayDate, 'EEEE, d MMM')}
                </Text>
              )}
            </View>
          </View>
          <View className="flex-row items-center gap-3">
            <Text className="text-primary font-bold">
              {Math.round(dayTotals.kcal)} kcal
            </Text>
            <IconSymbol
              name={isExpanded ? 'chevron.up' : 'chevron.down'}
              size={20}
              color={Colors[colorScheme ?? 'light'].mutedForeground}
            />
          </View>
        </TouchableOpacity>

        {isExpanded && (
          <View className="mt-3 ml-2">
            {day.meals.map(renderMeal)}
          </View>
        )}
      </View>
    );
  };

  if (isLoading) {
    return (
      <View className="flex-1 bg-background items-center justify-center">
        <Stack.Screen options={{ title: t('mealPlan.details.title') }} />
        <ActivityIndicator size="large" color={Colors[colorScheme ?? 'light'].tint} />
      </View>
    );
  }

  if (error || !plan) {
    return (
      <View className="flex-1 bg-background items-center justify-center px-6">
        <Stack.Screen options={{ title: t('mealPlan.details.title') }} />
        <IconSymbol name="exclamationmark.triangle" size={48} color={Colors[colorScheme ?? 'light'].muted} />
        <Text className="text-foreground font-bold text-lg mt-4 text-center">
          {t('mealPlan.generationError')}
        </Text>
        <TouchableOpacity
          onPress={() => router.back()}
          className="mt-6 px-6 py-3 bg-primary rounded-full"
        >
          <Text className="text-primary-foreground font-semibold">{t('mealPlan.close')}</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const startDate = new Date(plan.start_date);
  const endDate = new Date(plan.end_date);

  return (
    <View className="flex-1 bg-background">
      <Stack.Screen
        options={{
          title: plan.name || t('mealPlan.details.title'),
          headerBackTitle: t('settings.cancel'),
        }}
      />
      <ScrollView
        contentContainerStyle={{ padding: 20, paddingBottom: 100 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Plan Header */}
        <View className="bg-card rounded-2xl p-5 mb-6 border border-border">
          <Text className="text-foreground font-bold text-xl mb-2">
            {plan.name || t('mealPlan.untitledPlan')}
          </Text>
          <Text className="text-muted-foreground mb-3">
            {format(startDate, 'dd.MM.yyyy')} - {format(endDate, 'dd.MM.yyyy')}
          </Text>

          {/* Daily targets */}
          {plan.daily_targets && (
            <View className="flex-row justify-around py-3 bg-muted/50 rounded-xl">
              <View className="items-center">
                <Text className="text-xs text-muted-foreground mb-1">{t('dashboard.goal')}</Text>
                <Text className="text-lg font-bold text-primary">
                  {plan.daily_targets.kcal ?? plan.daily_targets.calories ?? 0} kcal
                </Text>
              </View>
              <View className="items-center">
                <Text className="text-xs text-muted-foreground mb-1">{t('manualEntry.protein')}</Text>
                <Text className="text-sm font-bold text-foreground">
                  {Math.round(plan.daily_targets.protein ?? 0)}g
                </Text>
              </View>
              <View className="items-center">
                <Text className="text-xs text-muted-foreground mb-1">{t('manualEntry.fat')}</Text>
                <Text className="text-sm font-bold text-foreground">
                  {Math.round(plan.daily_targets.fat ?? 0)}g
                </Text>
              </View>
              <View className="items-center">
                <Text className="text-xs text-muted-foreground mb-1">{t('manualEntry.carbs')}</Text>
                <Text className="text-sm font-bold text-foreground">
                  {Math.round(plan.daily_targets.carbs ?? 0)}g
                </Text>
              </View>
            </View>
          )}
        </View>

        {/* Days */}
        {plan.days.map(renderDay)}
      </ScrollView>
    </View>
  );
}
