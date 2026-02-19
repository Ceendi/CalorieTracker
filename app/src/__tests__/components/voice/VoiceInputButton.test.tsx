import { render, fireEvent, act, waitFor } from '@testing-library/react-native';

import { VoiceInputButton } from '@/components/voice/VoiceInputButton';

const mockStartRecording = jest.fn();
const mockStopAndProcess = jest.fn();
const mockCancelRecording = jest.fn();
const mockReset = jest.fn();
const mockRequestPermission = jest.fn(async () => true);

let mockState = 'idle';
let mockPermissionStatus = 'granted';
let mockError: string | null = null;
let mockRecordingDuration = 0;
let mockProcessedMeal: any = null;

jest.mock('@/hooks/useVoiceInput', () => ({
  useVoiceInput: () => ({
    state: mockState,
    recordingDuration: mockRecordingDuration,
    processedMeal: mockProcessedMeal,
    error: mockError,
    startRecording: mockStartRecording,
    stopAndProcess: mockStopAndProcess,
    cancelRecording: mockCancelRecording,
    reset: mockReset,
    permissionStatus: mockPermissionStatus,
    requestPermission: mockRequestPermission,
  }),
}));

jest.mock('@/hooks/useLanguage', () => ({
  useLanguage: () => ({ t: (k: string) => k, language: 'en', setLanguage: jest.fn() }),
}));
jest.mock('@/hooks/useColorScheme', () => ({
  useColorScheme: () => ({ colorScheme: 'light', toggleColorScheme: jest.fn(), setColorScheme: jest.fn(), isLoaded: true }),
}));
jest.mock('@/constants/theme', () => ({
  Colors: {
    light: { tint: '#6366f1', text: '#020617', error: '#ef4444', warning: '#f59e0b', success: '#22c55e' },
    dark: { tint: '#818cf8', text: '#f8fafc', error: '#f87171', warning: '#fbbf24', success: '#4ade80' },
  },
}));
jest.mock('@/components/ui/IconSymbol', () => ({
  IconSymbol: 'IconSymbol',
  IconSymbolName: {},
}));

describe('VoiceInputButton', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    mockState = 'idle';
    mockPermissionStatus = 'granted';
    mockError = null;
    mockRecordingDuration = 0;
    mockProcessedMeal = null;
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('renders in idle state with record label', () => {
    const { getByText } = render(<VoiceInputButton />);
    expect(getByText('addFood.voiceButton.record')).toBeTruthy();
  });

  it('shows hold hint in idle state', () => {
    const { getByText } = render(<VoiceInputButton />);
    expect(getByText('addFood.voiceButton.hold')).toBeTruthy();
  });

  it('shows recording duration in recording state', () => {
    mockState = 'recording';
    mockRecordingDuration = 65;
    const { getByText } = render(<VoiceInputButton />);
    expect(getByText('1:05')).toBeTruthy();
  });

  it('shows release hint in recording state', () => {
    mockState = 'recording';
    const { getByText } = render(<VoiceInputButton />);
    expect(getByText('addFood.voiceButton.release')).toBeTruthy();
  });

  it('shows processing label', () => {
    mockState = 'processing';
    const { getByText } = render(<VoiceInputButton />);
    expect(getByText('addFood.voiceButton.processing')).toBeTruthy();
  });

  it('shows success label', () => {
    mockState = 'success';
    const { getByText } = render(<VoiceInputButton />);
    expect(getByText('addFood.voiceButton.success')).toBeTruthy();
  });

  it('shows error label', () => {
    mockState = 'error';
    mockError = 'Something went wrong';
    const { getByText } = render(<VoiceInputButton />);
    expect(getByText('addFood.voiceButton.error')).toBeTruthy();
  });

  it('shows permission denied message', () => {
    mockPermissionStatus = 'denied';
    const { getByText } = render(<VoiceInputButton />);
    expect(getByText('addFood.voiceButton.permission')).toBeTruthy();
  });

  it('disables button in processing state', () => {
    mockState = 'processing';
    const { getByRole } = render(<VoiceInputButton />);
    const button = getByRole('button');
    expect(button.props.accessibilityState.disabled).toBe(true);
  });

  it('calls onMealProcessed when success state with meal', () => {
    const onMealProcessed = jest.fn();
    mockState = 'success';
    mockProcessedMeal = { meal_type: 'lunch', items: [] };
    render(<VoiceInputButton onMealProcessed={onMealProcessed} />);
    // The useEffect should fire
    expect(onMealProcessed).toHaveBeenCalledWith(mockProcessedMeal);
  });

  it('calls onError when error state', () => {
    const onError = jest.fn();
    mockState = 'error';
    mockError = 'test error';
    render(<VoiceInputButton onError={onError} />);
    expect(onError).toHaveBeenCalledWith('test error');
  });

  it('formats duration correctly for various values', () => {
    mockState = 'recording';
    mockRecordingDuration = 0;
    const { getByText, rerender } = render(<VoiceInputButton />);
    expect(getByText('0:00')).toBeTruthy();

    mockRecordingDuration = 9;
    rerender(<VoiceInputButton />);
    expect(getByText('0:09')).toBeTruthy();

    mockRecordingDuration = 120;
    rerender(<VoiceInputButton />);
    expect(getByText('2:00')).toBeTruthy();
  });
});
