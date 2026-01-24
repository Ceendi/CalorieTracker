import { useState, useEffect, useRef, useCallback } from 'react';
import { Audio } from 'expo-av';
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
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [recordingStatus, setRecordingStatus] = useState<RecordingStatus>('idle');
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [permissionStatus, setPermissionStatus] = useState<PermissionStatus>('undetermined');
  const [error, setError] = useState<string | null>(null);
  
  const durationInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    checkPermission();
    return () => {
      if (durationInterval.current) {
        clearInterval(durationInterval.current);
      }
    };
  }, []);

  const checkPermission = async () => {
    try {
      const { status } = await Audio.getPermissionsAsync();
      setPermissionStatus(status === 'granted' ? 'granted' : 'undetermined');
    } catch (err) {
      console.error('Failed to check audio permission:', err);
    }
  };

  const requestPermission = useCallback(async (): Promise<boolean> => {
    try {
      const { status } = await Audio.requestPermissionsAsync();
      const granted = status === 'granted';
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

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
        staysActiveInBackground: false,
        shouldDuckAndroid: true,
      });

      const { recording: newRecording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY,
        (status) => {
          if (status.isRecording) {
            setRecordingDuration(Math.floor(status.durationMillis / 1000));
          }
        },
        100
      );

      setRecording(newRecording);
      setRecordingStatus('recording');
      setRecordingDuration(0);

      durationInterval.current = setInterval(() => {
        setRecordingDuration((prev) => prev + 1);
      }, 1000);

    } catch (err) {
      console.error('Failed to start recording:', err);
      setError(t('common.errors.startRecording'));
      setRecordingStatus('idle');
    }
  }, [permissionStatus, requestPermission, t]);

  const stopRecording = useCallback(async (): Promise<string | null> => {
    if (!recording) {
      return null;
    }

    try {
      setRecordingStatus('stopping');
      
      if (durationInterval.current) {
        clearInterval(durationInterval.current);
        durationInterval.current = null;
      }

      await recording.stopAndUnloadAsync();
      
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
        playsInSilentModeIOS: true,
      });

      const uri = recording.getURI();
      
      setRecording(null);
      setRecordingStatus('idle');
      
      return uri;
      
    } catch (err) {
      console.error('Failed to stop recording:', err);
      setError(t('common.errors.unknown'));
      setRecordingStatus('idle');
      return null;
    }
  }, [recording, t]);

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
