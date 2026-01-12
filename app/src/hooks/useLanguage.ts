import { useCallback } from 'react';
import { storageService } from '@/services/storage.service';
import { translations, Language } from '@/i18n/translations';
import { create } from 'zustand';
import { getLocales } from 'expo-localization';

interface LanguageState {
  language: Language;
  setLanguage: (lang: Language) => Promise<void>;
  isLoading: boolean;
}

const useLanguageStore = create<LanguageState>((set) => ({
  language: 'en',
  isLoading: true,
  setLanguage: async (lang: Language) => {
    await storageService.setLanguage(lang);
    set({ language: lang });
  },
}));

const initLanguage = async () => {
    const saved = await storageService.getLanguage();
    if (saved === 'pl' || saved === 'en') {
        useLanguageStore.setState({ language: saved, isLoading: false });
    } else {
        const deviceLang = getLocales()[0]?.languageCode;
        const defaultLang = deviceLang === 'pl' ? 'pl' : 'en';
        useLanguageStore.setState({ language: defaultLang, isLoading: false });
    }
}
initLanguage();

export function useLanguage() {
  const language = useLanguageStore((state) => state.language);
  const setLanguage = useLanguageStore((state) => state.setLanguage);

  const t = useCallback((key: string) => {
    const keys = key.split('.');
    let value: any = translations[language];
    for (const k of keys) {
      if (value && typeof value === 'object') {
        value = value[k];
      } else {
        return key; 
      }
    }
    return value || key;
  }, [language]);

  return { language, setLanguage, t };
}
