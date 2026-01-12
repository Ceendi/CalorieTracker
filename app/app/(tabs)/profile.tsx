import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ScrollView, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '@/hooks/useAuth';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { apiClient } from '@/services/api.client';
import { InfoItem } from '@/components/profile/InfoItem';
import { SelectionModal } from '@/components/profile/SelectionModal';
import { SettingsModal } from '@/components/profile/SettingsModal';
import { GOAL_OPTIONS, ACTIVITY_OPTIONS } from '@/constants/options';
import { useLanguage } from '@/hooks/useLanguage';

export default function ProfileScreen() {
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
  });

  const [modalVisible, setModalVisible] = useState(false);
  const [settingsVisible, setSettingsVisible] = useState(false);
  const [activeSelectField, setActiveSelectField] = useState<'goal' | 'activity_level' | null>(null);



  const handleSave = async () => {
    try {
      setIsLoading(true);
      await apiClient.patch('/users/me', {
        height: formData.height ? parseFloat(formData.height) : null,
        weight: formData.weight ? parseFloat(formData.weight) : null,
        age: formData.age ? parseInt(formData.age) : null,
        goal: formData.goal,
        activity_level: formData.activity_level,
      });
      await refreshUser();
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

  const toggleEdit = () => {
    if (isEditing) {
      setFormData({
        height: user?.height?.toString() || '',
        weight: user?.weight?.toString() || '',
        age: user?.age?.toString() || '',
        goal: user?.goal || '',
        activity_level: user?.activity_level || '',
      });
      setIsEditing(false);
    } else {
      setIsEditing(true);
    }
  };

  const openSelection = (field: 'goal' | 'activity_level') => {
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
    <SafeAreaView className="flex-1 bg-gray-50 dark:bg-slate-900">
      <ScrollView contentContainerStyle={{ padding: 20, paddingBottom: 120 }}>
        
        <View className="flex-row justify-between items-center mb-6 h-12">
           <View className="min-w-[60px] items-start justify-center">
             {isEditing && (
               <TouchableOpacity onPress={() => setIsEditing(false)} className="py-2">
                 <Text className="text-gray-500 font-medium text-lg">{t('profile.cancel')}</Text>
               </TouchableOpacity>
             )}
           </View>
           
           <View className="min-w-[60px] items-end justify-center">
             {isEditing ? (
               <TouchableOpacity onPress={handleSave} disabled={isLoading} className="py-2">
                  <Text className="text-indigo-600 font-bold text-lg">{t('profile.done')}</Text>
               </TouchableOpacity>
             ) : (
               <TouchableOpacity onPress={() => setSettingsVisible(true)} className="p-2 bg-white dark:bg-slate-800 rounded-full border border-gray-200 dark:border-gray-700 shadow-sm">
                 <IconSymbol name="gear" size={24} color={colorScheme === 'dark' ? '#fff' : '#4B5563'} /> 
               </TouchableOpacity>
             )}
           </View>
        </View>

        <View className="items-center mb-8 -mt-6">
          <View className="w-24 h-24 bg-indigo-100 dark:bg-indigo-900 rounded-full items-center justify-center mb-4 border-4 border-white dark:border-slate-800 shadow-sm">
            <Text className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
              {user?.email?.charAt(0).toUpperCase()}
            </Text>
          </View>
          <Text className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
            {user?.email?.split('@')[0]}
          </Text>
          <Text className="text-gray-500 dark:text-gray-400 mb-3">{user?.email}</Text>
          
          <TouchableOpacity 
            onPress={toggleEdit} 
            disabled={isEditing}
            className={`bg-indigo-50 dark:bg-indigo-900/30 px-5 py-2 rounded-full border border-indigo-100 dark:border-indigo-800 ${isEditing ? 'opacity-0' : 'opacity-100'}`}
          >
              <Text className="text-indigo-600 dark:text-indigo-400 font-semibold text-sm">{t('profile.editProfile')}</Text>
          </TouchableOpacity>
        </View>

        <Text className="text-lg font-bold text-gray-900 dark:text-white mb-4">{t('profile.yourStats')}</Text>
        
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
        
        <SelectionModal 
            visible={modalVisible}
            title={`${t('options.select')} ${activeSelectField === 'goal' ? t('options.goal') : t('options.activity')}`}
            options={activeSelectField === 'goal' ? translatedGoalOptions : translatedActivityOptions}
            selectedValue={activeSelectField ? formData[activeSelectField] : ''}
            onSelect={selectOption}
            onClose={() => setModalVisible(false)}
        />







        <Text className="text-center text-gray-400 dark:text-gray-600 mt-8 text-sm">
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
