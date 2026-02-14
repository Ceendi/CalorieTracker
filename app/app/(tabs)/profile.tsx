import React, { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { View, Text, TouchableOpacity, ScrollView, Alert, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '@/hooks/useAuth';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { useColorScheme } from '@/hooks/useColorScheme';
import { apiClient } from '@/services/api.client';
import { InfoItem } from '@/components/profile/InfoItem';
import { SelectionModal } from '@/components/profile/SelectionModal';
import { SettingsModal } from '@/components/profile/SettingsModal';
import { GOAL_OPTIONS, ACTIVITY_OPTIONS, GENDER_OPTIONS } from '@/constants/options';
import { useLanguage } from '@/hooks/useLanguage';
import { Colors } from '@/constants/theme';
import { calculateDailyGoal } from '@/utils/calculations';
import { useDailyTargets, mealPlanKeys } from '@/hooks/useMealPlan';
import { User } from '@/utils/validators';
import { userService } from '@/services/user.service';
import { UserProfileSchema } from '@/schemas/user';

export default function ProfileScreen() {
  const queryClient = useQueryClient();
  const { user, signOut, refreshUser } = useAuth();
  const { colorScheme, toggleColorScheme } = useColorScheme();
  const { t } = useLanguage();
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const [formData, setFormData] = useState({
    height: user?.height?.toString() || '',
    weight: user?.weight?.toString() || '',
    age: user?.age?.toString() || '',
    goal: user?.goal || '',
    activity_level: user?.activity_level || '',
    gender: (user?.gender || 'male').toLowerCase(),
  });

  const [modalVisible, setModalVisible] = useState(false);
  const [settingsVisible, setSettingsVisible] = useState(false);
  const [activeSelectField, setActiveSelectField] = useState<'goal' | 'activity_level' | 'gender' | null>(null);

  // Fetch daily targets from backend
  const { data: backendTargets, isLoading: isLoadingTargets } = useDailyTargets();

  // Use backend targets if available, otherwise fall back to local calculation
  const currentCalories = React.useMemo(() => {
    // If we have backend targets, use them (convert kcal to calories for consistency)
    if (backendTargets) {
      return {
        calories: backendTargets.kcal,
        protein: Math.round(backendTargets.protein),
        fat: Math.round(backendTargets.fat),
        carbs: Math.round(backendTargets.carbs),
      };
    }

    // Fallback to local calculation
    const profile: Partial<User> = {
        weight: parseFloat(formData.weight) || 0,
        height: parseFloat(formData.height) || 0,
        age: parseInt(formData.age) || 0,
        gender: formData.gender,
        activity_level: formData.activity_level,
        goal: formData.goal
    };
    return calculateDailyGoal(profile);
  }, [backendTargets, formData]);



  const handleSave = async () => {
    const rawData = {
        height: formData.height ? parseFloat(formData.height) : null,
        weight: formData.weight ? parseFloat(formData.weight) : null,
        age: formData.age ? parseInt(formData.age) : null,
        goal: formData.goal,
        activity_level: formData.activity_level,
        gender: formData.gender,
    };

    const validationResult = UserProfileSchema.safeParse(rawData);

    if (!validationResult.success) {
      // Find the first error for user display
      const firstError = validationResult.error.issues[0];
      const field = firstError.path[0];
      
      // Map field errors to translation keys
      if (field === 'height') {
        Alert.alert(t('profile.error'), t('profile.validation.height'));
      } else if (field === 'weight') {
        Alert.alert(t('profile.error'), t('profile.validation.weight'));
      } else if (field === 'age') {
        Alert.alert(t('profile.error'), t('profile.validation.age'));
      } else {
        Alert.alert(t('profile.error'), firstError.message);
      }
      return;
    }

    try {
      setIsLoading(true);
      await userService.updateProfile(validationResult.data);
      await refreshUser();
      
      await queryClient.invalidateQueries({ queryKey: mealPlanKeys.dailyTargets() });
      
      setIsEditing(false);
      Alert.alert(t('profile.success'), t('profile.profileUpdated'));
    } catch (error) {
      Alert.alert(t('profile.error'), t('profile.updateFailed'));
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const translatedGoalOptions = GOAL_OPTIONS.map(opt => ({
      ...opt,
      label: t(`options.goals.${opt.value}`)
  }));

  const translatedActivityOptions = ACTIVITY_OPTIONS.map(opt => ({
      ...opt,
      label: t(`options.activities.${opt.value}`)
  }));

  const translatedGenderOptions = GENDER_OPTIONS.map(opt => ({
      ...opt,
      label: t(`options.genders.${opt.value}`)
  }));

  const toggleEdit = () => {
    if (isEditing) {
      setFormData({
        height: user?.height?.toString() || '',
        weight: user?.weight?.toString() || '',
        age: user?.age?.toString() || '',
        goal: user?.goal || '',
        activity_level: user?.activity_level || '',
        gender: user?.gender || 'male',
      });
      setIsEditing(false);
    } else {
      setIsEditing(true);
    }
  };

  const openSelection = (field: 'goal' | 'activity_level' | 'gender') => {
    setActiveSelectField(field);
    setModalVisible(true);
  };

  const selectOption = (value: string) => {
    if (activeSelectField) {
      setFormData(prev => ({ ...prev, [activeSelectField]: value }));
    }
    setModalVisible(false);
  };

  return (
    <SafeAreaView className="flex-1 bg-background" testID="profile-screen">
      <ScrollView contentContainerStyle={{ padding: 20, paddingBottom: 120 }}>
        
        <View className="flex-row justify-between items-center mb-6 h-12">
           <View className="min-w-[60px] items-start justify-center">
             {isEditing && (
               <TouchableOpacity testID="profile-cancel-button" onPress={() => setIsEditing(false)} className="py-2">
                 <Text className="text-muted-foreground font-medium text-lg">{t('profile.cancel')}</Text>
               </TouchableOpacity>
             )}
           </View>
           
           <View className="min-w-[60px] items-end justify-center">
             {isEditing ? (
               <TouchableOpacity testID="profile-done-button" onPress={handleSave} disabled={isLoading} className="py-2">
                  <Text className="text-primary font-bold text-lg">{t('profile.done')}</Text>
               </TouchableOpacity>
             ) : (
               <TouchableOpacity testID="settings-gear" onPress={() => setSettingsVisible(true)} className="p-2 bg-card rounded-full border border-border shadow-sm">
                 <IconSymbol name="gear" size={24} color={Colors[colorScheme ?? 'light'].tint} />
               </TouchableOpacity>
             )}
           </View>
        </View>

        <View className="items-center mb-8 -mt-6">
          <View className="w-24 h-24 bg-muted rounded-full items-center justify-center mb-4 shadow-sm">
            <Text className="text-3xl font-bold text-foreground opacity-60">
              {user?.email?.charAt(0).toUpperCase()}
            </Text>
          </View>
          <Text className="text-2xl font-bold text-foreground mb-1">
            {user?.email?.split('@')[0]}
          </Text>
          <Text className="text-muted-foreground mb-3">{user?.email}</Text>
          
          <TouchableOpacity
            testID="profile-edit-button"
            onPress={toggleEdit}
            disabled={isEditing}
            className={`bg-card px-6 py-2.5 rounded-full border border-border shadow-sm active:bg-muted ${isEditing ? 'opacity-0' : 'opacity-100'}`}
          >
              <Text className="text-foreground font-semibold text-sm">{t('profile.editProfile')}</Text>
          </TouchableOpacity>
        </View>

        <Text className="text-lg font-bold text-foreground mb-4">{t('profile.yourStats')}</Text>
        
        <InfoItem 
          label={t('profile.height')}
          value={formData.height} 
          fieldKey="height" 
          icon="ruler" 
          isNumber 
          isEditing={isEditing} 
          onChangeText={(t) => setFormData({...formData, height: t})} 
        />
        <InfoItem 
          label={t('profile.weight')}
          value={formData.weight} 
          fieldKey="weight" 
          icon="scalemass" 
          isNumber 
          isEditing={isEditing} 
          onChangeText={(t) => setFormData({...formData, weight: t})} 
        />
        <InfoItem 
          label={t('profile.age')}
          value={formData.age} 
          fieldKey="age" 
          icon="calendar" 
          isNumber 
          isEditing={isEditing} 
          onChangeText={(t) => setFormData({...formData, age: t})} 
        />

        <InfoItem 
          label={t('options.gender')}
          value={formData.gender} 
          fieldKey="gender" 
          icon="person.fill" 
          isSelect 
          selectOptions={translatedGenderOptions}
          isEditing={isEditing} 
          onOpenSelection={() => openSelection('gender')}
        />
        
        <InfoItem 
          label={t('profile.goal')}
          value={formData.goal} 
          fieldKey="goal" 
          icon="target" 
          isSelect 
          selectOptions={translatedGoalOptions}
          isEditing={isEditing} 
          onOpenSelection={() => openSelection('goal')}
        />
        <InfoItem 
          label={t('profile.activity')}
          value={formData.activity_level} 
          fieldKey="activity_level" 
          icon="figure.run" 
          isSelect 
          selectOptions={translatedActivityOptions}
          isEditing={isEditing} 
          onOpenSelection={() => openSelection('activity_level')}
        />

        <View className="p-4 bg-card rounded-2xl mb-3 border border-border">
             <View className="flex-row items-center justify-between mb-3">
                 <View className="flex-row items-center gap-3">
                    <View className="p-2 bg-primary/10 rounded-full">
                        <IconSymbol name="flame.fill" size={20} color={Colors[colorScheme ?? 'light'].tint} />
                    </View>
                    <View>
                        <Text className="text-foreground font-bold text-base">{t('dashboard.goal')}</Text>
                        <Text className="text-xs text-muted-foreground">{t('profile.recommended')}</Text>
                    </View>
                 </View>
                 {isLoadingTargets ? (
                    <ActivityIndicator size="small" color={Colors[colorScheme ?? 'light'].tint} />
                 ) : (
                    <Text className="text-2xl font-bold text-primary">
                       {currentCalories.calories} kcal
                    </Text>
                 )}
             </View>

             <View className="flex-row justify-between pt-3 border-t border-border">
                <View className="items-center flex-1">
                    <Text className="text-xs text-muted-foreground mb-0.5">{t('manualEntry.protein')}</Text>
                    {isLoadingTargets ? (
                       <Text className="text-sm font-bold text-foreground">...</Text>
                    ) : (
                       <Text className="text-sm font-bold text-foreground">{currentCalories.protein}g</Text>
                    )}
                </View>
                <View className="w-px h-8 bg-border" />
                <View className="items-center flex-1">
                    <Text className="text-xs text-muted-foreground mb-0.5">{t('manualEntry.fat')}</Text>
                    {isLoadingTargets ? (
                       <Text className="text-sm font-bold text-foreground">...</Text>
                    ) : (
                       <Text className="text-sm font-bold text-foreground">{currentCalories.fat}g</Text>
                    )}
                </View>
                <View className="w-px h-8 bg-border" />
                <View className="items-center flex-1">
                    <Text className="text-xs text-muted-foreground mb-0.5">{t('manualEntry.carbs')}</Text>
                    {isLoadingTargets ? (
                       <Text className="text-sm font-bold text-foreground">...</Text>
                    ) : (
                       <Text className="text-sm font-bold text-foreground">{currentCalories.carbs}g</Text>
                    )}
                </View>
             </View>
        </View>
        
        <SelectionModal 
            visible={modalVisible}
            title={`${t('options.select')} ${activeSelectField === 'goal' ? t('options.goal') : activeSelectField === 'gender' ? t('options.gender') : t('options.activity')}`}
            options={activeSelectField === 'goal' ? translatedGoalOptions : activeSelectField === 'gender' ? translatedGenderOptions : translatedActivityOptions}
            selectedValue={activeSelectField ? formData[activeSelectField] : ''}
            onSelect={selectOption}
            onClose={() => setModalVisible(false)}
        />

        <Text className="text-center text-muted-foreground mt-8 text-sm">
          {t('profile.version')} 1.0.0
        </Text>

        <SettingsModal 
          visible={settingsVisible}
          onClose={() => setSettingsVisible(false)}
        />
      </ScrollView>
    </SafeAreaView>
  );
}
