import {
  calculateBMR,
  calculateDailyGoal,
  summarizeMealMacros,
  calculateItemMacros,
  ActivityMultipliers,
} from '../utils/calculations';

/**
 * Note: calculateBMR, calculateDailyGoal, and ActivityMultipliers are deprecated.
 * They are kept as fallback for when the backend API is unavailable.
 * Prefer using useDailyTargets() hook from @/hooks/useMealPlan in components.
 * These tests remain to ensure the fallback logic continues to work correctly.
 */

describe('calculateBMR (deprecated - fallback)', () => {
  it('calculates BMR correctly for male', () => {
    // Mifflin-St Jeor: (10 * 80) + (6.25 * 180) - (5 * 30) + 5 = 800 + 1125 - 150 + 5 = 1780
    const result = calculateBMR(80, 180, 30, 'male');
    expect(result).toBe(1780);
  });

  it('calculates BMR correctly for female', () => {
    // Mifflin-St Jeor: (10 * 60) + (6.25 * 165) - (5 * 25) - 161 = 600 + 1031.25 - 125 - 161 = 1345.25 -> 1345
    const result = calculateBMR(60, 165, 25, 'female');
    expect(result).toBe(1345);
  });
});

describe('calculateDailyGoal (deprecated - fallback)', () => {
  it('returns default values when profile is incomplete', () => {
    const result = calculateDailyGoal({});
    expect(result).toEqual({
      calories: 2000,
      protein: 160,
      fat: 70,
      carbs: 250,
    });
  });

  it('calculates goals based on profile with sedentary activity', () => {
    const profile = {
      weight: 80,
      height: 180,
      age: 30,
      gender: 'male' as const,
      activity_level: 'sedentary',
      goal: 'maintain',
    };
    const result = calculateDailyGoal(profile);

    // BMR = 1780, TDEE = 1780 * 1.2 = 2136
    expect(result.calories).toBe(2136);
    // protein: (2136 * 0.2) / 4 = 107
    expect(result.protein).toBe(107);
    // fat: (2136 * 0.3) / 9 = 71
    expect(result.fat).toBe(71);
    // carbs: (2136 * 0.5) / 4 = 267
    expect(result.carbs).toBe(267);
  });
});

describe('summarizeMealMacros', () => {
  it('sums up macros from multiple items', () => {
    const items = [
      { kcal: 200, protein: 10, fat: 5, carbs: 30 },
      { kcal: 150, protein: 8, fat: 3, carbs: 20 },
      { kcal: 100, protein: 5, fat: 2, carbs: 15 },
    ];

    const result = summarizeMealMacros(items);

    expect(result).toEqual({
      kcal: 450,
      protein: 23,
      fat: 10,
      carbs: 65,
    });
  });

  it('returns zeros for empty array', () => {
    const result = summarizeMealMacros([]);
    expect(result).toEqual({ kcal: 0, protein: 0, fat: 0, carbs: 0 });
  });
});

describe('calculateItemMacros', () => {
  it('scales macros based on new quantity', () => {
    const currentMacros = { kcal: 100, protein: 10, fat: 5, carbs: 20 };
    const result = calculateItemMacros(currentMacros, 100, 200, 1);

    // 200g is 2x the original 100g
    expect(result.kcal).toBe(200);
    expect(result.protein).toBe(20);
    expect(result.fat).toBe(10);
    expect(result.carbs).toBe(40);
  });

  it('returns zeros for negative quantity', () => {
    const currentMacros = { kcal: 100, protein: 10, fat: 5, carbs: 20 };
    const result = calculateItemMacros(currentMacros, 100, -50, 1);

    expect(result).toEqual({ kcal: 0, protein: 0, fat: 0, carbs: 0 });
  });
});

describe('ActivityMultipliers (deprecated - fallback)', () => {
  it('has correct multiplier values', () => {
    expect(ActivityMultipliers.sedentary).toBe(1.2);
    expect(ActivityMultipliers.light).toBe(1.375);
    expect(ActivityMultipliers.moderate).toBe(1.55);
    expect(ActivityMultipliers.high).toBe(1.725);
    expect(ActivityMultipliers.very_high).toBe(1.9);
  });
});
