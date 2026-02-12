import { GOAL_OPTIONS, ACTIVITY_OPTIONS, GENDER_OPTIONS } from '../../../constants/options';

describe('GOAL_OPTIONS', () => {
  it('has 3 options', () => {
    expect(GOAL_OPTIONS).toHaveLength(3);
  });

  it('has correct values', () => {
    const values = GOAL_OPTIONS.map(o => o.value);
    expect(values).toEqual(['lose', 'maintain', 'gain']);
  });

  it('each option has label and value', () => {
    GOAL_OPTIONS.forEach(option => {
      expect(option.label).toBeTruthy();
      expect(option.value).toBeTruthy();
    });
  });
});

describe('ACTIVITY_OPTIONS', () => {
  it('has 5 options', () => {
    expect(ACTIVITY_OPTIONS).toHaveLength(5);
  });

  it('has correct values', () => {
    const values = ACTIVITY_OPTIONS.map(o => o.value);
    expect(values).toEqual(['sedentary', 'light', 'moderate', 'high', 'very_high']);
  });
});

describe('GENDER_OPTIONS', () => {
  it('has 2 options', () => {
    expect(GENDER_OPTIONS).toHaveLength(2);
  });

  it('has male and female', () => {
    const values = GENDER_OPTIONS.map(o => o.value);
    expect(values).toContain('male');
    expect(values).toContain('female');
  });
});
