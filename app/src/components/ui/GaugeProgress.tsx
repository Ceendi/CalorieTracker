import React, { useEffect } from 'react';
import { View } from 'react-native';
import Svg, { Circle } from 'react-native-svg';
import Animated, { useSharedValue, useAnimatedProps, withTiming } from 'react-native-reanimated';

const AnimatedCircle = Animated.createAnimatedComponent(Circle);

interface GaugeProgressProps {
  size?: number;
  strokeWidth?: number;
  progress: number; // 0 to 1
  color?: string;
  trackColor?: string;
  children?: React.ReactNode;
}

export function GaugeProgress({
  size = 200,
  strokeWidth = 15,
  progress,
  color = '#FFFFFF',
  trackColor = 'rgba(255,255,255,0.2)',
  children
}: GaugeProgressProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  
  const arcPercentage = 0.75; // 270 / 360
  const arcLength = circumference * arcPercentage;
  
  const animatedProgress = useSharedValue(0);

  useEffect(() => {
    animatedProgress.value = withTiming(progress, { duration: 1200 }); // slower, smoother animation
  }, [progress]);

  const animatedProps = useAnimatedProps(() => {
    const p = Math.min(Math.max(animatedProgress.value, 0), 1);
    const validLength = p * arcLength;
    
    return {
      strokeDasharray: [validLength, circumference],
    };
  });

  return (
    <View style={{ width: size, height: size, justifyContent: 'center', alignItems: 'center', position: 'relative' }}>
        <Svg width={size} height={size} style={{ transform: [{ rotate: '135deg' }] }}>
            <Circle
                cx={size / 2}
                cy={size / 2}
                r={radius}
                stroke={trackColor}
                strokeWidth={strokeWidth}
                fill="transparent"
                strokeDasharray={[arcLength, circumference]}
                strokeLinecap="round"
            />
            
            <AnimatedCircle
                cx={size / 2}
                cy={size / 2}
                r={radius}
                stroke={color}
                strokeWidth={strokeWidth}
                fill="transparent"
                strokeLinecap="round"
                animatedProps={animatedProps}
            />
        </Svg>
        
        <View className="absolute inset-0 justify-center items-center">
            {children}
        </View>
    </View>
  );
}
