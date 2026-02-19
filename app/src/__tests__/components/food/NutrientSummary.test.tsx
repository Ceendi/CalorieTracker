import { render } from '@testing-library/react-native';

import { NutrientSummary } from '@/components/food/NutrientSummary';

jest.mock('@/hooks/useLanguage', () => ({
  useLanguage: () => ({ t: (k: string) => k, language: 'en', setLanguage: jest.fn() }),
}));

describe('NutrientSummary', () => {
  it('renders all four macro values', () => {
    const { getByText } = render(
      <NutrientSummary calories={250} protein={12.34} fat={8.56} carbs={30.12} />,
    );
    expect(getByText('250')).toBeTruthy();
    expect(getByText('12.3g')).toBeTruthy();
    expect(getByText('8.6g')).toBeTruthy();
    expect(getByText('30.1g')).toBeTruthy();
  });

  it('rounds calories to nearest integer', () => {
    const { getByText } = render(
      <NutrientSummary calories={99.7} protein={0} fat={0} carbs={0} />,
    );
    expect(getByText('100')).toBeTruthy();
  });

  it('displays macros with one decimal place', () => {
    const { getByText } = render(
      <NutrientSummary calories={0} protein={0.05} fat={1} carbs={2.999} />,
    );
    expect(getByText('0.1g')).toBeTruthy(); // 0.05 rounds to 0.1
    expect(getByText('1.0g')).toBeTruthy();
    expect(getByText('3.0g')).toBeTruthy();
  });

  it('renders labels from translations', () => {
    const { getByText } = render(
      <NutrientSummary calories={0} protein={0} fat={0} carbs={0} />,
    );
    expect(getByText('manualEntry.calories')).toBeTruthy();
    expect(getByText('manualEntry.protein')).toBeTruthy();
    expect(getByText('manualEntry.fat')).toBeTruthy();
    expect(getByText('manualEntry.carbs')).toBeTruthy();
  });
});
