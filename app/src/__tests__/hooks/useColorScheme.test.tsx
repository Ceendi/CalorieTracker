import { renderHook, act, waitFor } from '@testing-library/react-native';

let mockScheme = 'light';
const mockSetColorScheme = jest.fn((s: string) => { mockScheme = s; });

jest.mock('nativewind', () => ({
  useColorScheme: jest.fn(() => ({
    colorScheme: mockScheme,
    setColorScheme: mockSetColorScheme,
    toggleColorScheme: jest.fn(),
  })),
}));

jest.mock('@/services/storage.service', () => ({
  storageService: {
    getTheme: jest.fn(async () => null),
    setTheme: jest.fn(async () => {}),
  },
}));

import { useColorScheme } from '@/hooks/useColorScheme';
import { storageService } from '@/services/storage.service';

describe('useColorScheme', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockScheme = 'light';
  });

  it('provides colorScheme', () => {
    const { result } = renderHook(() => useColorScheme());
    expect(result.current.colorScheme).toBe('light');
  });

  it('loads saved theme on mount', async () => {
    (storageService.getTheme as jest.Mock).mockResolvedValue('dark');
    const { result } = renderHook(() => useColorScheme());
    await waitFor(() => {
      expect(result.current.isLoaded).toBe(true);
    });
    expect(storageService.getTheme).toHaveBeenCalled();
    expect(mockSetColorScheme).toHaveBeenCalledWith('dark');
  });

  it('toggleColorScheme persists new scheme', async () => {
    mockScheme = 'light';
    const { result } = renderHook(() => useColorScheme());
    await act(async () => {
      await result.current.toggleColorScheme();
    });
    // light → dark
    expect(storageService.setTheme).toHaveBeenCalledWith('dark');
    expect(mockSetColorScheme).toHaveBeenCalledWith('dark');
  });

  it('setColorScheme persists the value', async () => {
    const { result } = renderHook(() => useColorScheme());
    await act(async () => {
      await result.current.setColorScheme('dark');
    });
    expect(storageService.setTheme).toHaveBeenCalledWith('dark');
    expect(mockSetColorScheme).toHaveBeenCalledWith('dark');
  });

  it('isLoaded becomes true after loading', async () => {
    (storageService.getTheme as jest.Mock).mockResolvedValue(null);
    const { result } = renderHook(() => useColorScheme());
    await waitFor(() => {
      expect(result.current.isLoaded).toBe(true);
    });
  });

  it('handles getTheme failure gracefully', async () => {
    (storageService.getTheme as jest.Mock).mockRejectedValue(new Error('fail'));
    const { result } = renderHook(() => useColorScheme());
    await waitFor(() => {
      expect(result.current.isLoaded).toBe(true);
    });
  });
});
