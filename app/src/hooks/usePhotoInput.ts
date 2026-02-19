import { useState, useCallback } from 'react';
import * as ImagePicker from 'expo-image-picker';
import { useLanguage } from './useLanguage';
import { aiService } from '@/services/ai.service';
import { ProcessedMeal } from '@/types/ai';

export type PhotoInputState = 
  | 'idle'
  | 'picking'
  | 'processing'
  | 'success'
  | 'error';

interface UsePhotoInputResult {
  state: PhotoInputState;
  processedMeal: ProcessedMeal | null;
  error: string | null;
  
  pickImage: () => Promise<void>;
  takePhoto: () => Promise<void>;
  reset: () => void;
  
  permissionStatus: ImagePicker.PermissionStatus | 'undetermined';
  requestPermission: () => Promise<boolean>;
}

export function usePhotoInput(): UsePhotoInputResult {
  const { t } = useLanguage();
  const [state, setState] = useState<PhotoInputState>('idle');
  const [processedMeal, setProcessedMeal] = useState<ProcessedMeal | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [permissionStatus, setPermissionStatus] = useState<ImagePicker.PermissionStatus | 'undetermined'>('undetermined');

  const requestPermission = useCallback(async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    const { status: cameraStatus } = await ImagePicker.requestCameraPermissionsAsync();
    
    // We strictly need at least one, but for simplicity let's track general status
    // If either is granted we can proceed with that mode
    if (status === ImagePicker.PermissionStatus.GRANTED || cameraStatus === ImagePicker.PermissionStatus.GRANTED) {
        setPermissionStatus(ImagePicker.PermissionStatus.GRANTED);
        return true;
    }
    setPermissionStatus(status);
    return false;
  }, []);

  const processImageUri = async (uri: string) => {
    try {
      setState('processing');
      setError(null);
      
      const result = await aiService.processImage(uri);
      
      setProcessedMeal(result);
      setState('success');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('common.errors.processingFailed');
      setError(errorMessage);
      setState('error');
    }
  };

  const pickImage = useCallback(async () => {
    try {
      setState('picking');
      setError(null);
      
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: true, // Allow cropping/rotating
        quality: 0.8,
        base64: false, // We upload file by URI
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        await processImageUri(result.assets[0].uri);
      } else {
        setState('idle');
      }
    } catch {
      setError(t('common.errors.unknown'));
      setState('error');
    }
  }, [t]);

  const takePhoto = useCallback(async () => {
    try {
      setState('picking');
      setError(null);
      
      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ['images'],
        allowsEditing: true,
        quality: 0.8,
        base64: false,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        await processImageUri(result.assets[0].uri);
      } else {
        setState('idle');
      }
    } catch {
        setError(t('common.errors.unknown'));
        setState('error');
    }
  }, [t]);

  const reset = useCallback(() => {
    setState('idle');
    setProcessedMeal(null);
    setError(null);
  }, []);

  return {
    state,
    processedMeal,
    error,
    pickImage,
    takePhoto,
    reset,
    permissionStatus,
    requestPermission,
  };
}
