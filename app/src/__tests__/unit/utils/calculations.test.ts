import {
  calculateBMR,
  calculateDailyGoal,
  summarizeMealMacros,
  calculateItemMacros,
  ActivityMultipliers,
  GoalModifiers,
  clamp,
  roundTo,
} from '../../../utils/calculations';

describe('calculateBMR', () => {
  it('calculates BMR correctly for male', () => {
    expect(calculateBMR(80, 180, 30, 'male')).toBe(1780);
  });

  it('calculates BMR correctly for female', () => {
    expect(calculateBMR(60, 165, 25, 'female')).toBe(1345.25);
  });

  it('treats "Male" (capitalized) as male', () => {
    expect(calculateBMR(80, 180, 30, 'Male')).toBe(1780);
  });

  it('treats unknown gender as female formula', () => {
    const result = calculateBMR(80, 180, 30, 'other');
    expect(result).toBe((10 * 80) + (6.25 * 180) - (5 * 30) - 161);
  });

  it('handles minimum values', () => {
    const result = calculateBMR(1, 1, 1, 'male');
    expect(result).toBe((10 * 1) + (6.25 * 1) - (5 * 1) + 5);
  });

  it('handles large values', () => {
    const result = calculateBMR(200, 250, 100, 'female');
    expect(result).toBe((10 * 200) + (6.25 * 250) - (5 * 100) - 161);
  });

  it('returns exact float value', () => {
    const result = calculateBMR(65, 170, 28, 'female');
    expect(result).toBe(1411.5);
  });
});

describe('calculateDailyGoal', () => {
  const baseProfile = { weight: 80, height: 180, age: 30, gender: 'male' as const, activity_level: 'sedentary' };

  it('returns default values when profile is incomplete', () => {
    expect(calculateDailyGoal({})).toEqual({
      calories: 2000, protein: 160, fat: 70, carbs: 250,
    });
  });

  it('returns defaults when only weight is provided', () => {
    expect(calculateDailyGoal({ weight: 80 })).toEqual({
      calories: 2000, protein: 160, fat: 70, carbs: 250,
    });
  });

  it('calculates goals with sedentary activity and maintain goal', () => {
    const profile = { ...baseProfile, goal: 'maintain' };
    const result = calculateDailyGoal(profile);
    // BMR=1780 * 1.4 = 2492
    expect(result.calories).toBe(2492);
    expect(result.protein).toBe(124.6); // 2492 * 0.2 / 4 = 124.6
    expect(result.fat).toBe(83.1); // 2492 * 0.3 / 9 = 83.06 -> 83.1
    expect(result.carbs).toBe(311.5); // 2492 * 0.5 / 4 = 311.5
  });

  it('applies lose weight goal modifier correctly', () => {
    // BMR=1780 * 1.4 = 2492
    // Lose goal: Math.round(2492 * 0.8) = Math.round(1993.6) = 1994
    const result = calculateDailyGoal({ ...baseProfile, goal: 'lose' });
    expect(result.calories).toBe(1994);
    expect(result.protein).toBe(99.7); // 1994 * 0.2 / 4 = 99.7
    expect(result.fat).toBe(66.5); // 1994 * 0.3 / 9 = 66.46 -> 66.5
    expect(result.carbs).toBe(249.3); // 1994 * 0.5 / 4 = 249.25 -> 249.3
  });

  it('applies gain weight goal modifier correctly', () => {
    // BMR=1780 * 1.4 = 2492
    // Gain goal: Math.round(2492 * 1.15) = Math.round(2865.8) = 2866
    const result = calculateDailyGoal({ ...baseProfile, goal: 'gain' });
    expect(result.calories).toBe(2866);
  });

  it('uses very_high activity multiplier', () => {
    const profile = { weight: 80, height: 180, age: 30, gender: 'male' as const, activity_level: 'very_high', goal: 'maintain' };
    const result = calculateDailyGoal(profile);
    // 1780 * 2.0 = 3560
    expect(result.calories).toBe(3560);
  });

  it('defaults to sedentary for unknown activity', () => {
    const profile = { weight: 80, height: 180, age: 30, gender: 'male' as const, activity_level: 'unknown', goal: 'maintain' };
    const result = calculateDailyGoal(profile);
    expect(result.calories).toBe(Math.trunc(1780 * 1.4)); 
  });

  it('defaults to maintain for unknown goal', () => {
    const profile = { weight: 80, height: 180, age: 30, gender: 'male' as const, activity_level: 'sedentary', goal: 'unknown' };
    const result = calculateDailyGoal(profile);
    // BMR=1780 * 1.4 = 2492
    expect(result.calories).toBe(2492);
  });
});

describe('summarizeMealMacros', () => {
  it('sums up macros from multiple items', () => {
    const items = [
      { kcal: 200, protein: 10, fat: 5, carbs: 30 },
      { kcal: 150, protein: 8, fat: 3, carbs: 20 },
      { kcal: 100, protein: 5, fat: 2, carbs: 15 },
    ];
    expect(summarizeMealMacros(items)).toEqual({ kcal: 450, protein: 23, fat: 10, carbs: 65 });
  });

  it('returns zeros for empty array', () => {
    expect(summarizeMealMacros([])).toEqual({ kcal: 0, protein: 0, fat: 0, carbs: 0 });
  });

  it('handles single item', () => {
    expect(summarizeMealMacros([{ kcal: 100, protein: 5, fat: 3, carbs: 10 }]))
      .toEqual({ kcal: 100, protein: 5, fat: 3, carbs: 10 });
  });
});

describe('calculateItemMacros', () => {
  const baseMacros = { kcal: 100, protein: 10, fat: 5, carbs: 20 };

  it('scales macros based on new quantity', () => {
    const result = calculateItemMacros(baseMacros, 100, 200, 1);
    expect(result.kcal).toBe(200);
    expect(result.protein).toBe(20);
    expect(result.fat).toBe(10);
    expect(result.carbs).toBe(40);
  });

  it('returns zeros for negative quantity', () => {
    expect(calculateItemMacros(baseMacros, 100, -50, 1))
      .toEqual({ kcal: 0, protein: 0, fat: 0, carbs: 0 });
  });

  it('returns zeros for NaN quantity', () => {
    expect(calculateItemMacros(baseMacros, 100, NaN, 1))
      .toEqual({ kcal: 0, protein: 0, fat: 0, carbs: 0 });
  });

  it('returns zeros for NaN macros', () => {
    expect(calculateItemMacros({ kcal: NaN, protein: NaN, fat: 0, carbs: 0 }, 100, 100, 1))
      .toEqual({ kcal: 0, protein: 0, fat: 0, carbs: 0 });
  });

  it('handles quantity=0', () => {
    const result = calculateItemMacros(baseMacros, 100, 0, 1);
    expect(result.kcal).toBe(0);
  });

  it('uses gramsPerUnit multiplier', () => {
    const result = calculateItemMacros(baseMacros, 100, 2, 50);
    expect(result.kcal).toBe(100);
  });

  it('defaults originalGrams=0 to 100', () => {
    const result = calculateItemMacros(baseMacros, 0, 100, 1);
    expect(result.kcal).toBe(100);
  });

  it('handles large values', () => {
    const result = calculateItemMacros({ kcal: 5000, protein: 200, fat: 100, carbs: 500 }, 100, 1000, 1);
    expect(result.kcal).toBe(50000);
  });
});

describe('ActivityMultipliers', () => {
  it('has correct multiplier values', () => {
    expect(ActivityMultipliers.sedentary).toBe(1.4);
    expect(ActivityMultipliers.light).toBe(1.55);
    expect(ActivityMultipliers.moderate).toBe(1.70);
    expect(ActivityMultipliers.high).toBe(1.85);
    expect(ActivityMultipliers.very_high).toBe(2.0);
  });
});

describe('GoalModifiers', () => {
  it('has correct modifier values', () => {
    expect(GoalModifiers.lose).toBe(0.8);
    expect(GoalModifiers.maintain).toBe(1.0);
    expect(GoalModifiers.gain).toBe(1.15);
  });
});

describe('clamp', () => {
  it('returns value when within range', () => {
    expect(clamp(5, 0, 10)).toBe(5);
  });

  it('clamps to min when below', () => {
    expect(clamp(-5, 0, 10)).toBe(0);
  });

  it('clamps to max when above', () => {
    expect(clamp(15, 0, 10)).toBe(10);
  });

  it('returns boundary values correctly', () => {
    expect(clamp(0, 0, 10)).toBe(0);
    expect(clamp(10, 0, 10)).toBe(10);
  });
});

describe('roundTo', () => {
  it('rounds to 1 decimal place by default', () => {
    expect(roundTo(3.456)).toBe(3.5);
  });

  it('rounds to 0 decimal places', () => {
    expect(roundTo(3.456, 0)).toBe(3);
  });

  it('rounds to 2 decimal places', () => {
    expect(roundTo(3.456, 2)).toBe(3.46);
  });

  it('handles already-rounded values', () => {
    expect(roundTo(3.0, 1)).toBe(3);
  });
});
