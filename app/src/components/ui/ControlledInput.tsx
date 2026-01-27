import React from 'react';
import { View, Text, TextInput, TextInputProps } from 'react-native';
import { Control, Controller, FieldValues, Path } from 'react-hook-form';

interface ControlledInputProps<T extends FieldValues> extends TextInputProps {
  control: Control<T>;
  name: Path<T>;
  label?: string;
  error?: string;
}

export function ControlledInput<T extends FieldValues>({ control, name, label, error, style, ...textInputProps }: ControlledInputProps<T>) {
  return (
    <View className="mb-4">
      {label && <Text className="text-foreground font-medium mb-1">{label}</Text>}
      <Controller
        control={control}
        name={name}
        render={({ field: { onChange, onBlur, value } }) => (
          <View className={`bg-card border rounded-lg h-12 justify-center px-3 ${error ? 'border-destructive' : 'border-border'}`}>
            <TextInput
              className="text-foreground flex-1"
              style={{ fontSize: 16, paddingVertical: 0, includeFontPadding: false }}
              placeholderTextColor="#9CA3AF"
              onBlur={onBlur}
              onChangeText={onChange}
              value={value}
              {...textInputProps}
            />
          </View>
        )}
      />
      {error && <Text className="text-destructive text-sm mt-1">{error}</Text>}
    </View>
  );
};
