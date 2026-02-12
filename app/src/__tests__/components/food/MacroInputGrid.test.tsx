import { render } from '@testing-library/react-native';
import React from 'react';
import { useForm } from 'react-hook-form';

jest.mock('@/hooks/useLanguage', () => ({
  useLanguage: () => ({ t: (k: string) => k, language: 'en', setLanguage: jest.fn() }),
}));
jest.mock('@/hooks/useColorScheme', () => ({
  useColorScheme: () => ({ colorScheme: 'light', toggleColorScheme: jest.fn(), setColorScheme: jest.fn(), isLoaded: true }),
}));
jest.mock('@/constants/theme', () => ({
  Colors: { light: { tint: '#6366f1', text: '#020617', placeholder: '#94a3b8' }, dark: {} },
}));

import { MacroInputGrid } from '@/components/food/MacroInputGrid';

interface ManualFoodFormValues {
  name: string;
  calories: number;
  protein: number;
  fat: number;
  carbs: number;
  weight: number;
  barcode?: string;
}

function TestWrapper() {
  const { control } = useForm<ManualFoodFormValues>({
    defaultValues: { name: '', calories: 100, protein: 10, fat: 5, carbs: 20, weight: 100 },
  });
  return <MacroInputGrid control={control as any} />;
}

describe('MacroInputGrid', () => {
  it('renders all four macro inputs', () => {
    const { getByText } = render(<TestWrapper />);
    expect(getByText('manualEntry.calories')).toBeTruthy();
    expect(getByText('manualEntry.protein')).toBeTruthy();
    expect(getByText('manualEntry.fat')).toBeTruthy();
    expect(getByText('manualEntry.carbs')).toBeTruthy();
  });

  it('displays initial values from form', () => {
    const { getByDisplayValue } = render(<TestWrapper />);
    expect(getByDisplayValue('100')).toBeTruthy(); // calories
    expect(getByDisplayValue('10')).toBeTruthy(); // protein
    expect(getByDisplayValue('5')).toBeTruthy(); // fat
    expect(getByDisplayValue('20')).toBeTruthy(); // carbs
  });

  it('renders without crashing', () => {
    const { toJSON } = render(<TestWrapper />);
    expect(toJSON()).toBeTruthy();
  });
});
