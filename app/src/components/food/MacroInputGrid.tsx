import React from 'react';
import { View, Text, TextInput } from 'react-native';
import { Control, Controller } from 'react-hook-form';
import { useLanguage } from '@/hooks/useLanguage';
import { ManualFoodFormValues } from '@/schemas/food';
import { useColorScheme } from '@/hooks/useColorScheme';
import { Colors } from '@/constants/theme';

interface MacroInputGridProps {
  control: Control<ManualFoodFormValues>;
}

export function MacroInputGrid({ control }: MacroInputGridProps) {
  const { t } = useLanguage();
  const { colorScheme } = useColorScheme();
  const theme = colorScheme ?? 'light';

  return (
    <View className="bg-card rounded-2xl p-4 mb-4 shadow-sm border border-border">
        <Text className="text-sm font-medium text-muted-foreground mb-3">{t('manualEntry.nutritionLabel')}</Text>
        
        <View className="flex-row gap-3 mb-3">
            <View className="flex-1">
                <Text className="text-xs text-muted-foreground mb-1">{t('manualEntry.calories')}</Text>
                <View className="border border-border rounded-xl bg-background h-12 justify-center px-3">
                    <Controller
                        control={control}
                        name="calories"
                        render={({ field: { onChange, value } }) => (
                            <TextInput
                                testID="macro-calories"
                                className="text-foreground w-full"
                                style={{ fontSize: 16, textAlignVertical: 'center', paddingVertical: 0, includeFontPadding: false, height: '100%' }}
                                value={value?.toString()}
                                onChangeText={onChange}
                                keyboardType="numeric"
                                placeholder="0"
                                placeholderTextColor={Colors[theme].placeholder}
                            />
                        )}
                    />
                </View>
            </View>
            <View className="flex-1">
                <Text className="text-xs text-muted-foreground mb-1">{t('manualEntry.protein')}</Text>
                <View className="border border-border rounded-xl bg-background h-12 justify-center px-3">
                    <Controller
                        control={control}
                        name="protein"
                        render={({ field: { onChange, value } }) => (
                            <TextInput
                                testID="macro-protein"
                                className="text-foreground w-full"
                                style={{ fontSize: 16, textAlignVertical: 'center', paddingVertical: 0, includeFontPadding: false, height: '100%' }}
                                value={value?.toString()}
                                onChangeText={onChange}
                                keyboardType="numeric"
                                placeholder="0"
                                placeholderTextColor={Colors[theme].placeholder}
                            />
                        )}
                    />
                </View>
            </View>
        </View>
            <View className="flex-row gap-3">
            <View className="flex-1">
                <Text className="text-xs text-muted-foreground mb-1">{t('manualEntry.fat')}</Text>
                <View className="border border-border rounded-xl bg-background h-12 justify-center px-3">
                    <Controller
                        control={control}
                        name="fat"
                        render={({ field: { onChange, value } }) => (
                            <TextInput
                                testID="macro-fat"
                                className="text-foreground w-full"
                                style={{ fontSize: 16, textAlignVertical: 'center', paddingVertical: 0, includeFontPadding: false, height: '100%' }}
                                value={value?.toString()}
                                onChangeText={onChange}
                                keyboardType="numeric"
                                placeholder="0"
                                placeholderTextColor={Colors[theme].placeholder}
                            />
                        )}
                    />
                </View>
            </View>
            <View className="flex-1">
                <Text className="text-xs text-muted-foreground mb-1">{t('manualEntry.carbs')}</Text>
                <View className="border border-border rounded-xl bg-background h-12 justify-center px-3">
                    <Controller
                        control={control}
                        name="carbs"
                        render={({ field: { onChange, value } }) => (
                            <TextInput
                                testID="macro-carbs"
                                className="text-foreground w-full"
                                style={{ fontSize: 16, textAlignVertical: 'center', paddingVertical: 0, includeFontPadding: false, height: '100%' }}
                                value={value?.toString()}
                                onChangeText={onChange}
                                keyboardType="numeric"
                                placeholder="0"
                                placeholderTextColor={Colors[theme].placeholder}
                            />
                        )}
                    />
                </View>
            </View>
        </View>

        <View className="flex-row gap-3 mt-3">
            <View className="flex-1">
                <Text className="text-xs text-muted-foreground mb-1">{t('foodDetails.gl.ig')} ({t('menu.optional') || 'Opcjonalnie'})</Text>
                <View className="border border-border rounded-xl bg-background h-12 justify-center px-3">
                    <Controller
                        control={control}
                        name="glycemic_index"
                        render={({ field: { onChange, value } }) => (
                            <TextInput
                                testID="macro-gi"
                                className="text-foreground w-full"
                                style={{ fontSize: 16, textAlignVertical: 'center', paddingVertical: 0, includeFontPadding: false, height: '100%' }}
                                value={value?.toString()}
                                onChangeText={onChange}
                                keyboardType="numeric"
                                placeholder="0"
                                placeholderTextColor={Colors[theme].placeholder}
                            />
                        )}
                    />
                </View>
            </View>
        </View>
    </View>
  );
}
