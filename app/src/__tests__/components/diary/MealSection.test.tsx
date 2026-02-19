import { render, fireEvent } from '@testing-library/react-native';

import { MealSection } from '@/components/diary/MealSection';
import { MealType, MealEntry } from '@/types/food';

jest.mock('@/hooks/useLanguage', () => ({
  useLanguage: () => ({ t: (k: string) => k, language: 'en', setLanguage: jest.fn() }),
}));
jest.mock('@/hooks/useColorScheme', () => ({
  useColorScheme: () => ({ colorScheme: 'light', toggleColorScheme: jest.fn(), setColorScheme: jest.fn(), isLoaded: true }),
}));
jest.mock('@/constants/theme', () => ({
  Colors: { light: { tint: '#6366f1', text: '#020617' }, dark: { tint: '#818cf8', text: '#f8fafc' } },
}));
jest.mock('@/components/ui/IconSymbol', () => ({
  IconSymbol: 'IconSymbol',
}));
jest.mock('@/components/diary/FoodEntryItem', () => ({
  FoodEntryItem: ({ entry, onDelete, onPress }: any) => {
    const React = require('react');
    const { Text, TouchableOpacity } = require('react-native');
    return React.createElement(TouchableOpacity, { onPress: () => onPress(entry) },
      React.createElement(Text, null, entry.product?.name || 'Unknown'),
    );
  },
}));

const createEntry = (id: string, name: string, calories: number): MealEntry => ({
  id,
  product_id: `prod-${id}`,
  product: {
    id: `prod-${id}`,
    name,
    nutrition: { calories_per_100g: 100, protein_per_100g: 10, fat_per_100g: 5, carbs_per_100g: 20 },
  },
  date: '2024-01-15',
  meal_type: MealType.BREAKFAST,
  amount_grams: 100,
  calories,
  protein: 10,
  fat: 5,
  carbs: 20,
});

describe('MealSection', () => {
  const onAdd = jest.fn();
  const onDeleteEntry = jest.fn();
  const onEditEntry = jest.fn();

  beforeEach(() => jest.clearAllMocks());

  it('renders meal type header', () => {
    const { getByText } = render(
      <MealSection
        type={MealType.BREAKFAST}
        entries={[]}
        onAdd={onAdd}
        onDeleteEntry={onDeleteEntry}
        onEditEntry={onEditEntry}
      />,
    );
    expect(getByText('meals.breakfast')).toBeTruthy();
  });

  it('renders total calories for entries', () => {
    const entries = [
      createEntry('1', 'Eggs', 155),
      createEntry('2', 'Toast', 80),
    ];
    const { getByText } = render(
      <MealSection
        type={MealType.BREAKFAST}
        entries={entries}
        onAdd={onAdd}
        onDeleteEntry={onDeleteEntry}
        onEditEntry={onEditEntry}
      />,
    );
    expect(getByText('235 kcal')).toBeTruthy();
  });

  it('renders quick add button', () => {
    const { getByText } = render(
      <MealSection
        type={MealType.LUNCH}
        entries={[]}
        onAdd={onAdd}
        onDeleteEntry={onDeleteEntry}
        onEditEntry={onEditEntry}
      />,
    );
    expect(getByText('dashboard.quickAdd')).toBeTruthy();
  });

  it('calls onAdd with meal type when quick add is pressed', () => {
    const { getByText } = render(
      <MealSection
        type={MealType.LUNCH}
        entries={[]}
        onAdd={onAdd}
        onDeleteEntry={onDeleteEntry}
        onEditEntry={onEditEntry}
      />,
    );
    fireEvent.press(getByText('dashboard.quickAdd'));
    expect(onAdd).toHaveBeenCalledWith(MealType.LUNCH);
  });

  it('shows 0 kcal for empty entries', () => {
    const { getByText } = render(
      <MealSection
        type={MealType.DINNER}
        entries={[]}
        onAdd={onAdd}
        onDeleteEntry={onDeleteEntry}
        onEditEntry={onEditEntry}
      />,
    );
    expect(getByText('0 kcal')).toBeTruthy();
  });

  it('rounds total calories', () => {
    const entries = [
      createEntry('1', 'Apple', 52.3),
      createEntry('2', 'Banana', 89.7),
    ];
    const { getByText } = render(
      <MealSection
        type={MealType.SNACK}
        entries={entries}
        onAdd={onAdd}
        onDeleteEntry={onDeleteEntry}
        onEditEntry={onEditEntry}
      />,
    );
    expect(getByText('142 kcal')).toBeTruthy();
  });
});
