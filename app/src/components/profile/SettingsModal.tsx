import React, { useState } from 'react';
import { View, Text, TouchableOpacity, Modal, Switch, ScrollView, Alert } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { useAuth } from '@/hooks/useAuth';
import { ChangePasswordModal } from './ChangePasswordModal';
import { useLanguage } from '@/hooks/useLanguage';

interface SettingsModalProps {
  visible: boolean;
  onClose: () => void;
  mode?: 'authenticated' | 'public';
}

export function SettingsModal({ visible, onClose, mode = 'authenticated' }: SettingsModalProps) {
  const insets = useSafeAreaInsets();
  const { colorScheme, toggleColorScheme } = useColorScheme();
  const { signOut } = useAuth();
  const { language, setLanguage, t } = useLanguage();
  const [changePasswordVisible, setChangePasswordVisible] = useState(false);

  const handleLogout = () => {
    Alert.alert(t('settings.logoutConfirmationTitle'), t('settings.logoutConfirmationMessage'), [
      { text: t('settings.cancel'), style: "cancel" },
      { text: t('settings.logout'), style: "destructive", onPress: async () => {
         onClose();
         await signOut();
      }}
    ]);
  };

  const handleChangeLanguage = () => {
    Alert.alert(t('settings.language'), undefined, [
      { text: "English", onPress: () => setLanguage('en') },
      { text: "Polski", onPress: () => setLanguage('pl') },
      { text: t('settings.cancel'), style: "cancel" }
    ]);
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <View className="flex-1 bg-gray-50 dark:bg-slate-900">
        <View className="flex-row justify-center items-center p-4 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-slate-900 relative">
          <Text className="text-xl font-bold text-gray-900 dark:text-white">{t('settings.title')}</Text>
          <TouchableOpacity 
            onPress={onClose} 
            className="p-2 bg-gray-100 dark:bg-slate-800 rounded-full absolute right-4"
          >
            <IconSymbol name="xmark" size={20} color="#6B7280" />
          </TouchableOpacity>
        </View>

        <ScrollView className="flex-1 p-4">
          <Text className="text-sm font-bold text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wider ml-1">
            {t('settings.preferences')}
          </Text>
          <View className="bg-white dark:bg-slate-800 rounded-2xl mb-6 overflow-hidden">
            
            <View className="flex-row items-center justify-between p-4 border-b border-gray-100 dark:border-gray-700">
              <View className="flex-row items-center gap-3">
                <View className="p-2 bg-indigo-50 dark:bg-indigo-900/30 rounded-full">
                  <IconSymbol name="moon.stars.fill" size={20} color="#4F46E5" />
                </View>
                <Text className="text-base font-medium text-gray-900 dark:text-white">{t('settings.darkMode')}</Text>
              </View>
              <Switch 
                value={colorScheme === 'dark'} 
                onValueChange={toggleColorScheme}
                trackColor={{ false: '#E5E7EB', true: '#4F46E5' }}
                thumbColor={'#fff'} 
              />
            </View>

            <TouchableOpacity onPress={handleChangeLanguage} className="flex-row items-center justify-between p-4">
              <View className="flex-row items-center gap-3">
                <View className="p-2 bg-emerald-50 dark:bg-emerald-900/30 rounded-full">
                  <IconSymbol name="globe" size={20} color="#10B981" />
                </View>
                <Text className="text-base font-medium text-gray-900 dark:text-white">{t('settings.language')}</Text>
              </View>
              <View className="flex-row items-center gap-2">
                <Text className="text-gray-500">{language === 'en' ? 'English' : 'Polski'}</Text>
                <IconSymbol name="chevron.right" size={16} color="#9CA3AF" />
              </View>
            </TouchableOpacity>
          </View>

          {mode === 'authenticated' && (
            <>
              <Text className="text-sm font-bold text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wider ml-1">
                {t('settings.account')}
              </Text>
              <View className="bg-white dark:bg-slate-800 rounded-2xl mb-6 overflow-hidden">
                
                <TouchableOpacity 
                  onPress={() => setChangePasswordVisible(true)}
                  className="flex-row items-center justify-between p-4"
                >
                  <View className="flex-row items-center gap-3">
                    <View className="p-2 bg-orange-50 dark:bg-orange-900/30 rounded-full">
                      <IconSymbol name="lock.fill" size={20} color="#F97316" />
                    </View>
                    <Text className="text-base font-medium text-gray-900 dark:text-white">{t('settings.changePassword')}</Text>
                  </View>
                  <IconSymbol name="chevron.right" size={16} color="#9CA3AF" />
                </TouchableOpacity>

              </View>
              
               <TouchableOpacity 
                 onPress={handleLogout}
                 className="flex-row items-center justify-center p-4 bg-red-50 dark:bg-red-900/20 rounded-2xl border border-red-100 dark:border-red-900/50 mt-2"
               >
                 <IconSymbol name="rectangle.portrait.and.arrow.right" size={20} color="#DC2626" />
                 <Text className="ml-2 text-red-600 dark:text-red-400 font-bold text-lg">{t('settings.logout')}</Text>
               </TouchableOpacity>
            </>
          )}

           <Text className="text-center text-gray-400 text-xs mt-6 mb-8">
            App {t('profile.version')} 1.0.0 (Build 42)
          </Text>

        </ScrollView>
        
        <ChangePasswordModal 
          visible={changePasswordVisible}
          onClose={() => setChangePasswordVisible(false)}
        />
      </View>
    </Modal>
  );
}
