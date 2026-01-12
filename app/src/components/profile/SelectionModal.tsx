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
      <View className="bg-white dark:bg-slate-800 w-[80%] rounded-2xl overflow-hidden">
        <View className="p-4 border-b border-gray-100 dark:border-gray-700">
          <Text className="text-lg font-bold text-center text-gray-900 dark:text-white">
            {title}
          </Text>
        </View>
        {options.map((option) => (
          <TouchableOpacity 
            key={option.value} 
            onPress={() => onSelect(option.value)}
            className="p-4 border-b border-gray-100 dark:border-gray-700 last:border-0 active:bg-gray-50 dark:active:bg-slate-700"
          >
            <Text className={`text-center text-base ${selectedValue === option.value ? 'text-indigo-600 font-bold' : 'text-gray-700 dark:text-gray-300'}`}>
              {option.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
};
