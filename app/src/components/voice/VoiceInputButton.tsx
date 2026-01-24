import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  Pressable,
  Animated,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useVoiceInput } from '@/hooks/useVoiceInput';
import { useThemeColor } from '@/hooks/use-theme-color';
import { useLanguage } from '@/hooks/useLanguage';
import { IconSymbol, IconSymbolName } from '@/components/ui/IconSymbol';

interface VoiceInputButtonProps {
  onMealProcessed?: (meal: any) => void;
  onError?: (error: string) => void;
  size?: 'small' | 'medium' | 'large';
}

export function VoiceInputButton({
  onMealProcessed,
  onError,
  size = 'large',
}: VoiceInputButtonProps) {
  const {
    state,
    recordingDuration,
    processedMeal,
    error,
    startRecording,
    stopAndProcess,
    cancelRecording,
    reset: resetInput,
    permissionStatus,
    requestPermission,
  } = useVoiceInput();

  const pulseAnim = useRef(new Animated.Value(1)).current;
  
  const primaryColor = useThemeColor({}, 'tint');
  const textColor = useThemeColor({}, 'text');

  useEffect(() => {
    if (state === 'recording') {
      const pulse = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.1,
            duration: 500,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 500,
            useNativeDriver: true,
          }),
        ])
      );
      pulse.start();
      return () => pulse.stop();
    } else {
      pulseAnim.setValue(1);
    }
  }, [state, pulseAnim]);

  useEffect(() => {
    if (state === 'success' && processedMeal) {
      onMealProcessed?.(processedMeal);
    }
  }, [state, processedMeal, onMealProcessed]);

  useEffect(() => {
    if (state === 'error' && error) {
      onError?.(error);
    }
  }, [state, error, onError]);

  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>;
    if (state === 'success' || state === 'error') {
      timeout = setTimeout(() => {
        resetInput();
      }, 3000);
    }
    return () => {
      if (timeout) clearTimeout(timeout);
    };
  }, [state, resetInput]);

  const getButtonSize = () => {
    switch (size) {
      case 'small': return 60;
      case 'medium': return 80;
      case 'large': return 100;
      default: return 100;
    }
  };

  const buttonSize = getButtonSize();
  const iconSize = buttonSize * 0.4;

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const { t } = useLanguage();
  
  const getStateConfig = (): { icon: string; color: string; label: string } => {
    switch (state) {
      case 'idle':
        return { icon: 'mic.fill', color: primaryColor, label: t('addFood.voiceButton.record') };
      case 'recording':
        return { icon: 'stop', color: '#FF3B30', label: formatDuration(recordingDuration) };
      case 'processing':
        return { icon: 'hourglass', color: '#FF9500', label: t('addFood.voiceButton.processing') };
      case 'success':
        return { icon: 'checkmark', color: '#34C759', label: t('addFood.voiceButton.success') };
      case 'error':
        return { icon: 'alert', color: '#FF3B30', label: t('addFood.voiceButton.error') };
      default: 
        return { icon: 'mic', color: primaryColor, label: t('addFood.voiceButton.record') };
    }
  };

  const config = getStateConfig();
  const isIconSymbolCompatible = config.icon === 'mic.fill'; 

  return (
    <View className="items-center py-4">
      <Animated.View
        style={{
          transform: [{ scale: pulseAnim }],
        }}
        className="shadow-sm shadow-black/30 elevation-8"
      >
        <Pressable
          className="items-center justify-center"
          style={{
             width: buttonSize,
             height: buttonSize,
             borderRadius: buttonSize / 2,
             backgroundColor: config.color,
             padding: 0,
             margin: 0,
          }}
          onPressIn={async () => {
             if (state === 'idle' || state === 'error' || state === 'success') {
                if (permissionStatus !== 'granted') {
                  const granted = await requestPermission();
                  if (!granted) {
                    onError?.(t('addFood.voiceButton.noPermission'));
                    return;
                  }
                }
                await startRecording();
             }
          }}
          onPressOut={async () => {
             if (state === 'recording') {
                await stopAndProcess();
             }
          }}
          disabled={state === 'processing'}
        >
          {state === 'processing' ? (
            <View style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, alignItems: 'center', justifyContent: 'center' }}>
              <ActivityIndicator size="large" color="#FFFFFF" />
            </View>
          ) : (
             isIconSymbolCompatible ? (
                <IconSymbol
                  name={config.icon as IconSymbolName}
                  size={iconSize}
                  color="#FFFFFF"
                />
             ) : (
                <Ionicons
                  name={config.icon as any}
                  size={iconSize}
                  color="#FFFFFF"
                />
             )
          )}
        </Pressable>
      </Animated.View>

      <Text className="mt-3 text-base font-semibold" style={{ color: textColor }}>
        {config.label}
      </Text>

      {state === 'idle' && (
        <Text className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          {t('addFood.voiceButton.hold')}
        </Text>
      )}

      {state === 'recording' && (
        <Text className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          {t('addFood.voiceButton.release')}
        </Text>
      )}

      {permissionStatus === 'denied' && (
        <Text className="mt-2 text-center text-xs text-red-500">
          {t('addFood.voiceButton.permission')}
        </Text>
      )}
    </View>
  );
}
