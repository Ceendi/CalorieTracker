import { renderHook, act } from '@testing-library/react-native';

import { usePhotoInput } from '@/hooks/usePhotoInput';
import * as ImagePicker from 'expo-image-picker';
import { aiService } from '@/services/ai.service';

jest.mock('@/hooks/useLanguage', () => ({
  useLanguage: () => ({ t: (k: string) => k, language: 'en', setLanguage: jest.fn() }),
}));

jest.mock('expo-image-picker', () => ({
  launchImageLibraryAsync: jest.fn(),
  launchCameraAsync: jest.fn(),
  requestMediaLibraryPermissionsAsync: jest.fn(async () => ({ status: 'granted' })),
  requestCameraPermissionsAsync: jest.fn(async () => ({ status: 'granted' })),
  PermissionStatus: { GRANTED: 'granted', DENIED: 'denied', UNDETERMINED: 'undetermined' },
}));

jest.mock('@/services/ai.service', () => ({
  aiService: {
    processImage: jest.fn(),
  },
}));

const mockMeal = {
  meal_type: 'lunch',
  items: [{ name: 'Salad', quantity_grams: 200, kcal: 80, protein: 3, fat: 1, carbs: 10, confidence: 0.9, status: 'matched', product_id: null, quantity_unit_value: 200, unit_matched: 'g' }],
  raw_transcription: '',
  processing_time_ms: 100,
};

describe('usePhotoInput', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('starts in idle state', () => {
    const { result } = renderHook(() => usePhotoInput());
    expect(result.current.state).toBe('idle');
    expect(result.current.processedMeal).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('requestPermission sets granted status', async () => {
    const { result } = renderHook(() => usePhotoInput());
    let granted: boolean;
    await act(async () => {
      granted = await result.current.requestPermission();
    });
    expect(granted!).toBe(true);
    expect(result.current.permissionStatus).toBe('granted');
  });

  it('pickImage processes image on success', async () => {
    (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({
      canceled: false,
      assets: [{ uri: 'file://photo.jpg' }],
    });
    (aiService.processImage as jest.Mock).mockResolvedValue(mockMeal);

    const { result } = renderHook(() => usePhotoInput());
    await act(async () => { await result.current.pickImage(); });

    expect(result.current.state).toBe('success');
    expect(result.current.processedMeal).toEqual(mockMeal);
  });

  it('pickImage returns to idle when cancelled', async () => {
    (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({ canceled: true });

    const { result } = renderHook(() => usePhotoInput());
    await act(async () => { await result.current.pickImage(); });

    expect(result.current.state).toBe('idle');
    expect(result.current.processedMeal).toBeNull();
  });

  it('pickImage sets error state on processing failure', async () => {
    (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({
      canceled: false,
      assets: [{ uri: 'file://photo.jpg' }],
    });
    (aiService.processImage as jest.Mock).mockRejectedValue(new Error('API down'));

    const { result } = renderHook(() => usePhotoInput());
    await act(async () => { await result.current.pickImage(); });

    expect(result.current.state).toBe('error');
    expect(result.current.error).toBe('API down');
  });

  it('takePhoto processes camera image', async () => {
    (ImagePicker.launchCameraAsync as jest.Mock).mockResolvedValue({
      canceled: false,
      assets: [{ uri: 'file://camera.jpg' }],
    });
    (aiService.processImage as jest.Mock).mockResolvedValue(mockMeal);

    const { result } = renderHook(() => usePhotoInput());
    await act(async () => { await result.current.takePhoto(); });

    expect(result.current.state).toBe('success');
    expect(aiService.processImage).toHaveBeenCalledWith('file://camera.jpg');
  });

  it('takePhoto returns to idle when cancelled', async () => {
    (ImagePicker.launchCameraAsync as jest.Mock).mockResolvedValue({ canceled: true });

    const { result } = renderHook(() => usePhotoInput());
    await act(async () => { await result.current.takePhoto(); });

    expect(result.current.state).toBe('idle');
  });

  it('reset clears state', async () => {
    (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({
      canceled: false,
      assets: [{ uri: 'file://photo.jpg' }],
    });
    (aiService.processImage as jest.Mock).mockResolvedValue(mockMeal);

    const { result } = renderHook(() => usePhotoInput());
    await act(async () => { await result.current.pickImage(); });
    expect(result.current.state).toBe('success');

    act(() => { result.current.reset(); });
    expect(result.current.state).toBe('idle');
    expect(result.current.processedMeal).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('requestPermission returns false when denied', async () => {
    (ImagePicker.requestMediaLibraryPermissionsAsync as jest.Mock).mockResolvedValue({ status: 'denied' });
    (ImagePicker.requestCameraPermissionsAsync as jest.Mock).mockResolvedValue({ status: 'denied' });

    const { result } = renderHook(() => usePhotoInput());
    let granted: boolean;
    await act(async () => {
      granted = await result.current.requestPermission();
    });
    expect(granted!).toBe(false);
  });
});
