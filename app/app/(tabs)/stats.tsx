import { View, Text } from 'react-native';
import { useLanguage } from '@/hooks/useLanguage';

export default function StatsScreen() {
  const { t } = useLanguage();
  
  return (
    <View className="flex-1 items-center justify-center bg-background">
      <Text className="text-xl font-bold text-foreground">
        {t('dashboard.stats') || 'Stats'}
      </Text>
      <Text className="text-muted-foreground mt-2">
        {t('common.comingSoon') || 'Coming Soon'}
      </Text>
    </View>
  );
}
