import React from 'react';
import { View, Text } from 'react-native';
import { CircularProgress } from '@/components/ui/CircularProgress';

interface NutrientRingProps {
  label: string;
  current: number;
  total: number;
  unit: string;
  color: string;
  bgColor?: string;
}

export function NutrientRing({ label, current, total, unit, color, bgColor }: NutrientRingProps) {
  const progress = Math.min(current / total, 1);
  const size = 60;
  const strokeWidth = 5;

  return (
    <View className="items-center bg-card p-3 rounded-2xl flex-1 mx-1.5 shadow-sm border border-border">
      <View className="mb-2">
          <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
             <View className="absolute inset-0 border-4 border-muted rounded-full opacity-30" />
             <CircularProgress 
                size={size} 
                strokeWidth={strokeWidth} 
                progress={progress} 
                color={color} 
                bgColor={bgColor} 
             >
                <Text className="text-[10px] font-bold text-muted-foreground">
                    {Math.round(progress * 100)}%
                </Text>
             </CircularProgress>
          </View>
      </View>
      
      <Text className="text-foreground font-bold text-lg -mb-0.5">
          {Math.round(current)}
          <Text className="text-xs font-normal text-muted-foreground">/{total}{unit}</Text>
      </Text>
      <Text 
        className="text-xs font-medium text-muted-foreground uppercase tracking-wide"
        numberOfLines={1}
        adjustsFontSizeToFit
      >
        {label}
      </Text>
    </View>
  );
}
