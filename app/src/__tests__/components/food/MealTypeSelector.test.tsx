import { render, fireEvent } from '@testing-library/react-native';

import { MealTypeSelector } from '@/components/food/MealTypeSelector';
import { MealType } from '@/types/food';

jest.mock('@/hooks/useLanguage', () => ({
  useLanguage: () => ({ t: (k: string) => k, language: 'en', setLanguage: jest.fn() }),
}));

describe('MealTypeSelector', () => {
  const onSelect = jest.fn();

  beforeEach(() => jest.clearAllMocks());

  it('renders all four meal type options', () => {
    const { getByText } = render(
      <MealTypeSelector selectedMeal={MealType.BREAKFAST} onSelect={onSelect} />,
    );
    expect(getByText('meals.breakfast')).toBeTruthy();
    expect(getByText('meals.lunch')).toBeTruthy();
    expect(getByText('meals.snack')).toBeTruthy();
    expect(getByText('meals.dinner')).toBeTruthy();
  });

  it('renders section label', () => {
    const { getByText } = render(
      <MealTypeSelector selectedMeal={MealType.BREAKFAST} onSelect={onSelect} />,
    );
    expect(getByText('manualEntry.mealLabel')).toBeTruthy();
  });

  it('calls onSelect when option is pressed', () => {
    const { getByText } = render(
      <MealTypeSelector selectedMeal={MealType.BREAKFAST} onSelect={onSelect} />,
    );
    fireEvent.press(getByText('meals.dinner'));
    expect(onSelect).toHaveBeenCalledWith(MealType.DINNER);
  });

  it('calls onSelect with each meal type', () => {
    const { getByText } = render(
      <MealTypeSelector selectedMeal={MealType.BREAKFAST} onSelect={onSelect} />,
    );
    fireEvent.press(getByText('meals.lunch'));
    expect(onSelect).toHaveBeenCalledWith(MealType.LUNCH);

    fireEvent.press(getByText('meals.snack'));
    expect(onSelect).toHaveBeenCalledWith(MealType.SNACK);
  });

  it('renders with different selectedMeal values', () => {
    const { getByText } = render(
      <MealTypeSelector selectedMeal={MealType.DINNER} onSelect={onSelect} />,
    );
    // All options should still be rendered
    expect(getByText('meals.breakfast')).toBeTruthy();
    expect(getByText('meals.dinner')).toBeTruthy();
  });
});
