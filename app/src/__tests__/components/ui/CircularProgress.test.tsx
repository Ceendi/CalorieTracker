import { render } from '@testing-library/react-native';

import { CircularProgress } from '@/components/ui/CircularProgress';
import React from 'react';
import { Text } from 'react-native';

jest.mock('@/constants/theme', () => ({
  Colors: { light: { tint: '#6366f1' }, dark: { tint: '#818cf8' } },
}));

describe('CircularProgress', () => {
  it('renders without crashing', () => {
    const { toJSON } = render(<CircularProgress progress={0.5} />);
    expect(toJSON()).toBeTruthy();
  });

  it('renders children in center', () => {
    const { getByText } = render(
      <CircularProgress progress={0.75}>
        <Text>75%</Text>
      </CircularProgress>,
    );
    expect(getByText('75%')).toBeTruthy();
  });

  it('renders with custom size and strokeWidth', () => {
    const { toJSON } = render(
      <CircularProgress progress={0.3} size={200} strokeWidth={20} />,
    );
    expect(toJSON()).toBeTruthy();
  });

  it('renders with custom colors', () => {
    const { toJSON } = render(
      <CircularProgress progress={1} color="#ff0000" bgColor="#cccccc" />,
    );
    expect(toJSON()).toBeTruthy();
  });
});
