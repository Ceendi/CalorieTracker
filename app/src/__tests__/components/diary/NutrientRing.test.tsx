import { render } from '@testing-library/react-native';

import { NutrientRing } from '@/components/diary/NutrientRing';

jest.mock('@/constants/theme', () => ({
  Colors: { light: { tint: '#6366f1' }, dark: { tint: '#818cf8' } },
}));

describe('NutrientRing', () => {
  it('renders label and values', () => {
    const { getByText } = render(
      <NutrientRing label="Protein" current={50} total={100} unit="g" color="#ff0000" />,
    );
    expect(getByText('Protein')).toBeTruthy();
    expect(getByText('50%')).toBeTruthy();
  });

  it('clamps progress to 100%', () => {
    const { getByText } = render(
      <NutrientRing label="Carbs" current={200} total={100} unit="g" color="#00ff00" />,
    );
    // Math.min(200/100, 1) = 1 → 100%
    expect(getByText('100%')).toBeTruthy();
  });

  it('renders current and total amounts', () => {
    const { getByText } = render(
      <NutrientRing label="Fat" current={30} total={65} unit="g" color="#0000ff" />,
    );
    expect(getByText('46%')).toBeTruthy(); // Math.round(30/65 * 100) = 46
  });

  it('renders with zero values', () => {
    const { getByText } = render(
      <NutrientRing label="Cals" current={0} total={2000} unit="kcal" color="#ffcc00" />,
    );
    expect(getByText('0%')).toBeTruthy();
  });
});
