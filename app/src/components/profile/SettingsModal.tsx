import React, { useState } from 'react';
import { View, Text, TouchableOpacity, Modal, Switch, ScrollView, Alert } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { useColorScheme } from '@/hooks/useColorScheme';
import { useAuth } from '@/hooks/useAuth';
import { ChangePasswordModal } from './ChangePasswordModal';
import { useLanguage } from '@/hooks/useLanguage';
import { Colors } from '@/constants/theme';

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
  const [isDarkLocal, setIsDarkLocal] = useState(colorScheme === 'dark');
  const [changePasswordVisible, setChangePasswordVisible] = useState(false);

  const handleThemeToggle = async () => {
    const newValue = !isDarkLocal;
    setIsDarkLocal(newValue);
    
    setTimeout(async () => {
      await toggleColorScheme();
    }, 100);
  };

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
      <View className="flex-1 bg-background">
        <View className="flex-row justify-center items-center p-4 border-b border-border bg-background relative">
          <Text className="text-xl font-bold text-foreground">{t('settings.title')}</Text>
          <TouchableOpacity 
            onPress={onClose} 
            className="p-2 bg-muted/50 rounded-full absolute right-4"
          >
            <IconSymbol name="xmark" size={20} color={Colors[colorScheme ?? 'light'].text} />
          </TouchableOpacity>
        </View>

        <ScrollView className="flex-1 p-4">
          <Text className="text-sm font-bold text-muted-foreground mb-2 uppercase tracking-wider ml-1">
            {t('settings.preferences')}
          </Text>
          <View className="bg-card rounded-2xl mb-6 overflow-hidden border border-border">
            
            <View className="flex-row items-center justify-between p-4 border-b border-border">
              <View className="flex-row items-center gap-3">
                <View className="p-2 bg-primary/10 rounded-full">
                  <IconSymbol name="moon.stars.fill" size={20} color={Colors[colorScheme ?? 'light'].tint} />
                </View>
                <Text className="text-base font-medium text-foreground">{t('settings.darkMode')}</Text>
              </View>
              <Switch 
                value={isDarkLocal} 
                onValueChange={handleThemeToggle}
                trackColor={{ false: '#E5E7EB', true: Colors.light.tint }}
                thumbColor={'#fff'} 
              />
            </View>

            <TouchableOpacity onPress={handleChangeLanguage} className="flex-row items-center justify-between p-4">
              <View className="flex-row items-center gap-3">
                <View className="p-2 bg-emerald-500/10 rounded-full">
                  <IconSymbol name="globe" size={20} color="#10B981" />
                </View>
                <Text className="text-base font-medium text-foreground">{t('settings.language')}</Text>
              </View>
              <View className="flex-row items-center gap-2">
                <Text className="text-muted-foreground">{language === 'en' ? 'English' : 'Polski'}</Text>
                <IconSymbol name="chevron.right" size={16} color={Colors[colorScheme ?? 'light'].text} />
              </View>
            </TouchableOpacity>
          </View>

          {mode === 'authenticated' && (
            <>
              <Text className="text-sm font-bold text-muted-foreground mb-2 uppercase tracking-wider ml-1">
                {t('settings.account')}
              </Text>
              <View className="bg-card rounded-2xl mb-6 overflow-hidden border border-border shadow-sm">
                
                <TouchableOpacity 
                  onPress={() => setChangePasswordVisible(true)}
                  className="flex-row items-center justify-between p-4"
                >
                  <View className="flex-row items-center gap-3">
                    <View className="p-2 bg-orange-500/10 rounded-full">
                      <IconSymbol name="lock.fill" size={20} color="#F97316" />
                    </View>
                    <Text className="text-base font-medium text-foreground">{t('settings.changePassword')}</Text>
                  </View>
                  <IconSymbol name="chevron.right" size={16} color={Colors[colorScheme ?? 'light'].text} />
                </TouchableOpacity>

              </View>
              
               <TouchableOpacity 
                 onPress={handleLogout}
                 className="flex-row items-center justify-center p-4 bg-card rounded-2xl border border-border shadow-sm mt-2 active:bg-muted"
               >
                 <IconSymbol name="rectangle.portrait.and.arrow.right" size={20} color="#EF4444" />
                 <Text className="ml-2 text-destructive font-bold text-lg">{t('settings.logout')}</Text>
               </TouchableOpacity>
            </>
          )}

           <Text className="text-center text-muted-foreground text-xs mt-6 mb-8">
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
