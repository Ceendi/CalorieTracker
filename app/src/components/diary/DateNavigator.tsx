import React from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { format, addDays, subDays } from 'date-fns';
import { pl, enUS } from 'date-fns/locale';
import { useLanguage } from '@/hooks/useLanguage';
import { useColorScheme } from '@/hooks/useColorScheme';
import { Colors } from '@/constants/theme';

interface DateNavigatorProps {
  date: Date;
  onDateChange: (date: Date) => void;
}

export function DateNavigator({ date, onDateChange }: DateNavigatorProps) {
  const { language } = useLanguage();
  const { colorScheme } = useColorScheme();
  const theme = colorScheme ?? 'light';
  const locale = language === 'pl' ? pl : enUS;

  const handlePrev = () => onDateChange(subDays(date, 1));
  const handleNext = () => onDateChange(addDays(date, 1));

  const isToday = format(date, 'yyyy-MM-dd') === format(new Date(), 'yyyy-MM-dd');

  return (
    <View className="flex-row items-center justify-between mb-6">
      <TouchableOpacity onPress={handlePrev} className="p-2 rounded-full bg-secondary">
        <IconSymbol name="chevron.left" size={20} color={Colors[theme].text} />
      </TouchableOpacity>
      
      <View className="items-center">
        <Text className="text-lg font-bold text-foreground capitalize">
          {isToday ? (language === 'pl' ? 'Dzisiaj' : 'Today') : format(date, 'EEEE, d MMM', { locale })}
        </Text>
      </View>

      <TouchableOpacity onPress={handleNext} className="p-2 rounded-full bg-secondary">
        <IconSymbol name="chevron.right" size={20} color={Colors[theme].text} />
      </TouchableOpacity>
    </View>
  );
}
