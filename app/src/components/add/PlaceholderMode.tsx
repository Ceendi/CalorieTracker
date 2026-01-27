import { View, Text, TouchableOpacity } from 'react-native';
import { IconSymbol, IconSymbolName } from '@/components/ui/IconSymbol';
import { useLanguage } from '@/hooks/useLanguage';
import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/useColorScheme';

interface PlaceholderModeProps {
  title: string;
  icon: IconSymbolName;
  description: string;
  actionTitle?: string;
  onAction?: () => void;
}

export function PlaceholderMode({ title, icon, description, actionTitle, onAction }: PlaceholderModeProps) {
  const { t } = useLanguage();
  const { colorScheme } = useColorScheme();
  const theme = colorScheme ?? 'light';

  return (
    <View className="flex-1 items-center justify-center px-8 -mt-20">
      <View className="w-32 h-32 bg-primary/10 rounded-full items-center justify-center mb-8 shadow-sm">
        <IconSymbol name={icon} size={56} color={Colors[theme].tint} />
      </View>
      <Text className="text-2xl font-bold text-foreground mb-4 text-center">{title}</Text>
      <Text className="text-base text-muted-foreground text-center leading-6 mb-8">
        {description}
      </Text>
      
      {onAction && (
        <TouchableOpacity 
          className="bg-primary px-8 py-4 rounded-full shadow-lg shadow-indigo-200 dark:shadow-none"
          onPress={onAction}
        >
          <Text className="text-white text-lg font-bold">{actionTitle || t('addFood.startScanning')}</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}
