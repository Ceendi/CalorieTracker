import { renderHook } from '@testing-library/react-native';

import { useThemeColor } from '@/hooks/use-theme-color';
import { Colors } from '@/constants/theme';

// theme.ts imports Platform from react-native — mock the constants module
jest.mock('@/constants/theme', () => ({
  Colors: {
    light: {
      text: '#020617',
      background: '#f8fafc',
    },
    dark: {
      text: '#f8fafc',
      background: '#0f172a',
    },
  },
}));

const mockUseColorScheme = jest.fn();
jest.mock('@/hooks/useColorScheme', () => ({
  useColorScheme: (...args: any[]) => mockUseColorScheme(...args),
}));

describe('useThemeColor', () => {
  beforeEach(() => {
    mockUseColorScheme.mockReturnValue({
      colorScheme: 'light',
      toggleColorScheme: jest.fn(),
      setColorScheme: jest.fn(),
      isLoaded: true,
    });
  });

  it('returns color from Colors.light for light scheme', () => {
    const { result } = renderHook(() => useThemeColor({}, 'text'));
    expect(result.current).toBe(Colors.light.text);
  });

  it('returns color from Colors.dark for dark scheme', () => {
    mockUseColorScheme.mockReturnValue({
      colorScheme: 'dark',
      toggleColorScheme: jest.fn(),
      setColorScheme: jest.fn(),
      isLoaded: true,
    });
    const { result } = renderHook(() => useThemeColor({}, 'text'));
    expect(result.current).toBe(Colors.dark.text);
  });

  it('prefers prop color over theme color', () => {
    const { result } = renderHook(() => useThemeColor({ light: '#ff0000' }, 'text'));
    expect(result.current).toBe('#ff0000');
  });

  it('prefers dark prop when in dark mode', () => {
    mockUseColorScheme.mockReturnValue({
      colorScheme: 'dark',
      toggleColorScheme: jest.fn(),
      setColorScheme: jest.fn(),
      isLoaded: true,
    });
    const { result } = renderHook(() => useThemeColor({ dark: '#00ff00' }, 'background'));
    expect(result.current).toBe('#00ff00');
  });

  it('falls back to light when colorScheme is null', () => {
    mockUseColorScheme.mockReturnValue({
      colorScheme: null,
      toggleColorScheme: jest.fn(),
      setColorScheme: jest.fn(),
      isLoaded: true,
    });
    const { result } = renderHook(() => useThemeColor({}, 'background'));
    expect(result.current).toBe(Colors.light.background);
  });
});
