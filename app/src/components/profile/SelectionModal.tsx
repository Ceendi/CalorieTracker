import React from 'react';
import { View, Text, TouchableOpacity } from 'react-native';

interface Option {
  label: string;
  value: string;
}

interface SelectionModalProps {
  visible: boolean;
  title: string;
  options: Option[];
  selectedValue: string;
  onSelect: (value: string) => void;
  onClose: () => void;
}

export const SelectionModal = ({ visible, title, options, selectedValue, onSelect, onClose }: SelectionModalProps) => {
  if (!visible) return null;

  return (
    <View className="absolute top-0 bottom-0 left-0 right-0 justify-center items-center z-50">
      <TouchableOpacity className="absolute inset-0 bg-black/50" onPress={onClose} />
      <View className="bg-card w-[80%] rounded-2xl overflow-hidden border border-border">
        <View className="p-4 border-b border-border">
          <Text className="text-lg font-bold text-center text-foreground">
            {title}
          </Text>
        </View>
        {options.map((option) => (
          <TouchableOpacity 
            key={option.value} 
            onPress={() => onSelect(option.value)}
            className="p-4 border-b border-border last:border-0 active:bg-muted"
          >
            <Text className={`text-center text-base ${selectedValue === option.value ? 'text-primary font-bold' : 'text-foreground'}`}>
              {option.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
};
