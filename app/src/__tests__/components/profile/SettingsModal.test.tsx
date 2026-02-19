import { render, fireEvent } from '@testing-library/react-native';

import { SettingsModal } from '@/components/profile/SettingsModal';

jest.mock('@/hooks/useLanguage', () => ({
  useLanguage: () => ({ t: (k: string) => k, language: 'en', setLanguage: jest.fn() }),
}));
jest.mock('@/hooks/useColorScheme', () => ({
  useColorScheme: () => ({ colorScheme: 'light', toggleColorScheme: jest.fn(), setColorScheme: jest.fn(), isLoaded: true }),
}));
jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({ signOut: jest.fn() }),
}));
jest.mock('@/constants/theme', () => ({
  Colors: { light: { tint: '#6366f1', text: '#020617' }, dark: { tint: '#818cf8', text: '#f8fafc' } },
}));
jest.mock('@/components/ui/IconSymbol', () => ({
  IconSymbol: 'IconSymbol',
}));
jest.mock('@/components/profile/ChangePasswordModal', () => ({
  ChangePasswordModal: () => null,
}));

describe('SettingsModal', () => {
  const onClose = jest.fn();

  beforeEach(() => jest.clearAllMocks());

  it('renders settings title when visible', () => {
    const { getByText } = render(
      <SettingsModal visible={true} onClose={onClose} />,
    );
    expect(getByText('settings.title')).toBeTruthy();
  });

  it('renders dark mode toggle', () => {
    const { getByText } = render(
      <SettingsModal visible={true} onClose={onClose} />,
    );
    expect(getByText('settings.darkMode')).toBeTruthy();
  });

  it('renders language option', () => {
    const { getByText } = render(
      <SettingsModal visible={true} onClose={onClose} />,
    );
    expect(getByText('settings.language')).toBeTruthy();
  });

  it('renders change password in authenticated mode', () => {
    const { getByText } = render(
      <SettingsModal visible={true} onClose={onClose} mode="authenticated" />,
    );
    expect(getByText('settings.changePassword')).toBeTruthy();
  });

  it('renders logout button in authenticated mode', () => {
    const { getByText } = render(
      <SettingsModal visible={true} onClose={onClose} mode="authenticated" />,
    );
    expect(getByText('settings.logout')).toBeTruthy();
  });

  it('hides account section in public mode', () => {
    const { queryByText } = render(
      <SettingsModal visible={true} onClose={onClose} mode="public" />,
    );
    expect(queryByText('settings.changePassword')).toBeNull();
    expect(queryByText('settings.logout')).toBeNull();
  });
});
