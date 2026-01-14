import React from 'react';
import { View, Text, TouchableOpacity, TextInput } from 'react-native';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { useLanguage } from '@/hooks/useLanguage';

interface InfoItemProps {
  label: string;
  value: string;
  icon: string;
  isEditing: boolean;
  fieldKey: string;
  isNumber?: boolean;
  isSelect?: boolean;
  selectOptions?: { label: string; value: string }[];
  onChangeText?: (text: string) => void;
  onOpenSelection?: () => void;
}

export const InfoItem = ({ 
  label, 
  value, 
  icon, 
  isEditing, 
  fieldKey, 
  isNumber = false, 
  isSelect = false,
  selectOptions,
  onChangeText,
  onOpenSelection
}: InfoItemProps) => {
  const { t } = useLanguage();

  const getDisplayValue = () => {
     if (isSelect && selectOptions) {
        return selectOptions.find(o => o.value === value)?.label || value;
     }
     return value;
  };

  const displayValue = value ? getDisplayValue() : '-';
  const suffix = isNumber && value ? (fieldKey === 'height' ? ' cm' : fieldKey === 'weight' ? ' kg' : t('units.age')) : '';

  return (
    <View className="flex-row items-center justify-between p-4 bg-white dark:bg-slate-800 rounded-2xl mb-3 border border-gray-100 dark:border-gray-700 h-[72px]">
      <View className="flex-row items-center gap-3">
        <View className="p-2 bg-indigo-50 dark:bg-indigo-900/30 rounded-full">
            <IconSymbol name={icon as any} size={20} color="#4F46E5" />
        </View>
        <Text className="text-gray-600 dark:text-gray-300 font-medium">{label}</Text>
      </View>
      
      {isEditing ? (
        isSelect ? (
           <TouchableOpacity onPress={onOpenSelection} className="flex-row items-center flex-1 justify-end">
             <Text className="text-indigo-600 dark:text-indigo-400 font-bold text-lg text-right mr-2">
               {value ? getDisplayValue() : 'Select'}
             </Text>
             <IconSymbol name="chevron.down" size={16} color="#4F46E5" />
           </TouchableOpacity>
        ) : (
            <TextInput
              value={value}
              onChangeText={onChangeText}
              keyboardType={isNumber ? 'numeric' : 'default'}
              className="flex-1 text-indigo-600 dark:text-indigo-400 font-bold text-right h-full"
              style={{ fontSize: 18, textAlignVertical: 'center', includeFontPadding: false, paddingVertical: 0 }}
              placeholder="-"
              placeholderTextColor="#9CA3AF"
              selectTextOnFocus
            />
        )
      ) : (
        <Text className="text-gray-900 dark:text-white font-bold text-lg text-right flex-1">
           {displayValue}
           {suffix}
        </Text>
      )}
    </View>
  );
};
