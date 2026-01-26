import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  Pressable,
  Animated,
  ActivityIndicator,
} from 'react-native';
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
        return { icon: 'stop', color: '#ef4444', label: formatDuration(recordingDuration) }; // red-500
      case 'processing':
        return { icon: 'hourglass', color: '#f59e0b', label: t('addFood.voiceButton.processing') }; // amber-500
      case 'success':
        return { icon: 'checkmark', color: '#10b981', label: t('addFood.voiceButton.success') }; // emerald-500
      case 'error':
        return { icon: 'alert', color: '#ef4444', label: t('addFood.voiceButton.error') }; // red-500
      default: 
        return { icon: 'mic', color: primaryColor, label: t('addFood.voiceButton.record') };
    }
  };

  const config = getStateConfig();

  const getOpticalOffsets = (currentState: string) => {
    switch (currentState) {
        case 'idle': 
            return { transform: [{ translateY: 0}, {translateX: 0}] }; 
        case 'processing': 
             return { transform: [{ translateY: 2}, {translateX: 1.5}] };
        case 'success':
             return { transform: [{ translateX: 0 }, { translateY: 0 }] };
        case 'recording':
            return { transform: [{ translateY: 0 }, {translateX: 0}] };
        default:
            return { transform: [{ translateY: 0 }, {translateX: 0}] };
    }
  };

  const currentOffset = getOpticalOffsets(state);

  return (
    <View className="items-center py-4">
      <Animated.View
        style={{
          transform: [{ scale: pulseAnim }],
          width: buttonSize,
          height: buttonSize,
          borderRadius: buttonSize / 2,
        }}
        className="shadow-sm shadow-black/30 elevation-8"
      >
        <Pressable
          style={{
             width: buttonSize,
             height: buttonSize,
             borderRadius: buttonSize / 2,
             backgroundColor: config.color,
             alignItems: 'center',
             justifyContent: 'center',
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
          <View style={{ 
                width: iconSize, 
                height: iconSize, 
                justifyContent: 'center', 
                alignItems: 'center',
            }}>
            {state === 'processing' ? (
                <ActivityIndicator size="large" color="#FFFFFF" style={currentOffset} />
            ) : (
                <IconSymbol
                name={config.icon as IconSymbolName}
                size={iconSize}
                color="#FFFFFF"
                style={currentOffset}
                />
            )}
          </View>
        </Pressable>
      </Animated.View>

      <Text className="mt-3 text-base font-semibold" style={{ color: textColor }}>
        {config.label}
      </Text>

      {state === 'idle' && (
        <Text className="mt-2 text-xs text-muted-foreground">
          {t('addFood.voiceButton.hold')}
        </Text>
      )}

      {state === 'recording' && (
        <Text className="mt-2 text-xs text-muted-foreground">
          {t('addFood.voiceButton.release')}
        </Text>
      )}

      {permissionStatus === 'denied' && (
        <Text className="mt-2 text-center text-xs text-destructive">
          {t('addFood.voiceButton.permission')}
        </Text>
      )}
    </View>
  );
}
