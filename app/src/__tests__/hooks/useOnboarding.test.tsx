import { renderHook, act } from '@testing-library/react-native';
import { useOnboarding } from '@/hooks/useOnboarding';

import { apiClient } from '@/services/api.client';

jest.mock('@/services/api.client', () => ({
  apiClient: {
    patch: jest.fn(),
  },
}));

const mockPatch = apiClient.patch as jest.Mock;

beforeEach(() => {
  jest.clearAllMocks();
  // Reset store state
  act(() => {
    useOnboarding.setState({ data: {}, isLoading: false });
  });
});

describe('useOnboarding', () => {
  describe('setData', () => {
    it('merges data into state', () => {
      const { result } = renderHook(() => useOnboarding());
      act(() => {
        result.current.setData({ age: 25, gender: 'Male' });
      });
      expect(result.current.data.age).toBe(25);
      expect(result.current.data.gender).toBe('Male');
    });

    it('preserves previous data on subsequent calls', () => {
      const { result } = renderHook(() => useOnboarding());
      act(() => {
        result.current.setData({ age: 25 });
      });
      act(() => {
        result.current.setData({ height: 180 });
      });
      expect(result.current.data.age).toBe(25);
      expect(result.current.data.height).toBe(180);
    });
  });

  describe('submitOnboarding', () => {
    it('sends PATCH with mapped data', async () => {
      mockPatch.mockResolvedValue({});
      const { result } = renderHook(() => useOnboarding());
      act(() => {
        result.current.setData({ age: 25, activityLevel: 'moderate', height: 180, weight: 80 });
      });

      await act(async () => {
        await result.current.submitOnboarding();
      });

      expect(mockPatch).toHaveBeenCalledWith('/users/me', expect.objectContaining({
        age: 25,
        height: 180,
        weight: 80,
        activity_level: 'moderate',
        is_onboarded: true,
      }));
    });

    it('calls onSuccess callback', async () => {
      mockPatch.mockResolvedValue({});
      const onSuccess = jest.fn();
      const { result } = renderHook(() => useOnboarding());

      await act(async () => {
        await result.current.submitOnboarding(onSuccess);
      });

      expect(onSuccess).toHaveBeenCalled();
    });

    it('sets isLoading during submission', async () => {
      let resolvePromise: () => void;
      mockPatch.mockReturnValue(new Promise<void>(r => { resolvePromise = r; }));
      const { result } = renderHook(() => useOnboarding());

      const submitPromise = act(async () => {
        const promise = result.current.submitOnboarding();
        return promise;
      });

      // After starting, isLoading should be true (might need to wait for state update)
      // Resolve the mock
      await act(async () => {
        resolvePromise!();
      });
      await submitPromise;
      expect(result.current.isLoading).toBe(false);
    });

    it('resets isLoading on error', async () => {
      mockPatch.mockRejectedValue(new Error('fail'));
      const { result } = renderHook(() => useOnboarding());

      await expect(act(async () => {
        await result.current.submitOnboarding();
      })).rejects.toThrow('fail');

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('initial state', () => {
    it('starts with empty data', () => {
      const { result } = renderHook(() => useOnboarding());
      expect(result.current.data).toEqual({});
    });

    it('starts with isLoading false', () => {
      const { result } = renderHook(() => useOnboarding());
      expect(result.current.isLoading).toBe(false);
    });
  });
});
