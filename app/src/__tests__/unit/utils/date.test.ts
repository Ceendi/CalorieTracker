import { formatDateForApi, formatDisplayDate, formatNumber } from '../../../utils/date';

describe('formatDateForApi', () => {
  it('formats default date as YYYY-MM-DD', () => {
    const result = formatDateForApi(new Date(2024, 0, 15));
    expect(result).toBe('2024-01-15');
  });

  it('pads single-digit month and day', () => {
    const result = formatDateForApi(new Date(2024, 2, 5));
    expect(result).toBe('2024-03-05');
  });

  it('formats specific date', () => {
    const result = formatDateForApi(new Date(2025, 11, 31));
    expect(result).toBe('2025-12-31');
  });

  it('uses current date when no argument', () => {
    const result = formatDateForApi();
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});

describe('formatDisplayDate', () => {
  it('formats date in English', () => {
    const date = new Date(2024, 0, 15);
    const result = formatDisplayDate(date, 'en');
    expect(result).toContain('January');
    expect(result).toContain('15');
  });

  it('formats date in Polish', () => {
    const date = new Date(2024, 0, 15);
    const result = formatDisplayDate(date, 'pl');
    expect(result).toContain('15');
    // Polish locale should include day name and month
    expect(result.length).toBeGreaterThan(5);
  });

  it('defaults to English', () => {
    const date = new Date(2024, 0, 15);
    const result = formatDisplayDate(date);
    expect(result).toContain('January');
  });
});

describe('formatNumber', () => {
  it('formats number in English', () => {
    const result = formatNumber(1234.56, 'en');
    expect(result).toContain('1');
    expect(result).toContain('234');
  });

  it('formats number in Polish', () => {
    const result = formatNumber(1234.56, 'pl');
    expect(result).toContain('1');
    expect(result).toContain('234');
  });

  it('defaults to English', () => {
    const result = formatNumber(1000);
    expect(result).toContain('1');
  });

  it('formats zero', () => {
    expect(formatNumber(0, 'en')).toBe('0');
  });
});
