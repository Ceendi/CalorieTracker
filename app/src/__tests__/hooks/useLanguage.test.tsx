import { renderHook, act } from '@testing-library/react-native';

jest.mock('@/services/storage.service', () => ({
  storageService: {
    getLanguage: jest.fn(),
    setLanguage: jest.fn(),
  },
}));

jest.mock('expo-localization', () => ({
  getLocales: jest.fn(() => [{ languageCode: 'en' }]),
}));

import { useLanguage } from '@/hooks/useLanguage';
import { storageService } from '@/services/storage.service';

beforeEach(() => {
  jest.clearAllMocks();
});

describe('useLanguage', () => {
  it('provides t function', () => {
    const { result } = renderHook(() => useLanguage());
    expect(typeof result.current.t).toBe('function');
  });

  it('t returns key for unknown translations', () => {
    const { result } = renderHook(() => useLanguage());
    expect(result.current.t('nonexistent.key.here')).toBe('nonexistent.key.here');
  });

  it('t resolves known translation keys', () => {
    const { result } = renderHook(() => useLanguage());
    // 'auth.signIn' should resolve to a non-empty string in EN
    const value = result.current.t('auth.signIn');
    expect(value).toBeTruthy();
    expect(value).not.toBe('auth.signIn');
  });

  it('provides setLanguage', () => {
    const { result } = renderHook(() => useLanguage());
    expect(typeof result.current.setLanguage).toBe('function');
  });

  it('setLanguage updates language and persists', async () => {
    (storageService.setLanguage as jest.Mock).mockResolvedValue(undefined);
    const { result } = renderHook(() => useLanguage());

    await act(async () => {
      await result.current.setLanguage('pl');
    });

    expect(storageService.setLanguage).toHaveBeenCalledWith('pl');
    expect(result.current.language).toBe('pl');
  });

  it('t resolves Polish translations after switching', async () => {
    (storageService.setLanguage as jest.Mock).mockResolvedValue(undefined);
    const { result } = renderHook(() => useLanguage());

    await act(async () => {
      await result.current.setLanguage('pl');
    });

    const value = result.current.t('auth.signIn');
    expect(value).toBeTruthy();
  });

  it('has language property', () => {
    const { result } = renderHook(() => useLanguage());
    expect(['en', 'pl']).toContain(result.current.language);
  });
});
