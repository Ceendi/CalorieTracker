import { render, fireEvent } from '@testing-library/react-native';

import { QuantitySelector } from '@/components/food/QuantitySelector';
import { UnitInfo } from '@/types/food';

jest.mock('@/hooks/useLanguage', () => ({
  useLanguage: () => ({ t: (k: string) => k, language: 'en', setLanguage: jest.fn() }),
}));
jest.mock('@/hooks/useColorScheme', () => ({
  useColorScheme: () => ({ colorScheme: 'light', toggleColorScheme: jest.fn(), setColorScheme: jest.fn(), isLoaded: true }),
}));
jest.mock('@/constants/theme', () => ({
  Colors: { light: { tint: '#6366f1', text: '#020617', mutedForeground: '#64748b', placeholder: '#94a3b8' }, dark: {} },
}));
jest.mock('@/components/ui/IconSymbol', () => ({
  IconSymbol: ({ name }: { name: string }) => {
    const React = require('react');
    const { Text } = require('react-native');
    return React.createElement(Text, { testID: `icon-${name}` }, name);
  },
}));

describe('QuantitySelector', () => {
  const onChangeQuantity = jest.fn();
  const onSelectUnit = jest.fn();

  const pieceUnit: UnitInfo = { unit: 'piece', grams: 60, label: 'piece' };
  const cupUnit: UnitInfo = { unit: 'cup', grams: 240, label: 'cup' };

  beforeEach(() => jest.clearAllMocks());

  it('renders quantity input with current value', () => {
    const { getByDisplayValue } = render(
      <QuantitySelector
        quantity="100"
        onChangeQuantity={onChangeQuantity}
        selectedUnit={null}
        units={undefined}
        onSelectUnit={onSelectUnit}
      />,
    );
    expect(getByDisplayValue('100')).toBeTruthy();
  });

  it('calls onChangeQuantity when text changes', () => {
    const { getByDisplayValue } = render(
      <QuantitySelector
        quantity="100"
        onChangeQuantity={onChangeQuantity}
        selectedUnit={null}
        units={undefined}
        onSelectUnit={onSelectUnit}
      />,
    );
    fireEvent.changeText(getByDisplayValue('100'), '250');
    expect(onChangeQuantity).toHaveBeenCalledWith('250');
  });

  it('increments by 10 for grams (no unit)', () => {
    const { getByLabelText } = render(
      <QuantitySelector
        quantity="100"
        onChangeQuantity={onChangeQuantity}
        selectedUnit={null}
        units={undefined}
        onSelectUnit={onSelectUnit}
      />,
    );
    fireEvent.press(getByLabelText('accessibility.increaseQuantity'));
    expect(onChangeQuantity).toHaveBeenCalledWith('110');
  });

  it('decrements by 10 for grams (no unit)', () => {
    const { getByLabelText } = render(
      <QuantitySelector
        quantity="100"
        onChangeQuantity={onChangeQuantity}
        selectedUnit={null}
        units={undefined}
        onSelectUnit={onSelectUnit}
      />,
    );
    fireEvent.press(getByLabelText('accessibility.decreaseQuantity'));
    expect(onChangeQuantity).toHaveBeenCalledWith('90');
  });

  it('increments by 1 when unit is selected', () => {
    const { getByLabelText } = render(
      <QuantitySelector
        quantity="2"
        onChangeQuantity={onChangeQuantity}
        selectedUnit={pieceUnit}
        units={[pieceUnit]}
        onSelectUnit={onSelectUnit}
      />,
    );
    fireEvent.press(getByLabelText('accessibility.increaseQuantity'));
    expect(onChangeQuantity).toHaveBeenCalledWith('3');
  });

  it('decrements by 1 when unit is selected, min 1', () => {
    const { getByLabelText } = render(
      <QuantitySelector
        quantity="1"
        onChangeQuantity={onChangeQuantity}
        selectedUnit={pieceUnit}
        units={[pieceUnit]}
        onSelectUnit={onSelectUnit}
      />,
    );
    fireEvent.press(getByLabelText('accessibility.decreaseQuantity'));
    expect(onChangeQuantity).toHaveBeenCalledWith('1'); // min is 1
  });

  it('shows gram equivalent when unit is selected', () => {
    const { getByText } = render(
      <QuantitySelector
        quantity="3"
        onChangeQuantity={onChangeQuantity}
        selectedUnit={pieceUnit}
        units={[pieceUnit]}
        onSelectUnit={onSelectUnit}
      />,
    );
    expect(getByText('= 180 g')).toBeTruthy();
  });

  it('shows unit label when unit is selected', () => {
    const { getByText } = render(
      <QuantitySelector
        quantity="2"
        onChangeQuantity={onChangeQuantity}
        selectedUnit={pieceUnit}
        units={[pieceUnit, cupUnit]}
        onSelectUnit={onSelectUnit}
      />,
    );
    expect(getByText('piece (60g)')).toBeTruthy();
  });

  it('shows grams label when no unit selected', () => {
    const { getAllByText } = render(
      <QuantitySelector
        quantity="100"
        onChangeQuantity={onChangeQuantity}
        selectedUnit={null}
        units={undefined}
        onSelectUnit={onSelectUnit}
      />,
    );
    expect(getAllByText('foodDetails.grams').length).toBeGreaterThan(0);
  });

  it('renders quantity label', () => {
    const { getByText } = render(
      <QuantitySelector
        quantity="100"
        onChangeQuantity={onChangeQuantity}
        selectedUnit={null}
        units={undefined}
        onSelectUnit={onSelectUnit}
      />,
    );
    expect(getByText('manualEntry.quantity')).toBeTruthy();
  });
});
