import { translations } from '../../../i18n/translations';

describe('translations', () => {
  it('has both en and pl languages', () => {
    expect(translations).toHaveProperty('en');
    expect(translations).toHaveProperty('pl');
  });

  it('PL and EN have the same top-level keys', () => {
    const enKeys = Object.keys(translations.en).sort();
    const plKeys = Object.keys(translations.pl).sort();
    expect(enKeys).toEqual(plKeys);
  });

  it('has no empty strings in EN', () => {
    const findEmpty = (obj: any, path: string = ''): string[] => {
      const result: string[] = [];
      for (const [key, value] of Object.entries(obj)) {
        const fullPath = path ? `${path}.${key}` : key;
        if (typeof value === 'string' && value === '') {
          result.push(fullPath);
        } else if (typeof value === 'object' && value !== null) {
          result.push(...findEmpty(value, fullPath));
        }
      }
      return result;
    };
    const emptyKeys = findEmpty(translations.en);
    expect(emptyKeys).toEqual([]);
  });

  it('has no empty strings in PL', () => {
    const findEmpty = (obj: any, path: string = ''): string[] => {
      const result: string[] = [];
      for (const [key, value] of Object.entries(obj)) {
        const fullPath = path ? `${path}.${key}` : key;
        if (typeof value === 'string' && value === '') {
          result.push(fullPath);
        } else if (typeof value === 'object' && value !== null) {
          result.push(...findEmpty(value, fullPath));
        }
      }
      return result;
    };
    const emptyKeys = findEmpty(translations.pl);
    expect(emptyKeys).toEqual([]);
  });

  it('key popular keys exist in both languages', () => {
    const popularKeys = ['auth', 'profile', 'dashboard', 'meals', 'settings', 'tabs'];
    for (const key of popularKeys) {
      expect(translations.en).toHaveProperty(key);
      expect(translations.pl).toHaveProperty(key);
    }
  });

  it('meal types exist in both languages', () => {
    expect(translations.en.meals.breakfast).toBeTruthy();
    expect(translations.en.meals.lunch).toBeTruthy();
    expect(translations.en.meals.dinner).toBeTruthy();
    expect(translations.en.meals.snack).toBeTruthy();
    expect(translations.pl.meals.breakfast).toBeTruthy();
    expect(translations.pl.meals.lunch).toBeTruthy();
    expect(translations.pl.meals.dinner).toBeTruthy();
    expect(translations.pl.meals.snack).toBeTruthy();
  });
});
