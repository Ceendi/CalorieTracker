import {
  PlanPreferencesSchema,
  GeneratePlanRequestSchema,
  GenerationStatusResponseSchema,
  MealPlanSchema,
  DailyTargetsResponseSchema,
  MealPlanListResponseSchema,
} from '../../../schemas/meal-plan';

describe('PlanPreferencesSchema', () => {
  it('parses with defaults', () => {
    const result = PlanPreferencesSchema.parse({});
    expect(result.allergies).toEqual([]);
    expect(result.cuisine_preferences).toEqual(['polish']);
    expect(result.excluded_ingredients).toEqual([]);
  });

  it('accepts full preferences', () => {
    const result = PlanPreferencesSchema.parse({
      diet: 'vegetarian',
      allergies: ['gluten', 'dairy'],
      cuisine_preferences: ['italian', 'polish'],
      excluded_ingredients: ['mushrooms'],
      max_preparation_time: 30,
    });
    expect(result.diet).toBe('vegetarian');
    expect(result.allergies).toHaveLength(2);
  });

  it('accepts null diet', () => {
    const result = PlanPreferencesSchema.parse({ diet: null });
    expect(result.diet).toBeNull();
  });
});

describe('GeneratePlanRequestSchema', () => {
  it('parses valid request', () => {
    const result = GeneratePlanRequestSchema.parse({
      start_date: '2024-01-15',
      days: 7,
    });
    expect(result.days).toBe(7);
  });

  it('defaults days to 7', () => {
    const result = GeneratePlanRequestSchema.parse({ start_date: '2024-01-15' });
    expect(result.days).toBe(7);
  });

  it('rejects days < 1', () => {
    expect(() => GeneratePlanRequestSchema.parse({ start_date: '2024-01-15', days: 0 })).toThrow();
  });

  it('rejects days > 14', () => {
    expect(() => GeneratePlanRequestSchema.parse({ start_date: '2024-01-15', days: 15 })).toThrow();
  });

  it('accepts days=1', () => {
    const result = GeneratePlanRequestSchema.parse({ start_date: '2024-01-15', days: 1 });
    expect(result.days).toBe(1);
  });

  it('accepts days=14', () => {
    const result = GeneratePlanRequestSchema.parse({ start_date: '2024-01-15', days: 14 });
    expect(result.days).toBe(14);
  });
});

describe('GenerationStatusResponseSchema', () => {
  it('parses completed status', () => {
    const result = GenerationStatusResponseSchema.parse({
      status: 'completed',
      progress: 100,
      plan_id: 'plan-123',
    });
    expect(result.status).toBe('completed');
    expect(result.plan_id).toBe('plan-123');
  });

  it('parses error status', () => {
    const result = GenerationStatusResponseSchema.parse({
      status: 'error',
      error: 'Generation failed',
    });
    expect(result.status).toBe('error');
    expect(result.error).toBe('Generation failed');
  });

  it('parses generating with progress', () => {
    const result = GenerationStatusResponseSchema.parse({
      status: 'generating',
      progress: 50,
      message: 'Generating day 3...',
      day: 3,
    });
    expect(result.progress).toBe(50);
    expect(result.day).toBe(3);
  });

  it('rejects invalid status', () => {
    expect(() => GenerationStatusResponseSchema.parse({ status: 'invalid' })).toThrow();
  });
});

describe('DailyTargetsResponseSchema', () => {
  it('parses targets', () => {
    const result = DailyTargetsResponseSchema.parse({
      kcal: 2000,
      protein: 150,
      fat: 70,
      carbs: 250,
    });
    expect(result.kcal).toBe(2000);
  });

  it('rejects missing fields', () => {
    expect(() => DailyTargetsResponseSchema.parse({ kcal: 2000 })).toThrow();
  });
});

describe('MealPlanSchema', () => {
  it('parses minimal plan', () => {
    const result = MealPlanSchema.parse({
      id: '550e8400-e29b-41d4-a716-446655440000',
      start_date: '2024-01-15',
      end_date: '2024-01-21',
      status: 'draft',
    });
    expect(result.days).toEqual([]);
  });

  it('parses plan with days and meals', () => {
    const result = MealPlanSchema.parse({
      id: '550e8400-e29b-41d4-a716-446655440000',
      name: 'Weekly Plan',
      start_date: '2024-01-15',
      end_date: '2024-01-21',
      status: 'active',
      daily_targets: { protein: 150, fat: 70, carbs: 250 },
      days: [{
        id: '550e8400-e29b-41d4-a716-446655440001',
        day_number: 1,
        meals: [{
          id: '550e8400-e29b-41d4-a716-446655440002',
          meal_type: 'breakfast',
          name: 'Oatmeal',
          ingredients: [],
        }],
      }],
    });
    expect(result.days).toHaveLength(1);
    expect(result.days[0].meals).toHaveLength(1);
  });
});

describe('MealPlanListResponseSchema', () => {
  it('parses plan list', () => {
    const result = MealPlanListResponseSchema.parse({
      plans: [{
        id: '550e8400-e29b-41d4-a716-446655440000',
        start_date: '2024-01-15',
        end_date: '2024-01-21',
        status: 'active',
      }],
    });
    expect(result.plans).toHaveLength(1);
  });

  it('parses empty plan list', () => {
    const result = MealPlanListResponseSchema.parse({ plans: [] });
    expect(result.plans).toEqual([]);
  });
});
