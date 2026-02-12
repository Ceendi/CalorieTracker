import { render, fireEvent } from '@testing-library/react-native';

jest.mock('@/hooks/useLanguage', () => ({
  useLanguage: () => ({ t: (k: string) => k, language: 'en', setLanguage: jest.fn() }),
}));
jest.mock('@/components/ui/IconSymbol', () => ({
  IconSymbol: 'IconSymbol',
}));

import { FoodEntryItem } from '@/components/diary/FoodEntryItem';
import { MealEntry, MealType } from '@/types/food';

const createEntry = (overrides?: Partial<MealEntry>): MealEntry => ({
  id: 'entry-1',
  product_id: 'prod-1',
  product: {
    id: 'prod-1',
    name: 'Chicken Breast',
    nutrition: { calories_per_100g: 165, protein_per_100g: 31, fat_per_100g: 3.6, carbs_per_100g: 0 },
  },
  date: '2024-01-15',
  meal_type: MealType.LUNCH,
  amount_grams: 200,
  calories: 330,
  protein: 62,
  fat: 7.2,
  carbs: 0,
  ...overrides,
});

describe('FoodEntryItem', () => {
  const onDelete = jest.fn();
  const onPress = jest.fn();

  beforeEach(() => jest.clearAllMocks());

  it('renders product name', () => {
    const entry = createEntry();
    const { getByText } = render(
      <FoodEntryItem entry={entry} onDelete={onDelete} onPress={onPress} />,
    );
    expect(getByText('Chicken Breast')).toBeTruthy();
  });

  it('renders grams and calories', () => {
    const entry = createEntry();
    const { getByText } = render(
      <FoodEntryItem entry={entry} onDelete={onDelete} onPress={onPress} />,
    );
    expect(getByText('200g • 330 kcal')).toBeTruthy();
  });

  it('renders macros', () => {
    const entry = createEntry();
    const { getByText } = render(
      <FoodEntryItem entry={entry} onDelete={onDelete} onPress={onPress} />,
    );
    expect(getByText(/foodDetails.macroP.*62.*foodDetails.macroF.*7.*foodDetails.macroC.*0/)).toBeTruthy();
  });

  it('calls onPress when tapped', () => {
    const entry = createEntry();
    const { getByText } = render(
      <FoodEntryItem entry={entry} onDelete={onDelete} onPress={onPress} />,
    );
    fireEvent.press(getByText('Chicken Breast'));
    expect(onPress).toHaveBeenCalledWith(entry);
  });

  it('shows fallback name when product is null', () => {
    const entry = createEntry({ product: undefined as any });
    const { getByText } = render(
      <FoodEntryItem entry={entry} onDelete={onDelete} onPress={onPress} />,
    );
    expect(getByText('foodDetails.unknownProduct')).toBeTruthy();
  });

  it('rounds grams and calories', () => {
    const entry = createEntry({ amount_grams: 150.7, calories: 248.3 });
    const { getByText } = render(
      <FoodEntryItem entry={entry} onDelete={onDelete} onPress={onPress} />,
    );
    expect(getByText('151g • 248 kcal')).toBeTruthy();
  });

  it('rounds macro values', () => {
    const entry = createEntry({ protein: 31.7, fat: 3.2, carbs: 0.4 });
    const { getByText } = render(
      <FoodEntryItem entry={entry} onDelete={onDelete} onPress={onPress} />,
    );
    expect(getByText(/32.*3.*0/)).toBeTruthy();
  });
});
