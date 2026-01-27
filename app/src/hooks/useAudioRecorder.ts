import { useState, useEffect, useCallback, useRef } from 'react';
import {
  useAudioRecorder as useExpoAudioRecorder,
  AudioModule,
  RecordingPresets,
} from 'expo-audio';
import { useLanguage } from './useLanguage';

export type RecordingStatus = 'idle' | 'recording' | 'stopping';
export type PermissionStatus = 'undetermined' | 'granted' | 'denied';

interface UseAudioRecorderResult {
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<string | null>;
  isRecording: boolean;
  recordingStatus: RecordingStatus;
  recordingDuration: number;
  permissionStatus: PermissionStatus;
  requestPermission: () => Promise<boolean>;
  error: string | null;
}

export function useAudioRecorder(): UseAudioRecorderResult {
  const { t } = useLanguage();
  const [recordingStatus, setRecordingStatus] = useState<RecordingStatus>('idle');
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [permissionStatus, setPermissionStatus] = useState<PermissionStatus>('undetermined');
  const [error, setError] = useState<string | null>(null);
  const durationIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);

  const audioRecorder = useExpoAudioRecorder(RecordingPresets.HIGH_QUALITY);

  useEffect(() => {
    checkPermission();
    return () => {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
    };
  }, []);

  const checkPermission = async () => {
    try {
      const status = await AudioModule.getRecordingPermissionsAsync();
      setPermissionStatus(status.granted ? 'granted' : 'undetermined');
    } catch (err) {
      console.error('Failed to check audio permission:', err);
    }
  };

  const requestPermission = useCallback(async (): Promise<boolean> => {
    try {
      const status = await AudioModule.requestRecordingPermissionsAsync();
      const granted = status.granted;
      setPermissionStatus(granted ? 'granted' : 'denied');
      return granted;
    } catch (err) {
      console.error('Failed to request audio permission:', err);
      setError(t('common.errors.micAccess'));
      return false;
    }
  }, [t]);

  const startRecording = useCallback(async () => {
    try {
      setError(null);

      if (permissionStatus !== 'granted') {
        const granted = await requestPermission();
        if (!granted) {
          setError(t('addFood.voiceButton.noPermission'));
          return;
        }
      }

      await AudioModule.setAudioModeAsync({
        allowsRecording: true,
        playsInSilentMode: true,
      });

      await audioRecorder.prepareToRecordAsync();
      audioRecorder.record();
      
      setRecordingStatus('recording');
      setRecordingDuration(0);
      startTimeRef.current = Date.now();

      durationIntervalRef.current = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000);
        setRecordingDuration(elapsed);
      }, 100);

    } catch (err) {
      console.error('Failed to start recording:', err);
      setError(t('common.errors.startRecording'));
      setRecordingStatus('idle');
    }
  }, [permissionStatus, requestPermission, t, audioRecorder]);

  const stopRecording = useCallback(async (): Promise<string | null> => {
    if (recordingStatus !== 'recording') {
      return null;
    }

    try {
      setRecordingStatus('stopping');

      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
        durationIntervalRef.current = null;
      }

      await audioRecorder.stop();
      
      const uri = audioRecorder.uri;

      await AudioModule.setAudioModeAsync({
        allowsRecording: false,
        playsInSilentMode: false,
      });

      setRecordingStatus('idle');

      return uri || null;

    } catch (err) {
      console.error('Failed to stop recording:', err);
      setError(t('common.errors.unknown'));
      setRecordingStatus('idle');
      return null;
    }
  }, [recordingStatus, t, audioRecorder]);

  return {
    startRecording,
    stopRecording,
    isRecording: recordingStatus === 'recording',
    recordingStatus,
    recordingDuration,
    permissionStatus,
    requestPermission,
    error,
  };
}
