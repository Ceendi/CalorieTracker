import React, { useEffect } from 'react';
import { View } from 'react-native';
import Svg, { Circle } from 'react-native-svg';
import Animated, { useSharedValue, useAnimatedProps, withTiming } from 'react-native-reanimated';

const AnimatedCircle = Animated.createAnimatedComponent(Circle);

interface ArcProgressProps {
  size?: number;
  strokeWidth?: number;
  progress: number; // 0 to 1
  color?: string;
  bgColor?: string;
  children?: React.ReactNode;
}

export function ArcProgress({
  size = 120,
  strokeWidth = 12,
  progress,
  color = '#FFFFFF',
  bgColor = 'rgba(255,255,255,0.2)',
  children
}: ArcProgressProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const arcLength = circumference / 2;

  const animatedProgress = useSharedValue(0);

  useEffect(() => {
    animatedProgress.value = withTiming(progress, { duration: 1000 });
  }, [progress]);

  const animatedProps = useAnimatedProps(() => {
    const p = Math.min(Math.max(animatedProgress.value, 0), 1);
    const dashLength = p * arcLength;
    return {
      strokeDasharray: [dashLength, circumference],
    };
  });

  return (
    <View style={{ width: size, height: size / 2 + strokeWidth, justifyContent: 'flex-start', alignItems: 'center' }}>
      <View style={{ transform: [{ scaleX: -1 }] }}>
           <Svg width={size} height={size} style={{ transform: [{ translateY: -size / 2 }] }}>
                <Circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    stroke={bgColor}
                    strokeWidth={strokeWidth}
                    fill="transparent"
                    strokeDasharray={[arcLength, circumference]}
                    strokeLinecap="round"
                    rotation={0}
                    origin={`${size/2}, ${size/2}`}
                />
                
                <AnimatedCircle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    stroke={color}
                    strokeWidth={strokeWidth}
                    fill="transparent"
                    strokeLinecap="round"
                    rotation={0}
                    origin={`${size/2}, ${size/2}`}
                    animatedProps={animatedProps}
                />
            </Svg>
      </View>
      
      <View className="absolute top-0 w-full h-full justify-start items-center pt-2">
        {children}
      </View>
    </View>
  );
}
