import { renderHook, act, waitFor } from '@testing-library/react-native';

// expo-audio is already mocked in setup.tsx. We import it to configure per-test behavior.
jest.mock('@/hooks/useLanguage', () => ({
  useLanguage: () => ({ t: (k: string) => k, language: 'en', setLanguage: jest.fn() }),
}));

import { useAudioRecorder } from '@/hooks/useAudioRecorder';
import { useAudioRecorder as useExpoAudioRecorder, AudioModule } from 'expo-audio';

describe('useAudioRecorder', () => {
  const mockRecorder = {
    prepareToRecordAsync: jest.fn(),
    record: jest.fn(),
    stop: jest.fn(),
    uri: 'file://recording.m4a',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useExpoAudioRecorder as jest.Mock).mockReturnValue(mockRecorder);
    (AudioModule.getRecordingPermissionsAsync as jest.Mock).mockResolvedValue({ granted: true });
    (AudioModule.requestRecordingPermissionsAsync as jest.Mock).mockResolvedValue({ granted: true });
  });

  it('checks permission on mount and sets granted', async () => {
    const { result } = renderHook(() => useAudioRecorder());
    await waitFor(() => {
      expect(result.current.permissionStatus).toBe('granted');
    });
    expect(result.current.isRecording).toBe(false);
    expect(result.current.recordingStatus).toBe('idle');
  });

  it('requestPermission returns true when granted', async () => {
    const { result } = renderHook(() => useAudioRecorder());
    let granted: boolean;
    await act(async () => {
      granted = await result.current.requestPermission();
    });
    expect(granted!).toBe(true);
    expect(result.current.permissionStatus).toBe('granted');
  });

  it('requestPermission returns false when denied', async () => {
    (AudioModule.requestRecordingPermissionsAsync as jest.Mock).mockResolvedValueOnce({ granted: false });
    const { result } = renderHook(() => useAudioRecorder());
    let granted: boolean;
    await act(async () => {
      granted = await result.current.requestPermission();
    });
    expect(granted!).toBe(false);
    expect(result.current.permissionStatus).toBe('denied');
  });

  it('startRecording sets status to recording', async () => {
    const { result } = renderHook(() => useAudioRecorder());
    await waitFor(() => expect(result.current.permissionStatus).toBe('granted'));

    await act(async () => { await result.current.startRecording(); });
    expect(result.current.recordingStatus).toBe('recording');
    expect(result.current.isRecording).toBe(true);
    expect(mockRecorder.prepareToRecordAsync).toHaveBeenCalled();
    expect(mockRecorder.record).toHaveBeenCalled();
  });

  it('stopRecording returns uri and resets status', async () => {
    const { result } = renderHook(() => useAudioRecorder());
    await waitFor(() => expect(result.current.permissionStatus).toBe('granted'));
    await act(async () => { await result.current.startRecording(); });

    let uri: string | null;
    await act(async () => { uri = await result.current.stopRecording(); });
    expect(uri!).toBe('file://recording.m4a');
    expect(result.current.recordingStatus).toBe('idle');
    expect(mockRecorder.stop).toHaveBeenCalled();
  });

  it('stopRecording returns null when not recording', async () => {
    const { result } = renderHook(() => useAudioRecorder());
    let uri: string | null;
    await act(async () => { uri = await result.current.stopRecording(); });
    expect(uri!).toBeNull();
  });

  it('handles startRecording error', async () => {
    mockRecorder.prepareToRecordAsync.mockRejectedValueOnce(new Error('mic fail'));
    const { result } = renderHook(() => useAudioRecorder());
    await waitFor(() => expect(result.current.permissionStatus).toBe('granted'));

    await act(async () => { await result.current.startRecording(); });
    expect(result.current.recordingStatus).toBe('idle');
    expect(result.current.error).toBe('common.errors.startRecording');
  });

  it('sets audio mode before recording', async () => {
    const { result } = renderHook(() => useAudioRecorder());
    await waitFor(() => expect(result.current.permissionStatus).toBe('granted'));
    await act(async () => { await result.current.startRecording(); });
    expect(AudioModule.setAudioModeAsync).toHaveBeenCalledWith(
      expect.objectContaining({ allowsRecording: true }),
    );
  });
});
