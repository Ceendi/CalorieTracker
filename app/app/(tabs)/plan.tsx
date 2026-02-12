import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  Alert,
  TextInput,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { format, addDays } from 'date-fns';

import { useMealPlans, useMealPlanGeneration, useDeleteMealPlan } from '@/hooks/useMealPlan';
import { useLanguage } from '@/hooks/useLanguage';
import { useColorScheme } from '@/hooks/useColorScheme';
import { Colors } from '@/constants/theme';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { MealPlanSummary, GeneratePlanRequest } from '@/schemas/meal-plan';

// Diet options for the form
const DIET_OPTIONS = [
  { value: '', label: 'none' },
  { value: 'vegetarian', label: 'vegetarian' },
  { value: 'vegan', label: 'vegan' },
  { value: 'keto', label: 'keto' },
  { value: 'mediterranean', label: 'mediterranean' },
  { value: 'low_gi', label: 'low_gi' },
];

// Common allergens
const ALLERGY_OPTIONS = [
  'gluten',
  'dairy',
  'eggs',
  'nuts',
  'soy',
  'shellfish',
  'fish',
];

export default function PlanScreen() {
  const router = useRouter();
  const { t } = useLanguage();
  const { colorScheme } = useColorScheme();

  // Data fetching
  const { data: plansData, isLoading, refetch } = useMealPlans();
  const deleteMutation = useDeleteMealPlan();
  const {
    generate,
    progress,
    reset,
    isGenerating,
    isCompleted,
    isError,
    isStarting,
  } = useMealPlanGeneration();

  // UI State
  const [showGenerateForm, setShowGenerateForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    days: '7',
    diet: '',
    allergies: [] as string[],
  });

  const plans = plansData?.plans ?? [];

  const handleGeneratePlan = useCallback(() => {
    const startDate = format(new Date(), 'yyyy-MM-dd');
    const daysCount = parseInt(formData.days) || 7;

    const request: GeneratePlanRequest = {
      name: formData.name || undefined,
      start_date: startDate,
      days: daysCount,
      preferences: {
        diet: formData.diet || undefined,
        allergies: formData.allergies,
        cuisine_preferences: ['polish'],
        excluded_ingredients: [],
      },
    };

    generate(request);
    setShowGenerateForm(false);
  }, [formData, generate]);

  const handleDeletePlan = useCallback((planId: string) => {
    Alert.alert(
      t('mealPlan.deleteConfirmTitle'),
      t('mealPlan.deleteConfirmMessage'),
      [
        { text: t('profile.cancel'), style: 'cancel' },
        {
          text: t('dashboard.delete'),
          style: 'destructive',
          onPress: () => deleteMutation.mutate(planId),
        },
      ]
    );
  }, [t, deleteMutation]);

  const handleViewPlan = useCallback((planId: string) => {
    router.push({
      pathname: '/plan-details' as any,
      params: { planId },
    });
  }, [router]);

  const toggleAllergy = (allergy: string) => {
    setFormData(prev => ({
      ...prev,
      allergies: prev.allergies.includes(allergy)
        ? prev.allergies.filter(a => a !== allergy)
        : [...prev.allergies, allergy],
    }));
  };

  const resetForm = () => {
    setFormData({
      name: '',
      days: '7',
      diet: '',
      allergies: [],
    });
    reset();
  };

  // Navigate to newly created plan
  React.useEffect(() => {
    if (isCompleted && progress.planId) {
      setTimeout(() => {
        reset();
        handleViewPlan(progress.planId!);
      }, 1500);
    }
  }, [isCompleted, progress.planId, handleViewPlan, reset]);

  const renderPlanCard = (plan: MealPlanSummary) => {
    const startDate = new Date(plan.start_date);
    const endDate = new Date(plan.end_date);

    return (
      <TouchableOpacity
        key={plan.id}
        onPress={() => handleViewPlan(plan.id)}
        className="bg-card rounded-2xl p-4 mb-3 border border-border"
      >
        <View className="flex-row justify-between items-start mb-2">
          <View className="flex-1">
            <Text className="text-foreground font-bold text-base" numberOfLines={1}>
              {plan.name || t('mealPlan.untitledPlan')}
            </Text>
            <Text className="text-muted-foreground text-sm mt-1">
              {format(startDate, 'dd.MM')} - {format(endDate, 'dd.MM.yyyy')}
            </Text>
          </View>
          <View className="flex-row items-center gap-2">
            <View className={`px-2 py-1 rounded-full ${
              plan.status === 'active' ? 'bg-green-100 dark:bg-green-900' :
              plan.status === 'draft' ? 'bg-yellow-100 dark:bg-yellow-900' :
              'bg-muted'
            }`}>
              <Text className={`text-xs font-medium ${
                plan.status === 'active' ? 'text-green-700 dark:text-green-300' :
                plan.status === 'draft' ? 'text-yellow-700 dark:text-yellow-300' :
                'text-muted-foreground'
              }`}>
                {t(`mealPlan.status.${plan.status}`)}
              </Text>
            </View>
            <TouchableOpacity
              onPress={() => handleDeletePlan(plan.id)}
              className="p-2"
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
            >
              <IconSymbol name="trash" size={18} color={Colors[colorScheme ?? 'light'].mutedForeground} />
            </TouchableOpacity>
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  const renderGenerationProgress = () => {
    if (!isGenerating && !isCompleted && !isError) return null;

    return (
      <View className="bg-card rounded-2xl p-5 mb-4 border border-border">
        <View className="flex-row items-center gap-3 mb-3">
          {isGenerating && (
            <ActivityIndicator size="small" color={Colors[colorScheme ?? 'light'].tint} />
          )}
          {isCompleted && (
            <IconSymbol name="checkmark.circle.fill" size={24} color="#22C55E" />
          )}
          {isError && (
            <IconSymbol name="xmark.circle.fill" size={24} color="#EF4444" />
          )}
          <Text className="text-foreground font-semibold text-base flex-1">
            {isCompleted ? t('mealPlan.generationComplete') :
             isError ? t('mealPlan.generationError') :
             t('mealPlan.generating')}
          </Text>
        </View>

        {isGenerating && (
          <>
            <View className="h-2 bg-muted rounded-full overflow-hidden mb-2">
              <View
                className="h-full bg-primary rounded-full"
                style={{ width: `${progress.progress}%` }}
              />
            </View>
            <Text className="text-muted-foreground text-sm">
              {progress.message || `${progress.progress}%`}
              {progress.day && ` - ${t('mealPlan.day')} ${progress.day}`}
            </Text>
          </>
        )}

        {isError && progress.error && (
          <Text className="text-destructive text-sm">{progress.error}</Text>
        )}

        {(isCompleted || isError) && (
          <TouchableOpacity
            onPress={resetForm}
            className="mt-3 py-2 px-4 bg-muted rounded-lg self-start"
          >
            <Text className="text-foreground font-medium">{t('mealPlan.close')}</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  };

  const renderEmptyState = () => (
    <View testID="plan-empty-state" className="items-center py-16 px-6">
      <View className="w-20 h-20 bg-muted rounded-full items-center justify-center mb-4">
        <IconSymbol name="calendar" size={40} color={Colors[colorScheme ?? 'light'].mutedForeground} />
      </View>
      <Text className="text-foreground font-bold text-xl mb-2 text-center">
        {t('mealPlan.emptyTitle')}
      </Text>
      <Text className="text-muted-foreground text-center mb-6">
        {t('mealPlan.emptyDescription')}
      </Text>
      <TouchableOpacity
        onPress={() => setShowGenerateForm(true)}
        className="bg-primary px-6 py-3 rounded-full"
      >
        <Text className="text-primary-foreground font-semibold">
          {t('mealPlan.generateFirst')}
        </Text>
      </TouchableOpacity>
    </View>
  );

  const renderGenerateForm = () => (
    <Modal
      visible={showGenerateForm}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={() => setShowGenerateForm(false)}
    >
      <SafeAreaView className="flex-1 bg-background">
        <View className="flex-row justify-between items-center px-5 py-4 border-b border-border">
          <TouchableOpacity onPress={() => setShowGenerateForm(false)}>
            <Text className="text-muted-foreground font-medium text-lg">
              {t('profile.cancel')}
            </Text>
          </TouchableOpacity>
          <Text className="text-foreground font-bold text-lg">
            {t('mealPlan.newPlan')}
          </Text>
          <TouchableOpacity onPress={handleGeneratePlan} disabled={isStarting}>
            <Text className={`font-bold text-lg ${isStarting ? 'text-muted-foreground' : 'text-primary'}`}>
              {t('mealPlan.generate')}
            </Text>
          </TouchableOpacity>
        </View>

        <ScrollView className="flex-1 px-5 py-4">
          {/* Plan Name */}
          <View className="mb-5">
            <Text className="text-foreground font-semibold mb-2">
              {t('mealPlan.planName')}
            </Text>
            <TextInput
              className="bg-card border border-border rounded-xl px-4 py-3 text-foreground"
              placeholder={t('mealPlan.planNamePlaceholder')}
              placeholderTextColor={Colors[colorScheme ?? 'light'].placeholder}
              value={formData.name}
              onChangeText={(text) => setFormData(prev => ({ ...prev, name: text }))}
            />
          </View>

          {/* Number of Days */}
          <View className="mb-5">
            <Text className="text-foreground font-semibold mb-2">
              {t('mealPlan.numberOfDays')}
            </Text>
            <View className="flex-row gap-2">
              {['3', '5', '7', '14'].map(days => (
                <TouchableOpacity
                  key={days}
                  onPress={() => setFormData(prev => ({ ...prev, days }))}
                  className={`flex-1 py-3 rounded-xl border ${
                    formData.days === days
                      ? 'bg-primary border-primary'
                      : 'bg-card border-border'
                  }`}
                >
                  <Text className={`text-center font-semibold ${
                    formData.days === days ? 'text-primary-foreground' : 'text-foreground'
                  }`}>
                    {days}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Diet Type */}
          <View className="mb-5">
            <Text className="text-foreground font-semibold mb-2">
              {t('mealPlan.dietType')}
            </Text>
            <View className="flex-row flex-wrap gap-2">
              {DIET_OPTIONS.map(option => (
                <TouchableOpacity
                  key={option.value}
                  onPress={() => setFormData(prev => ({ ...prev, diet: option.value }))}
                  className={`px-4 py-2 rounded-full border ${
                    formData.diet === option.value
                      ? 'bg-primary border-primary'
                      : 'bg-card border-border'
                  }`}
                >
                  <Text className={`font-medium ${
                    formData.diet === option.value ? 'text-primary-foreground' : 'text-foreground'
                  }`}>
                    {t(`mealPlan.diets.${option.label}`)}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Allergies */}
          <View className="mb-5">
            <Text className="text-foreground font-semibold mb-2">
              {t('mealPlan.allergies')}
            </Text>
            <View className="flex-row flex-wrap gap-2">
              {ALLERGY_OPTIONS.map(allergy => (
                <TouchableOpacity
                  key={allergy}
                  onPress={() => toggleAllergy(allergy)}
                  className={`px-4 py-2 rounded-full border ${
                    formData.allergies.includes(allergy)
                      ? 'bg-destructive border-destructive'
                      : 'bg-card border-border'
                  }`}
                >
                  <Text className={`font-medium ${
                    formData.allergies.includes(allergy) ? 'text-destructive-foreground' : 'text-foreground'
                  }`}>
                    {t(`mealPlan.allergens.${allergy}`)}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );

  return (
    <SafeAreaView className="flex-1 bg-background" edges={['top']} testID="plan-screen">
      <ScrollView
        contentContainerStyle={{ padding: 20, paddingBottom: 100 }}
        refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} />}
      >
        {/* Header */}
        <View className="flex-row justify-between items-center mb-6">
          <View>
            <Text className="text-2xl font-bold text-foreground">
              {t('mealPlan.title')}
            </Text>
            <Text className="text-muted-foreground text-sm mt-1">
              {t('mealPlan.subtitle')}
            </Text>
          </View>
          {plans.length > 0 && !isGenerating && (
            <TouchableOpacity
              onPress={() => setShowGenerateForm(true)}
              className="bg-primary p-3 rounded-full"
            >
              <IconSymbol name="plus" size={24} color="#FFFFFF" />
            </TouchableOpacity>
          )}
        </View>

        {/* Generation Progress */}
        {renderGenerationProgress()}

        {/* Content */}
        {isLoading && plans.length === 0 ? (
          <View className="items-center py-16">
            <ActivityIndicator size="large" color={Colors[colorScheme ?? 'light'].tint} />
          </View>
        ) : plans.length === 0 && !isGenerating ? (
          renderEmptyState()
        ) : (
          <View>
            {plans.map(renderPlanCard)}
          </View>
        )}
      </ScrollView>

      {renderGenerateForm()}
    </SafeAreaView>
  );
}
