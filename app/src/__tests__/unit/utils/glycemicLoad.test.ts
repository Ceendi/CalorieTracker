import { calculateGL, GLResult } from '../../../utils/glycemicLoad';

describe('calculateGL', () => {
  describe('formula: GL = (GI × carbsGrams) / 100', () => {
    it('calculates GL for white rice portion', () => {
      const result = calculateGL(73, 28);
      expect(result.value).toBe(20.4);
    });

    it('calculates GL for apple', () => {
      const result = calculateGL(36, 14);
      expect(result.value).toBe(5);
    });

    it('calculates GL for oatmeal portion', () => {
      const result = calculateGL(55, 27);
      expect(result.value).toBe(14.9);
    });

    it('rounds to one decimal place', () => {
      const result = calculateGL(73, 15);
      expect(result.value).toBe(11);
    });

    it('returns zero when gi is 0', () => {
      expect(calculateGL(0, 30).value).toBe(0);
    });

    it('returns zero when carbsGrams is 0', () => {
      expect(calculateGL(73, 0).value).toBe(0);
    });
  });

  describe('label classification', () => {
    it('returns "low" when GL = 10.0 (boundary)', () => {
      expect(calculateGL(50, 20).label).toBe('low');
    });

    it('returns "low" when GL < 10', () => {
      expect(calculateGL(36, 14).label).toBe('low');
    });

    it('returns "medium" when GL = 11.0 (just above low boundary)', () => {
      expect(calculateGL(55, 20).label).toBe('medium');
    });

    it('returns "medium" when GL = 19.0 (boundary)', () => {
      expect(calculateGL(76, 25).label).toBe('medium');
    });

    it('returns "high" when GL = 20.0 (just above medium boundary)', () => {
      expect(calculateGL(80, 25).label).toBe('high');
    });

    it('returns "high" when GL is large', () => {
      expect(calculateGL(87, 50).label).toBe('high');
    });

    it('returns "low" for zero GL', () => {
      expect(calculateGL(0, 0).label).toBe('low');
    });
  });

  describe('return shape', () => {
    it('returns an object with value and label', () => {
      const result: GLResult = calculateGL(55, 30);
      expect(result).toHaveProperty('value');
      expect(result).toHaveProperty('label');
    });

    it('value is a number', () => {
      expect(typeof calculateGL(55, 30).value).toBe('number');
    });

    it('label is one of the valid GLLabel values', () => {
      const validLabels: string[] = ['low', 'medium', 'high'];
      expect(validLabels).toContain(calculateGL(55, 30).label);
    });
  });
});
