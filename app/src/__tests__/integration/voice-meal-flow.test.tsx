import { renderHook, act } from '@testing-library/react-native';

jest.mock('@/hooks/useLanguage', () => ({
  useLanguage: () => ({ t: (k: string) => k, language: 'en', setLanguage: jest.fn() }),
}));

jest.mock('react-native/Libraries/Components/Keyboard/Keyboard', () => ({
  default: { dismiss: jest.fn(), addListener: jest.fn(() => ({ remove: jest.fn() })) },
  dismiss: jest.fn(),
  addListener: jest.fn(() => ({ remove: jest.fn() })),
}));

import { useVoiceMealLogic } from '@/hooks/useVoiceMealLogic';
import { ProcessedMeal, ProcessedFoodItem } from '@/types/ai';

const mockT = (k: string) => k;

const createItem = (overrides?: Partial<ProcessedFoodItem>): ProcessedFoodItem => ({
  product_id: 1,
  name: 'Chicken',
  quantity_grams: 200,
  kcal: 330,
  protein: 62,
  fat: 7.2,
  carbs: 0,
  confidence: 0.95,
  unit_matched: 'g',
  quantity_unit_value: 200,
  status: 'matched',
  ...overrides,
});

const createMeal = (items?: ProcessedFoodItem[]): ProcessedMeal => ({
  meal_type: 'lunch',
  items: items || [
    createItem(),
    createItem({ product_id: 2, name: 'Rice', quantity_grams: 150, kcal: 195, protein: 4, fat: 0.4, carbs: 43, quantity_unit_value: 150 }),
  ],
  raw_transcription: 'chicken with rice',
  processing_time_ms: 500,
});

describe('Voice Meal Flow Integration', () => {
  it('process → review → edit quantity in grams → recalculate', () => {
    const meal = createMeal();
    const { result } = renderHook(() =>
      useVoiceMealLogic({ initialMeal: meal, t: mockT }),
    );

    // Initial totals
    expect(result.current.totals.kcal).toBe(525);

    // Edit quantity of first item: 200g → 300g, pass null for gram unit
    act(() => { result.current.updateQuantity(0, 300, null); });

    // Chicken 200g has 330 kcal → per gram = 1.65
    // 300g → 300 * 1.65 = 495 kcal; rice stays 195
    expect(result.current.localMeal!.items[0].quantity_grams).toBe(300);
    expect(result.current.totals.kcal).toBe(690);
  });

  it('process → remove item → totals update', () => {
    const meal = createMeal();
    const { result } = renderHook(() =>
      useVoiceMealLogic({ initialMeal: meal, t: mockT }),
    );

    expect(result.current.localMeal!.items.length).toBe(2);

    // Remove rice
    act(() => { result.current.removeItem(1); });

    expect(result.current.localMeal!.items.length).toBe(1);
    expect(result.current.totals.kcal).toBe(330); // Only chicken
  });

  it('process → add manual item → totals include new item', () => {
    const meal = createMeal([createItem()]);
    const { result } = renderHook(() =>
      useVoiceMealLogic({ initialMeal: meal, t: mockT }),
    );

    expect(result.current.localMeal!.items.length).toBe(1);

    const manualProduct = {
      id: 'p-3',
      name: 'Banana',
      nutrition: { calories_per_100g: 89, protein_per_100g: 1.1, fat_per_100g: 0.3, carbs_per_100g: 23 },
    };

    act(() => { result.current.addManualItem(manualProduct); });

    expect(result.current.localMeal!.items.length).toBe(2);
    expect(result.current.localMeal!.items[1].name).toBe('Banana');
    // 100g default → 89 kcal; chicken 330 + banana 89 = 419
    expect(result.current.totals.kcal).toBe(330 + 89);
  });

  it('process → cycle meal type through full cycle', () => {
    const meal = createMeal();
    const { result } = renderHook(() =>
      useVoiceMealLogic({ initialMeal: meal, t: mockT }),
    );

    // Cycle order: breakfast, second_breakfast, lunch, tea, dinner, snack
    expect(result.current.localMeal!.meal_type).toBe('lunch');

    act(() => { result.current.cycleMealType(); });
    expect(result.current.localMeal!.meal_type).toBe('tea');

    act(() => { result.current.cycleMealType(); });
    expect(result.current.localMeal!.meal_type).toBe('dinner');

    act(() => { result.current.cycleMealType(); });
    expect(result.current.localMeal!.meal_type).toBe('snack');

    act(() => { result.current.cycleMealType(); });
    expect(result.current.localMeal!.meal_type).toBe('breakfast');

    act(() => { result.current.cycleMealType(); });
    expect(result.current.localMeal!.meal_type).toBe('second_breakfast');

    act(() => { result.current.cycleMealType(); });
    expect(result.current.localMeal!.meal_type).toBe('lunch');
  });

  it('getMealTypeLabel returns translation keys', () => {
    const meal = createMeal();
    const { result } = renderHook(() =>
      useVoiceMealLogic({ initialMeal: meal, t: mockT }),
    );

    expect(result.current.getMealTypeLabel('breakfast')).toBe('meals.breakfast');
    expect(result.current.getMealTypeLabel('lunch')).toBe('meals.lunch');
    expect(result.current.getMealTypeLabel('dinner')).toBe('meals.dinner');
    expect(result.current.getMealTypeLabel('snack')).toBe('meals.snack');
    expect(result.current.getMealTypeLabel('tea')).toBe('meals.tea');
    expect(result.current.getMealTypeLabel('second_breakfast')).toBe('meals.second_breakfast');
  });

  it('edit with unit conversion recalculates macros', () => {
    const meal = createMeal([
      createItem({ unit_matched: 'piece', quantity_unit_value: 2, quantity_grams: 400, kcal: 660 }),
    ]);
    const { result } = renderHook(() =>
      useVoiceMealLogic({ initialMeal: meal, t: mockT }),
    );

    // Change from 2 pieces to 3 pieces using unit object
    act(() => {
      result.current.updateQuantity(0, 3, { grams: 200, label: 'piece' });
    });

    // 3 pieces × 200g = 600g
    expect(result.current.localMeal!.items[0].quantity_unit_value).toBe(3);
    expect(result.current.localMeal!.items[0].quantity_grams).toBe(600);
    // 660 kcal / 400g = 1.65 per gram; 600g × 1.65 = 990
    expect(result.current.localMeal!.items[0].kcal).toBe(990);
  });
});
