import { render, fireEvent } from '@testing-library/react-native';

import { DateNavigator } from '@/components/diary/DateNavigator';
import { format } from 'date-fns';

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
  IconSymbol: ({ name }: { name: string }) => {
    const React = require('react');
    const { Text } = require('react-native');
    return React.createElement(Text, { testID: `icon-${name}` }, name);
  },
}));

describe('DateNavigator', () => {
  const onDateChange = jest.fn();

  beforeEach(() => jest.clearAllMocks());

  it('displays "Today" for current date', () => {
    const { getByText } = render(
      <DateNavigator date={new Date()} onDateChange={onDateChange} />,
    );
    expect(getByText('Today')).toBeTruthy();
  });

  it('displays formatted date for non-today dates', () => {
    const date = new Date(2024, 0, 15); // January 15 2024
    const { queryByText } = render(
      <DateNavigator date={date} onDateChange={onDateChange} />,
    );
    expect(queryByText('Today')).toBeNull();
  });

  it('calls onDateChange with previous day on left press', () => {
    const date = new Date(2024, 5, 15); // June 15
    const { getByTestId } = render(
      <DateNavigator date={date} onDateChange={onDateChange} />,
    );
    // Find the left chevron icon and press its parent
    const leftIcon = getByTestId('icon-chevron.left');
    fireEvent.press(leftIcon);
    // Should be called with June 14
    expect(onDateChange).toHaveBeenCalledTimes(1);
    const calledDate = onDateChange.mock.calls[0][0];
    expect(format(calledDate, 'yyyy-MM-dd')).toBe('2024-06-14');
  });

  it('calls onDateChange with next day on right press', () => {
    const date = new Date(2024, 5, 15);
    const { getByTestId } = render(
      <DateNavigator date={date} onDateChange={onDateChange} />,
    );
    const rightIcon = getByTestId('icon-chevron.right');
    fireEvent.press(rightIcon);
    const calledDate = onDateChange.mock.calls[0][0];
    expect(format(calledDate, 'yyyy-MM-dd')).toBe('2024-06-16');
  });

  it('renders both navigation chevrons', () => {
    const date = new Date(2024, 5, 15);
    const { getByTestId } = render(
      <DateNavigator date={date} onDateChange={onDateChange} />,
    );
    expect(getByTestId('icon-chevron.left')).toBeTruthy();
    expect(getByTestId('icon-chevron.right')).toBeTruthy();
  });
});
