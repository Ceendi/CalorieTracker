import React from 'react';
import { View, Text, TextInput, TextInputProps } from 'react-native';
import { Control, Controller } from 'react-hook-form';

interface ControlledInputProps extends TextInputProps {
  control: Control<any>;
  name: string;
  label?: string;
  error?: string;
}

export const ControlledInput = ({ control, name, label, error, style, ...textInputProps }: ControlledInputProps) => {
  return (
    <View className="mb-4">
      {label && <Text className="text-gray-700 dark:text-gray-300 font-medium mb-1">{label}</Text>}
      <Controller
        control={control}
        name={name}
        render={({ field: { onChange, onBlur, value } }) => (
          <TextInput
            className={`bg-white dark:bg-slate-800 border text-gray-900 dark:text-white rounded-lg p-3 ${error ? 'border-red-500' : 'border-gray-300 dark:border-gray-700'}`}
            placeholderTextColor="#9CA3AF"
            onBlur={onBlur}
            onChangeText={onChange}
            value={value}
            {...textInputProps}
          />
        )}
      />
      {error && <Text className="text-red-500 text-sm mt-1">{error}</Text>}
    </View>
  );
};
