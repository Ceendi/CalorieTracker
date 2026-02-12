import { render, fireEvent } from '@testing-library/react-native';

jest.mock('@/hooks/useLanguage', () => ({
  useLanguage: () => ({ t: (k: string) => k, language: 'en', setLanguage: jest.fn() }),
}));
jest.mock('@/hooks/useColorScheme', () => ({
  useColorScheme: () => ({ colorScheme: 'light', toggleColorScheme: jest.fn(), setColorScheme: jest.fn(), isLoaded: true }),
}));
jest.mock('@/constants/theme', () => ({
  Colors: { light: { tint: '#6366f1', text: '#020617', placeholder: '#aaa' }, dark: { tint: '#818cf8', text: '#f8fafc', placeholder: '#666' } },
}));
jest.mock('@/components/ui/IconSymbol', () => ({
  IconSymbol: 'IconSymbol',
}));

import { InfoItem } from '@/components/profile/InfoItem';

describe('InfoItem', () => {
  it('renders label and value in display mode', () => {
    const { getByText } = render(
      <InfoItem label="Height" value="180" icon="ruler" isEditing={false} fieldKey="height" />,
    );
    expect(getByText('Height')).toBeTruthy();
    expect(getByText(/180/)).toBeTruthy();
  });

  it('shows dash when value is empty', () => {
    const { getByText } = render(
      <InfoItem label="Weight" value="" icon="scalemass" isEditing={false} fieldKey="weight" />,
    );
    expect(getByText('-')).toBeTruthy();
  });

  it('shows suffix for number fields', () => {
    const { getByText } = render(
      <InfoItem label="Height" value="175" icon="ruler" isEditing={false} fieldKey="height" isNumber />,
    );
    expect(getByText(/175/)).toBeTruthy();
    expect(getByText(/ cm/)).toBeTruthy();
  });

  it('shows kg suffix for weight field', () => {
    const { getByText } = render(
      <InfoItem label="Weight" value="70" icon="scalemass" isEditing={false} fieldKey="weight" isNumber />,
    );
    expect(getByText(/ kg/)).toBeTruthy();
  });

  it('renders TextInput in editing mode', () => {
    const onChangeText = jest.fn();
    const { getByDisplayValue } = render(
      <InfoItem
        label="Height"
        value="180"
        icon="ruler"
        isEditing={true}
        fieldKey="height"
        isNumber
        onChangeText={onChangeText}
      />,
    );
    expect(getByDisplayValue('180')).toBeTruthy();
  });

  it('calls onChangeText when input changes', () => {
    const onChangeText = jest.fn();
    const { getByDisplayValue } = render(
      <InfoItem
        label="Height"
        value="180"
        icon="ruler"
        isEditing={true}
        fieldKey="height"
        onChangeText={onChangeText}
      />,
    );
    fireEvent.changeText(getByDisplayValue('180'), '185');
    expect(onChangeText).toHaveBeenCalledWith('185');
  });

  it('renders select option display when isSelect in display mode', () => {
    const selectOptions = [
      { label: 'Male', value: 'male' },
      { label: 'Female', value: 'female' },
    ];
    const { getByText } = render(
      <InfoItem
        label="Gender"
        value="male"
        icon="person"
        isEditing={false}
        fieldKey="gender"
        isSelect
        selectOptions={selectOptions}
      />,
    );
    expect(getByText('Male')).toBeTruthy();
  });

  it('calls onOpenSelection when select pressed in edit mode', () => {
    const onOpenSelection = jest.fn();
    const selectOptions = [
      { label: 'Male', value: 'male' },
      { label: 'Female', value: 'female' },
    ];
    const { getByText } = render(
      <InfoItem
        label="Gender"
        value="male"
        icon="person"
        isEditing={true}
        fieldKey="gender"
        isSelect
        selectOptions={selectOptions}
        onOpenSelection={onOpenSelection}
      />,
    );
    fireEvent.press(getByText('Male'));
    expect(onOpenSelection).toHaveBeenCalled();
  });
});
