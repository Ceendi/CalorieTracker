import { renderHook, act } from '@testing-library/react-native';
import { useVoiceMealLogic } from '@/hooks/useVoiceMealLogic';
import { ProcessedMeal } from '@/types/ai';
import { FoodProduct } from '@/types/food';

// Mock only the Keyboard module that the hook uses (avoids loading native bridge)
jest.mock('react-native/Libraries/Components/Keyboard/Keyboard', () => ({
  default: { dismiss: jest.fn(), addListener: jest.fn(() => ({ remove: jest.fn() })) },
  dismiss: jest.fn(),
  addListener: jest.fn(() => ({ remove: jest.fn() })),
}));

const mockT = (key: string) => key;

const createMeal = (overrides: Partial<ProcessedMeal> = {}): ProcessedMeal => ({
  meal_type: 'breakfast',
  items: [
    {
      product_id: null,
      name: 'Chicken',
      quantity_grams: 200,
      quantity_unit_value: 200,
      unit_matched: 'g',
      kcal: 330,
      protein: 62,
      fat: 7.2,
      carbs: 0,
      confidence: 0.95,
      status: 'matched',
    },
  ],
  raw_transcription: 'chicken 200g',
  processing_time_ms: 500,
  ...overrides,
});

describe('useVoiceMealLogic', () => {
  // IMPORTANT: initialMeal must be a stable reference to avoid infinite re-renders.
  // The hook has a useEffect([initialMeal]) that calls setLocalMeal, so creating
  // a new object on every render causes an infinite loop.

  describe('totals', () => {
    it('sums item macros', () => {
      const meal = createMeal();
      const { result } = renderHook(() => useVoiceMealLogic({ initialMeal: meal, t: mockT }));
      expect(result.current.totals.kcal).toBe(330);
      expect(result.current.totals.protein).toBe(62);
    });

    it('returns zeros for empty items', () => {
      const meal = createMeal({ items: [] });
      const { result } = renderHook(() => useVoiceMealLogic({ initialMeal: meal, t: mockT }));
      expect(result.current.totals).toEqual({ kcal: 0, protein: 0, fat: 0, carbs: 0 });
    });

    it('returns zeros for null meal', () => {
      const { result } = renderHook(() => useVoiceMealLogic({ initialMeal: null, t: mockT }));
      expect(result.current.totals).toEqual({ kcal: 0, protein: 0, fat: 0, carbs: 0 });
    });
  });

  describe('updateQuantity', () => {
    it('recalculates macros when quantity changes', () => {
      const meal = createMeal();
      const { result } = renderHook(() => useVoiceMealLogic({ initialMeal: meal, t: mockT }));
      act(() => {
        result.current.updateQuantity(0, 100); // halve from 200g to 100g
      });
      expect(result.current.localMeal?.items[0].quantity_grams).toBe(100);
      expect(result.current.localMeal?.items[0].kcal).toBeCloseTo(165, 0);
    });

    it('handles unit change', () => {
      const meal = createMeal();
      const { result } = renderHook(() => useVoiceMealLogic({ initialMeal: meal, t: mockT }));
      act(() => {
        result.current.updateQuantity(0, 2, { grams: 100, label: 'slice' });
      });
      expect(result.current.localMeal?.items[0].quantity_grams).toBe(200);
      expect(result.current.localMeal?.items[0].unit_matched).toBe('slice');
    });

    it('sets unit to g when null unit passed', () => {
      const meal = createMeal();
      const { result } = renderHook(() => useVoiceMealLogic({ initialMeal: meal, t: mockT }));
      act(() => {
        result.current.updateQuantity(0, 150, null);
      });
      expect(result.current.localMeal?.items[0].unit_matched).toBe('g');
      expect(result.current.localMeal?.items[0].quantity_grams).toBe(150);
    });

    it('does nothing when localMeal is null', () => {
      const { result } = renderHook(() => useVoiceMealLogic({ initialMeal: null, t: mockT }));
      act(() => {
        result.current.updateQuantity(0, 100);
      });
      expect(result.current.localMeal).toBeNull();
    });
  });

  describe('removeItem', () => {
    it('removes item at index', () => {
      const meal = createMeal({
        items: [
          { ...createMeal().items[0], name: 'A' },
          { ...createMeal().items[0], name: 'B' },
        ],
      });
      const { result } = renderHook(() => useVoiceMealLogic({ initialMeal: meal, t: mockT }));
      act(() => {
        result.current.removeItem(0);
      });
      expect(result.current.localMeal?.items).toHaveLength(1);
      expect(result.current.localMeal?.items[0].name).toBe('B');
    });
  });

  describe('cycleMealType', () => {
    it('cycles to next meal type', () => {
      const meal = createMeal({ meal_type: 'breakfast' });
      const { result } = renderHook(() => useVoiceMealLogic({ initialMeal: meal, t: mockT }));
      act(() => {
        result.current.cycleMealType();
      });
      expect(result.current.localMeal?.meal_type).toBe('second_breakfast');
    });

    it('wraps around from snack to breakfast', () => {
      const meal = createMeal({ meal_type: 'snack' });
      const { result } = renderHook(() => useVoiceMealLogic({ initialMeal: meal, t: mockT }));
      act(() => {
        result.current.cycleMealType();
      });
      expect(result.current.localMeal?.meal_type).toBe('breakfast');
    });
  });

  describe('getMealTypeLabel', () => {
    it('returns translation key for known types', () => {
      const meal = createMeal();
      const { result } = renderHook(() => useVoiceMealLogic({ initialMeal: meal, t: mockT }));
      expect(result.current.getMealTypeLabel('breakfast')).toBe('meals.breakfast');
      expect(result.current.getMealTypeLabel('lunch')).toBe('meals.lunch');
    });

    it('returns the type itself for unknown types', () => {
      const meal = createMeal();
      const { result } = renderHook(() => useVoiceMealLogic({ initialMeal: meal, t: mockT }));
      expect(result.current.getMealTypeLabel('brunch')).toBe('brunch');
    });

    it('maps Polish meal types', () => {
      const meal = createMeal();
      const { result } = renderHook(() => useVoiceMealLogic({ initialMeal: meal, t: mockT }));
      expect(result.current.getMealTypeLabel('śniadanie')).toBe('meals.breakfast');
      expect(result.current.getMealTypeLabel('obiad')).toBe('meals.lunch');
    });
  });

  describe('addManualItem', () => {
    it('adds product as new item', () => {
      const meal = createMeal();
      const { result } = renderHook(() => useVoiceMealLogic({ initialMeal: meal, t: mockT }));
      const product: FoodProduct = {
        id: 'prod-123',
        name: 'Rice',
        nutrition: { calories_per_100g: 130, protein_per_100g: 2.7, fat_per_100g: 0.3, carbs_per_100g: 28 },
      };
      act(() => {
        result.current.addManualItem(product);
      });
      expect(result.current.localMeal?.items).toHaveLength(2);
      const added = result.current.localMeal?.items[1];
      expect(added?.name).toBe('Rice');
      expect(added?.quantity_grams).toBe(100);
      expect(added?.kcal).toBe(130);
    });
  });
});
