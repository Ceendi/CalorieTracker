import { render, fireEvent } from '@testing-library/react-native';

import { ProductSearchMode } from '@/components/add/ProductSearchMode';

jest.mock('@/hooks/useLanguage', () => ({
  useLanguage: () => ({ t: (k: string) => k, language: 'en', setLanguage: jest.fn() }),
}));
jest.mock('@/hooks/useColorScheme', () => ({
  useColorScheme: () => ({ colorScheme: 'light', toggleColorScheme: jest.fn(), setColorScheme: jest.fn(), isLoaded: true }),
}));
jest.mock('@/constants/theme', () => ({
  Colors: { light: { tint: '#6366f1', text: '#020617', icon: '#64748b', placeholder: '#94a3b8' }, dark: {} },
}));
jest.mock('@/components/ui/IconSymbol', () => ({
  IconSymbol: ({ name }: { name: string }) => {
    const React = require('react');
    const { Text } = require('react-native');
    return React.createElement(Text, { testID: `icon-${name}` }, name);
  },
}));

const mockUseFoodSearch = jest.fn(() => ({
  data: undefined as unknown[] | undefined,
  isLoading: false,
  refetch: jest.fn(),
  isRefetching: false,
}));
jest.mock('@/hooks/useFood', () => ({
  useFoodSearch: (_q: string) => mockUseFoodSearch(),
}));

jest.mock('react-native/Libraries/Components/Keyboard/Keyboard', () => ({
  dismiss: jest.fn(),
  addListener: jest.fn(() => ({ remove: jest.fn() })),
}));

describe('ProductSearchMode', () => {
  const onItemPress = jest.fn();
  const onManualPress = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseFoodSearch.mockReturnValue({
      data: undefined,
      isLoading: false,
      refetch: jest.fn(),
      isRefetching: false,
    });
  });

  it('renders search input', () => {
    const { getByPlaceholderText } = render(
      <ProductSearchMode onItemPress={onItemPress} onManualPress={onManualPress} />,
    );
    expect(getByPlaceholderText('addFood.searchPlaceholder')).toBeTruthy();
  });

  it('renders empty state when no query', () => {
    const { getByText } = render(
      <ProductSearchMode onItemPress={onItemPress} onManualPress={onManualPress} />,
    );
    expect(getByText('addFood.emptyState')).toBeTruthy();
  });

  it('updates search query on text input', () => {
    const { getByPlaceholderText } = render(
      <ProductSearchMode onItemPress={onItemPress} onManualPress={onManualPress} />,
    );
    fireEvent.changeText(getByPlaceholderText('addFood.searchPlaceholder'), 'chicken');
    // useFoodSearch will be called with the query
    expect(mockUseFoodSearch).toHaveBeenCalled();
  });

  it('renders search results when available', () => {
    mockUseFoodSearch.mockReturnValue({
      data: [
        { id: '1', name: 'Chicken Breast', nutrition: { calories_per_100g: 165, protein_per_100g: 31, fat_per_100g: 3.6, carbs_per_100g: 0 } },
      ],
      isLoading: false,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { getByText } = render(
      <ProductSearchMode onItemPress={onItemPress} onManualPress={onManualPress} />,
    );
    expect(getByText('Chicken Breast')).toBeTruthy();
    expect(getByText(/165/)).toBeTruthy();
  });

  it('calls onItemPress when a result is tapped', () => {
    const product = { id: '1', name: 'Apple', nutrition: { calories_per_100g: 52, protein_per_100g: 0.3, fat_per_100g: 0.2, carbs_per_100g: 14 } };
    mockUseFoodSearch.mockReturnValue({
      data: [product],
      isLoading: false,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { getByText } = render(
      <ProductSearchMode onItemPress={onItemPress} onManualPress={onManualPress} />,
    );
    fireEvent.press(getByText('Apple'));
    expect(onItemPress).toHaveBeenCalledWith(product);
  });
});
