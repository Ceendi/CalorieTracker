import React from 'react';
import { View, Text, TouchableOpacity, TextInput } from 'react-native';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { useLanguage } from '@/hooks/useLanguage';
import { useColorScheme } from '@/hooks/useColorScheme';
import { Colors } from '@/constants/theme';

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
  const { colorScheme } = useColorScheme();

  const getDisplayValue = () => {
     if (isSelect && selectOptions) {
        return selectOptions.find(o => o.value === value)?.label || value;
     }
     return value;
  };

  const displayValue = value ? getDisplayValue() : '-';
  const suffix = isNumber && value ? (fieldKey === 'height' ? ' cm' : fieldKey === 'weight' ? ' kg' : t('units.age')) : '';

  return (
    <View className="flex-row items-center justify-between p-4 bg-card rounded-2xl mb-3 border border-border h-[72px]">
      <View className="flex-row items-center gap-3">
        <View className="p-2 bg-primary/10 rounded-full">
            <IconSymbol name={icon as any} size={20} color={Colors[colorScheme ?? 'light'].tint} />
        </View>
        <Text className="text-muted-foreground font-medium">{label}</Text>
      </View>
      
      {isEditing ? (
        isSelect ? (
           <TouchableOpacity onPress={onOpenSelection} className="flex-row items-center flex-1 justify-end">
              <Text className="text-primary font-bold text-lg text-right mr-2">
               {value ? getDisplayValue() : t('options.select')}
             </Text>
             <IconSymbol name="chevron.down" size={16} color={Colors[colorScheme ?? 'light'].tint} />
           </TouchableOpacity>
        ) : (
            <TextInput
              value={value}
              onChangeText={onChangeText}
              keyboardType={isNumber ? 'numeric' : 'default'}
              className="flex-1 text-primary font-bold text-right h-full"
              style={{ fontSize: 18, textAlignVertical: 'center', includeFontPadding: false, paddingVertical: 0 }}
              placeholder="-"
              placeholderTextColor={Colors[colorScheme ?? 'light'].placeholder}
              selectTextOnFocus
            />
        )
      ) : (
        <Text className="text-foreground font-bold text-lg text-right flex-1">
           {displayValue}
           {suffix}
        </Text>
      )}
    </View>
  );
};
