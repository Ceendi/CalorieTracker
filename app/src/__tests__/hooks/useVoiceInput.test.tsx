import { renderHook, act } from '@testing-library/react-native';

import { useVoiceInput } from '@/hooks/useVoiceInput';
import { aiService } from '@/services/ai.service';

const mockStartRecording = jest.fn();
const mockStopRecording = jest.fn();
const mockRequestPermission = jest.fn(async () => true);

jest.mock('@/hooks/useAudioRecorder', () => ({
  useAudioRecorder: () => ({
    startRecording: mockStartRecording,
    stopRecording: mockStopRecording,
    isRecording: false,
    recordingDuration: 0,
    permissionStatus: 'granted' as const,
    requestPermission: mockRequestPermission,
    error: null,
  }),
}));

jest.mock('@/hooks/useLanguage', () => ({
  useLanguage: () => ({ t: (k: string) => k, language: 'en', setLanguage: jest.fn() }),
}));

jest.mock('@/services/ai.service', () => ({
  aiService: {
    processAudio: jest.fn(),
  },
}));

const mockMeal = {
  meal_type: 'breakfast',
  items: [{ name: 'Eggs', quantity_grams: 100, kcal: 155, protein: 13, fat: 11, carbs: 1.1, confidence: 0.9, status: 'matched', product_id: null, quantity_unit_value: 100, unit_matched: 'g' }],
  raw_transcription: 'two eggs',
  processing_time_ms: 300,
};

describe('useVoiceInput', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('starts in idle state', () => {
    const { result } = renderHook(() => useVoiceInput());
    expect(result.current.state).toBe('idle');
    expect(result.current.processedMeal).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('startRecording transitions to recording state', async () => {
    const { result } = renderHook(() => useVoiceInput());
    await act(async () => { await result.current.startRecording(); });
    expect(mockStartRecording).toHaveBeenCalled();
    expect(result.current.state).toBe('recording');
  });

  it('startRecording sets error state on failure', async () => {
    mockStartRecording.mockRejectedValueOnce(new Error('mic fail'));
    const { result } = renderHook(() => useVoiceInput());
    await act(async () => { await result.current.startRecording(); });
    expect(result.current.state).toBe('error');
    expect(result.current.error).toBeTruthy();
  });

  it('stopAndProcess returns processed meal', async () => {
    mockStopRecording.mockResolvedValue('file://recording.m4a');
    (aiService.processAudio as jest.Mock).mockResolvedValue(mockMeal);

    const { result } = renderHook(() => useVoiceInput());

    // Start recording first
    await act(async () => { await result.current.startRecording(); });

    let meal: any;
    await act(async () => { meal = await result.current.stopAndProcess(); });

    expect(result.current.state).toBe('success');
    expect(result.current.processedMeal).toEqual(mockMeal);
    expect(meal).toEqual(mockMeal);
  });

  it('stopAndProcess handles no audio URI', async () => {
    mockStopRecording.mockResolvedValue(null);

    const { result } = renderHook(() => useVoiceInput());
    await act(async () => { await result.current.startRecording(); });

    let meal: any;
    await act(async () => { meal = await result.current.stopAndProcess(); });

    expect(result.current.state).toBe('error');
    expect(meal).toBeNull();
  });

  it('stopAndProcess handles processing error', async () => {
    mockStopRecording.mockResolvedValue('file://recording.m4a');
    (aiService.processAudio as jest.Mock).mockRejectedValue(new Error('server error'));

    const { result } = renderHook(() => useVoiceInput());
    await act(async () => { await result.current.startRecording(); });

    let meal: any;
    await act(async () => { meal = await result.current.stopAndProcess(); });

    expect(result.current.state).toBe('error');
    expect(result.current.error).toBe('server error');
    expect(meal).toBeNull();
  });

  it('cancelRecording resets to idle', async () => {
    const { result } = renderHook(() => useVoiceInput());
    await act(async () => { await result.current.startRecording(); });

    await act(async () => { await result.current.cancelRecording(); });
    expect(result.current.state).toBe('idle');
    expect(result.current.error).toBeNull();
  });

  it('reset clears all state', async () => {
    mockStopRecording.mockResolvedValue('file://recording.m4a');
    (aiService.processAudio as jest.Mock).mockResolvedValue(mockMeal);

    const { result } = renderHook(() => useVoiceInput());
    await act(async () => { await result.current.startRecording(); });
    await act(async () => { await result.current.stopAndProcess(); });

    expect(result.current.processedMeal).not.toBeNull();

    act(() => { result.current.reset(); });
    expect(result.current.state).toBe('idle');
    expect(result.current.processedMeal).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('provides permission info', () => {
    const { result } = renderHook(() => useVoiceInput());
    expect(result.current.permissionStatus).toBe('granted');
    expect(typeof result.current.requestPermission).toBe('function');
  });
});
