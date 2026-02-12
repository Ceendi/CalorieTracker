import {
  TokenResponseSchema,
  UserResponseSchema,
  NutritionSchema,
  FoodProductResponseSchema,
  FoodSearchResponseSchema,
  MealEntryResponseSchema,
  DailyLogResponseSchema,
  VoiceProcessResponseSchema,
} from '../../../schemas/api';

describe('TokenResponseSchema', () => {
  it('parses valid tokens', () => {
    const result = TokenResponseSchema.parse({
      access_token: 'abc123',
      refresh_token: 'xyz789',
    });
    expect(result.access_token).toBe('abc123');
    expect(result.token_type).toBe('bearer');
  });

  it('accepts custom token_type', () => {
    const result = TokenResponseSchema.parse({
      access_token: 'a',
      refresh_token: 'b',
      token_type: 'custom',
    });
    expect(result.token_type).toBe('custom');
  });

  it('rejects missing access_token', () => {
    expect(() => TokenResponseSchema.parse({ refresh_token: 'b' })).toThrow();
  });
});

describe('UserResponseSchema', () => {
  it('parses minimal user', () => {
    const result = UserResponseSchema.parse({
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'user@test.com',
    });
    expect(result.is_active).toBe(true);
    expect(result.is_verified).toBe(false);
    expect(result.is_onboarded).toBe(false);
  });

  it('parses full user with profile', () => {
    const result = UserResponseSchema.parse({
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'user@test.com',
      is_active: true,
      is_verified: true,
      weight: 80,
      height: 180,
      age: 30,
      gender: 'male',
      activity_level: 'moderate',
      goal: 'maintain',
    });
    expect(result.weight).toBe(80);
    expect(result.gender).toBe('male');
  });

  it('accepts nullable fields', () => {
    const result = UserResponseSchema.parse({
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'u@t.com',
      weight: null,
      height: null,
    });
    expect(result.weight).toBeNull();
  });

  it('rejects invalid uuid', () => {
    expect(() => UserResponseSchema.parse({ id: 'not-a-uuid', email: 'u@t.com' })).toThrow();
  });

  it('rejects invalid email', () => {
    expect(() => UserResponseSchema.parse({ id: '550e8400-e29b-41d4-a716-446655440000', email: 'bad' })).toThrow();
  });
});

describe('NutritionSchema', () => {
  it('parses valid nutrition', () => {
    const result = NutritionSchema.parse({
      kcal_per_100g: 250,
      protein_per_100g: 20,
      fat_per_100g: 10,
      carbs_per_100g: 30,
    });
    expect(result.kcal_per_100g).toBe(250);
  });

  it('defaults missing values to 0', () => {
    const result = NutritionSchema.parse({});
    expect(result.kcal_per_100g).toBe(0);
    expect(result.protein_per_100g).toBe(0);
  });
});

describe('FoodProductResponseSchema', () => {
  it('parses food product', () => {
    const result = FoodProductResponseSchema.parse({
      id: '550e8400-e29b-41d4-a716-446655440000',
      name: 'Apple',
      nutrition: { kcal_per_100g: 52, protein_per_100g: 0.3, fat_per_100g: 0.2, carbs_per_100g: 14 },
    });
    expect(result.name).toBe('Apple');
    expect(result.units).toEqual([]);
  });

  it('accepts nullable id', () => {
    const result = FoodProductResponseSchema.parse({
      id: null,
      name: 'Custom Food',
      nutrition: {},
    });
    expect(result.id).toBeNull();
  });

  it('parses units array', () => {
    const result = FoodProductResponseSchema.parse({
      id: '550e8400-e29b-41d4-a716-446655440000',
      name: 'Milk',
      nutrition: {},
      units: [{ unit: 'glass', grams: 250, label: 'szklanka' }],
    });
    expect(result.units).toHaveLength(1);
    expect(result.units[0].grams).toBe(250);
  });
});

describe('FoodSearchResponseSchema', () => {
  it('parses array of food products', () => {
    const result = FoodSearchResponseSchema.parse([
      { id: '550e8400-e29b-41d4-a716-446655440000', name: 'A', nutrition: {} },
      { id: '550e8400-e29b-41d4-a716-446655440001', name: 'B', nutrition: {} },
    ]);
    expect(result).toHaveLength(2);
  });

  it('parses empty array', () => {
    expect(FoodSearchResponseSchema.parse([])).toEqual([]);
  });
});

describe('MealEntryResponseSchema', () => {
  it('parses meal entry', () => {
    const result = MealEntryResponseSchema.parse({
      id: '550e8400-e29b-41d4-a716-446655440000',
      daily_log_id: '550e8400-e29b-41d4-a716-446655440001',
      product_id: '550e8400-e29b-41d4-a716-446655440002',
      amount_grams: 200,
      meal_type: 'lunch',
    });
    expect(result.amount_grams).toBe(200);
    expect(result.product_name).toBe('Unknown');
    expect(result.computed_kcal).toBe(0);
  });
});

describe('DailyLogResponseSchema', () => {
  it('parses daily log', () => {
    const result = DailyLogResponseSchema.parse({
      id: '550e8400-e29b-41d4-a716-446655440000',
      date: '2024-01-15',
    });
    expect(result.entries).toEqual([]);
    expect(result.total_kcal).toBe(0);
  });

  it('parses with entries', () => {
    const result = DailyLogResponseSchema.parse({
      id: '550e8400-e29b-41d4-a716-446655440000',
      date: '2024-01-15',
      entries: [{
        id: '550e8400-e29b-41d4-a716-446655440001',
        daily_log_id: '550e8400-e29b-41d4-a716-446655440000',
        product_id: '550e8400-e29b-41d4-a716-446655440002',
        amount_grams: 100,
        meal_type: 'breakfast',
      }],
      total_kcal: 250,
    });
    expect(result.entries).toHaveLength(1);
    expect(result.total_kcal).toBe(250);
  });
});

describe('VoiceProcessResponseSchema', () => {
  it('parses voice processing result', () => {
    const result = VoiceProcessResponseSchema.parse({
      transcription: 'chicken breast 200g',
      meal_type: 'lunch',
      items: [{
        product_id: '550e8400-e29b-41d4-a716-446655440000',
        name: 'Chicken Breast',
        quantity_grams: 200,
        quantity_unit_value: 200,
        unit_matched: 'g',
        kcal: 330,
        protein: 62,
        fat: 7.2,
        carbs: 0,
        kcal_per_100g: 165,
        protein_per_100g: 31,
        fat_per_100g: 3.6,
        carbs_per_100g: 0,
      }],
    });
    expect(result.transcription).toBe('chicken breast 200g');
    expect(result.items).toHaveLength(1);
  });

  it('accepts empty items', () => {
    const result = VoiceProcessResponseSchema.parse({
      transcription: '',
      meal_type: 'snack',
      items: [],
    });
    expect(result.items).toEqual([]);
  });
});
