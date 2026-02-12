import { parseFoodDetailsParams, serializeFoodForParams } from '../../../utils/foodDetailsParams';
import { MealType } from '../../../types/food';
import type { FoodProduct } from '../../../types/food';

describe('parseFoodDetailsParams', () => {
  it('returns "new" mode for empty params', () => {
    const result = parseFoodDetailsParams({});
    expect(result.mode).toBe('new');
    expect(result.initialValues.amount).toBe(100);
  });

  it('returns "barcode" mode when barcode present', () => {
    const result = parseFoodDetailsParams({ barcode: '123456789' });
    expect(result.mode).toBe('barcode');
    expect(result.barcode).toBe('123456789');
  });

  it('returns "edit" mode when entryId present', () => {
    const result = parseFoodDetailsParams({ entryId: 'uuid-123' });
    expect(result.mode).toBe('edit');
    expect(result.entryId).toBe('uuid-123');
  });

  it('parses food from valid JSON', () => {
    const food: FoodProduct = {
      id: 'test-id',
      name: 'Apple',
      nutrition: { calories_per_100g: 52, protein_per_100g: 0.3, fat_per_100g: 0.2, carbs_per_100g: 14 },
    };
    const result = parseFoodDetailsParams({ item: JSON.stringify(food) });
    expect(result.food?.name).toBe('Apple');
  });

  it('handles invalid JSON gracefully', () => {
    const result = parseFoodDetailsParams({ item: 'not-json' });
    expect(result.food).toBeUndefined();
  });

  it('parses unit info when both label and grams provided', () => {
    const result = parseFoodDetailsParams({ initialUnitLabel: 'slice', initialUnitGrams: '30' });
    expect(result.initialValues.unit).toEqual({ label: 'slice', grams: 30, unit: 'slice' });
  });

  it('does not set unit when only label provided', () => {
    const result = parseFoodDetailsParams({ initialUnitLabel: 'slice' });
    expect(result.initialValues.unit).toBeNull();
  });

  it('parses valid mealType', () => {
    const result = parseFoodDetailsParams({ initialMealType: 'breakfast' });
    expect(result.initialValues.mealType).toBe(MealType.BREAKFAST);
  });

  it('ignores invalid mealType', () => {
    const result = parseFoodDetailsParams({ initialMealType: 'brunch' });
    expect(result.initialValues.mealType).toBeUndefined();
  });

  it('uses initialAmount for amount', () => {
    const result = parseFoodDetailsParams({ initialAmount: '250' });
    expect(result.initialValues.amount).toBe(250);
  });

  it('prefers initialUnitQuantity over initialAmount', () => {
    const result = parseFoodDetailsParams({ initialUnitQuantity: '3', initialAmount: '250' });
    expect(result.initialValues.amount).toBe(3);
  });

  it('passes date through', () => {
    const result = parseFoodDetailsParams({ date: '2024-01-15' });
    expect(result.date).toBe('2024-01-15');
  });

  it('defaults amount to 100 when nothing provided', () => {
    const result = parseFoodDetailsParams({});
    expect(result.initialValues.amount).toBe(100);
  });
});

describe('serializeFoodForParams', () => {
  it('serializes food to JSON string', () => {
    const food: FoodProduct = {
      id: 'test-id',
      name: 'Apple',
      nutrition: { calories_per_100g: 52, protein_per_100g: 0.3, fat_per_100g: 0.2, carbs_per_100g: 14 },
    };
    const result = serializeFoodForParams(food);
    const parsed = JSON.parse(result);
    expect(parsed.name).toBe('Apple');
    expect(parsed.id).toBe('test-id');
  });
});
