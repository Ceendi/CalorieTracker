import { useColorScheme as useNativeWindColorScheme } from 'nativewind';
import { useEffect, useState } from 'react';
import { storageService } from '@/services/storage.service';

export function useColorScheme() {
  const { colorScheme, setColorScheme } = useNativeWindColorScheme();
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    const loadTheme = async () => {
      try {
        const savedTheme = await storageService.getTheme();
        if (savedTheme === 'dark' || savedTheme === 'light') {
          setColorScheme(savedTheme);
        }
      } catch (e) {
        console.log('Failed to load theme preference', e);
      } finally {
        setIsLoaded(true);
      }
    };
    loadTheme();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // intentional: load once on mount — setColorScheme from nativewind is not a stable reference

  const toggleColorScheme = async () => {
    const newScheme = colorScheme === 'dark' ? 'light' : 'dark';
    setColorScheme(newScheme);
    await storageService.setTheme(newScheme);
    return newScheme;
  };

  const setColorSchemeWithPersist = async (scheme: 'light' | 'dark' | 'system') => {
    setColorScheme(scheme);
    await storageService.setTheme(scheme);
  };

  return {
    colorScheme,
    toggleColorScheme,
    setColorScheme: setColorSchemeWithPersist,
    isLoaded
  };
}
