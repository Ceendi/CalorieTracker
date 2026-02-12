import { manualFoodSchema } from '../../../schemas/food';

describe('manualFoodSchema', () => {
  it('accepts valid food data', () => {
    const result = manualFoodSchema.safeParse({
      name: 'Scrambled Eggs',
      calories: 155,
      protein: 11,
      fat: 11,
      carbs: 1.6,
      weight: 100,
      mealType: 'breakfast',
    });
    expect(result.success).toBe(true);
  });

  it('rejects empty name', () => {
    const result = manualFoodSchema.safeParse({
      name: '',
      calories: 100,
      protein: 10,
      fat: 5,
      carbs: 15,
      weight: 100,
      mealType: 'lunch',
    });
    expect(result.success).toBe(false);
  });

  it('rejects negative calories', () => {
    const result = manualFoodSchema.safeParse({
      name: 'Food',
      calories: -10,
      protein: 10,
      fat: 5,
      carbs: 15,
      weight: 100,
      mealType: 'lunch',
    });
    expect(result.success).toBe(false);
  });

  it('rejects weight less than 1', () => {
    const result = manualFoodSchema.safeParse({
      name: 'Food',
      calories: 100,
      protein: 10,
      fat: 5,
      carbs: 15,
      weight: 0,
      mealType: 'lunch',
    });
    expect(result.success).toBe(false);
  });

  it('applies defaults for missing numeric fields', () => {
    const result = manualFoodSchema.safeParse({
      name: 'Food',
      mealType: 'snack',
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.calories).toBe(0);
      expect(result.data.protein).toBe(0);
      expect(result.data.fat).toBe(0);
      expect(result.data.carbs).toBe(0);
      expect(result.data.weight).toBe(100);
    }
  });

  it('coerces string numbers', () => {
    const result = manualFoodSchema.safeParse({
      name: 'Food',
      calories: '200',
      protein: '15',
      fat: '8',
      carbs: '25',
      weight: '150',
      mealType: 'lunch',
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.calories).toBe(200);
      expect(result.data.weight).toBe(150);
    }
  });

  it('accepts all valid MealType values', () => {
    for (const mealType of ['breakfast', 'lunch', 'dinner', 'snack']) {
      const result = manualFoodSchema.safeParse({ name: 'Food', mealType });
      expect(result.success).toBe(true);
    }
  });

  it('rejects invalid mealType', () => {
    const result = manualFoodSchema.safeParse({ name: 'Food', mealType: 'brunch' });
    expect(result.success).toBe(false);
  });
});
