import { UserProfileSchema } from '../../../schemas/user';

describe('UserProfileSchema', () => {
  it('accepts valid full profile', () => {
    const result = UserProfileSchema.safeParse({
      height: 180,
      weight: 80,
      age: 30,
      goal: 'maintain',
      activity_level: 'moderate',
      gender: 'male',
    });
    expect(result.success).toBe(true);
  });

  it('rejects height below 50', () => {
    const result = UserProfileSchema.safeParse({ height: 40 });
    expect(result.success).toBe(false);
  });

  it('rejects height above 300', () => {
    const result = UserProfileSchema.safeParse({ height: 310 });
    expect(result.success).toBe(false);
  });

  it('rejects weight below 20', () => {
    const result = UserProfileSchema.safeParse({ weight: 10 });
    expect(result.success).toBe(false);
  });

  it('rejects weight above 500', () => {
    const result = UserProfileSchema.safeParse({ weight: 600 });
    expect(result.success).toBe(false);
  });

  it('rejects age below 10', () => {
    const result = UserProfileSchema.safeParse({ age: 5 });
    expect(result.success).toBe(false);
  });

  it('rejects age above 120', () => {
    const result = UserProfileSchema.safeParse({ age: 130 });
    expect(result.success).toBe(false);
  });

  it('accepts nullable fields', () => {
    const result = UserProfileSchema.safeParse({ height: null, weight: null, age: null });
    expect(result.success).toBe(true);
  });

  it('accepts empty object', () => {
    const result = UserProfileSchema.safeParse({});
    expect(result.success).toBe(true);
  });

  it('accepts boundary values', () => {
    const result = UserProfileSchema.safeParse({ height: 50, weight: 20, age: 10 });
    expect(result.success).toBe(true);
    const result2 = UserProfileSchema.safeParse({ height: 300, weight: 500, age: 120 });
    expect(result2.success).toBe(true);
  });
});
