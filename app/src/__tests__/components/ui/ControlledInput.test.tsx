import { render, fireEvent } from '@testing-library/react-native';
import { useForm } from 'react-hook-form';
import React from 'react';

import { ControlledInput } from '@/components/ui/ControlledInput';

jest.mock('@/hooks/useColorScheme', () => ({
  useColorScheme: () => ({ colorScheme: 'light', toggleColorScheme: jest.fn(), setColorScheme: jest.fn(), isLoaded: true }),
}));
jest.mock('@/constants/theme', () => ({
  Colors: { light: { tint: '#6366f1', text: '#020617', placeholder: '#94a3b8' }, dark: {} },
}));

interface TestForm {
  email: string;
  name: string;
}

function TestWrapper({ error, label }: { error?: string; label?: string }) {
  const { control } = useForm<TestForm>({
    defaultValues: { email: 'test@example.com', name: '' },
  });
  return (
    <ControlledInput
      control={control}
      name="email"
      label={label}
      error={error}
      placeholder="Enter email"
    />
  );
}

describe('ControlledInput', () => {
  it('renders with label', () => {
    const { getByText } = render(<TestWrapper label="Email" />);
    expect(getByText('Email')).toBeTruthy();
  });

  it('renders without label', () => {
    const { queryByText } = render(<TestWrapper />);
    expect(queryByText('Email')).toBeNull();
  });

  it('displays current value from form', () => {
    const { getByDisplayValue } = render(<TestWrapper />);
    expect(getByDisplayValue('test@example.com')).toBeTruthy();
  });

  it('shows error message when error prop is provided', () => {
    const { getByText } = render(<TestWrapper error="Invalid email" />);
    expect(getByText('Invalid email')).toBeTruthy();
  });

  it('does not show error when no error prop', () => {
    const { queryByText } = render(<TestWrapper />);
    expect(queryByText('Invalid email')).toBeNull();
  });

  it('renders placeholder', () => {
    const { getByPlaceholderText } = render(<TestWrapper />);
    expect(getByPlaceholderText('Enter email')).toBeTruthy();
  });
});
