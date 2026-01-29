import { useState, useCallback } from 'react';
import { useAudioRecorder } from './useAudioRecorder';
import { useLanguage } from './useLanguage';
import { aiService } from '@/services/ai.service';
import { ProcessedMeal, ProcessedFoodItem } from '@/types/ai';

export type VoiceInputState = 
  | 'idle'
  | 'recording'
  | 'processing'
  | 'success'
  | 'error';

interface UseVoiceInputResult {
  state: VoiceInputState;
  recordingDuration: number;
  processedMeal: ProcessedMeal | null;
  error: string | null;
  
  startRecording: () => Promise<void>;
  stopAndProcess: () => Promise<ProcessedMeal | null>;
  cancelRecording: () => Promise<void>;
  reset: () => void;
  
  permissionStatus: 'undetermined' | 'granted' | 'denied';
  requestPermission: () => Promise<boolean>;
}

export function useVoiceInput(): UseVoiceInputResult {
  const { t } = useLanguage();
  const {
    startRecording: startAudioRecording,
    stopRecording: stopAudioRecording,
    isRecording,
    recordingDuration,
    permissionStatus,
    requestPermission,
    error: recorderError,
  } = useAudioRecorder();

  const [state, setState] = useState<VoiceInputState>('idle');
  const [processedMeal, setProcessedMeal] = useState<ProcessedMeal | null>(null);
  const [error, setError] = useState<string | null>(null);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      setProcessedMeal(null);
      await startAudioRecording();
      setState('recording');
    } catch (err) {
      setError(recorderError || t('common.errors.startRecording'));
      setState('error');
    }
  }, [startAudioRecording, recorderError, t]);

  const stopAndProcess = useCallback(async (): Promise<ProcessedMeal | null> => {
    try {
      const audioUri = await stopAudioRecording();
      
      if (!audioUri) {
        throw new Error(t('common.errors.noRecording'));
      }

      setState('processing');
      
      const result = await aiService.processAudio(audioUri);
      
      setProcessedMeal(result);
      setState('success');
      
      return result;
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('common.errors.processingFailed');
      setError(errorMessage);
      setState('error');
      return null;
    }
  }, [stopAudioRecording, t]);

  const cancelRecording = useCallback(async () => {
    try {
      await stopAudioRecording();
    } catch (err) {
      // ignore errors during cancel
    }
    setState('idle');
    setError(null);
  }, [stopAudioRecording]);

  const reset = useCallback(() => {
    setState('idle');
    setProcessedMeal(null);
    setError(null);
  }, []);

  return {
    state: isRecording ? 'recording' : state,
    recordingDuration,
    processedMeal,
    error: error || recorderError,
    startRecording,
    stopAndProcess,
    cancelRecording,
    reset,
    permissionStatus,
    requestPermission,
  };
}

export type { ProcessedMeal, ProcessedFoodItem };
