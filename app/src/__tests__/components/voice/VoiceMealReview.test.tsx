import { render, fireEvent } from '@testing-library/react-native';

import { VoiceMealReview } from '@/components/voice/confirmation/VoiceMealReview';
import { ProcessedMeal } from '@/types/ai';

jest.mock('@/hooks/useColorScheme', () => ({
  useColorScheme: () => ({ colorScheme: 'light', toggleColorScheme: jest.fn(), setColorScheme: jest.fn(), isLoaded: true }),
}));
jest.mock('@/constants/theme', () => ({
  Colors: {
    light: { tint: '#6366f1', text: '#020617', tabIconDefault: '#94a3b8' },
    dark: { tint: '#818cf8', text: '#f8fafc', tabIconDefault: '#64748b' },
  },
}));
jest.mock('@/components/ui/IconSymbol', () => ({
  IconSymbol: ({ name }: { name: string }) => {
    const React = require('react');
    const { Text } = require('react-native');
    return React.createElement(Text, { testID: `icon-${name}` }, name);
  },
}));
jest.mock('@/components/voice/confirmation/VoiceMealSummary', () => ({
  VoiceMealSummary: ({ onConfirm, isLoading, t }: any) => {
    const React = require('react');
    const { TouchableOpacity, Text } = require('react-native');
    return React.createElement(TouchableOpacity, { onPress: onConfirm, testID: 'confirm-btn' },
      React.createElement(Text, null, 'Confirm'),
    );
  },
}));

const t = (k: string) => k;

const createMeal = (overrides?: Partial<ProcessedMeal>): ProcessedMeal => ({
  meal_type: 'lunch',
  items: [
    {
      product_id: "1",
      name: 'Chicken',
      quantity_grams: 200,
      kcal: 330,
      protein: 62,
      fat: 7,
      carbs: 0,
      confidence: 0.95,
      unit_matched: 'g',
      quantity_unit_value: 200,
      status: 'matched',
    },
    {
      product_id: "2",
      name: 'Rice',
      quantity_grams: 150,
      kcal: 195,
      protein: 4,
      fat: 0.4,
      carbs: 43,
      confidence: 0.9,
      unit_matched: 'g',
      quantity_unit_value: 150,
      status: 'matched',
    },
  ],
  raw_transcription: 'chicken with rice',
  processing_time_ms: 500,
  ...overrides,
});

const defaultProps = {
  textColor: '#020617',
  cycleMealType: jest.fn(),
  getMealTypeLabel: (type: string) => `meal-${type}`,
  onEditItem: jest.fn(),
  handleRemoveItem: jest.fn(),
  setIsSearching: jest.fn(),
  totals: { kcal: 525, protein: 66, fat: 7.4, carbs: 43 },
  onConfirm: jest.fn(),
  onCancel: jest.fn(),
  t,
};

describe('VoiceMealReview', () => {
  beforeEach(() => jest.clearAllMocks());

  it('renders food items', () => {
    const meal = createMeal();
    const { getByText } = render(
      <VoiceMealReview {...defaultProps} localMeal={meal} />,
    );
    expect(getByText('Chicken')).toBeTruthy();
    expect(getByText('Rice')).toBeTruthy();
  });

  it('renders raw transcription', () => {
    const meal = createMeal();
    const { getByText } = render(
      <VoiceMealReview {...defaultProps} localMeal={meal} />,
    );
    expect(getByText(/chicken with rice/)).toBeTruthy();
  });

  it('renders meal type label', () => {
    const meal = createMeal();
    const { getByText } = render(
      <VoiceMealReview {...defaultProps} localMeal={meal} />,
    );
    expect(getByText('meal-lunch')).toBeTruthy();
  });

  it('calls cycleMealType on meal type press', () => {
    const meal = createMeal();
    const { getByText } = render(
      <VoiceMealReview {...defaultProps} localMeal={meal} />,
    );
    fireEvent.press(getByText('meal-lunch'));
    expect(defaultProps.cycleMealType).toHaveBeenCalled();
  });

  it('calls onCancel on cancel press', () => {
    const meal = createMeal();
    const { getAllByTestId } = render(
      <VoiceMealReview {...defaultProps} localMeal={meal} />,
    );
    // First xmark is the cancel button, others are per-item remove buttons
    fireEvent.press(getAllByTestId('icon-xmark')[0]);
    expect(defaultProps.onCancel).toHaveBeenCalled();
  });

  it('calls onConfirm via VoiceMealSummary', () => {
    const meal = createMeal();
    const { getByTestId } = render(
      <VoiceMealReview {...defaultProps} localMeal={meal} />,
    );
    fireEvent.press(getByTestId('confirm-btn'));
    expect(defaultProps.onConfirm).toHaveBeenCalled();
  });

  it('calls setIsSearching when add button is pressed', () => {
    const meal = createMeal();
    const { getByText } = render(
      <VoiceMealReview {...defaultProps} localMeal={meal} />,
    );
    fireEvent.press(getByText('addFood.searchToConfirm'));
    expect(defaultProps.setIsSearching).toHaveBeenCalledWith(true);
  });

  it('renders quantity in grams for gram unit', () => {
    const meal = createMeal();
    const { getByText } = render(
      <VoiceMealReview {...defaultProps} localMeal={meal} />,
    );
    expect(getByText('200')).toBeTruthy(); // quantity_grams for gram unit
    expect(getByText('150')).toBeTruthy();
  });

  it('renders unit_value for non-gram units', () => {
    const meal = createMeal({
      items: [{
        product_id: "3",
        name: 'Eggs',
        quantity_grams: 120,
        kcal: 186,
        protein: 15.6,
        fat: 13.2,
        carbs: 1.3,
        confidence: 0.9,
        unit_matched: 'piece',
        quantity_unit_value: 2,
        status: 'matched',
      }],
    });
    const { getByText } = render(
      <VoiceMealReview {...defaultProps} localMeal={meal} />,
    );
    expect(getByText('2')).toBeTruthy(); // quantity_unit_value
    expect(getByText('piece')).toBeTruthy(); // unit label
  });

  it('renders empty list without crashing', () => {
    const meal = createMeal({ items: [] });
    const { getByText } = render(
      <VoiceMealReview {...defaultProps} localMeal={meal} />,
    );
    expect(getByText('addFood.searchToConfirm')).toBeTruthy();
  });
});
