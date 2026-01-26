import { CameraView, useCameraPermissions } from 'expo-camera';
import { Stack, useRouter } from 'expo-router';
import { Text, TouchableOpacity, View, ActivityIndicator } from 'react-native';
import { useState } from 'react';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { Colors } from '@/constants/theme';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLanguage } from '@/hooks/useLanguage';

export default function ScannerScreen() {
  const [permission, requestPermission] = useCameraPermissions();
  const router = useRouter();
  const { colorScheme } = useColorScheme();
  const { t } = useLanguage();
  const [scanned, setScanned] = useState(false);

  if (!permission) {
    return (
        <View className="flex-1 justify-center items-center bg-background">
            <ActivityIndicator size="large" color={Colors.light.tint} />
        </View>
    );
  }

  if (!permission.granted) {
    return (
      <View className="flex-1 bg-background justify-center items-center p-6">
        <Stack.Screen options={{ title: t('addFood.modes.scan'), headerBackTitle: t('settings.cancel') }} />
        <View className="bg-card p-8 rounded-3xl shadow-sm items-center w-full max-w-sm border border-border">
            <View className="w-16 h-16 bg-primary/10 rounded-full items-center justify-center mb-6">
                 <IconSymbol name="camera.fill" size={32} color={Colors[colorScheme ?? 'light'].tint} />
            </View>
            <Text className="text-xl font-bold text-foreground text-center mb-3">
                {t('scanner.permissionTitle')}
            </Text>
            <Text className="text-base text-muted-foreground text-center mb-8 leading-6">
                 {t('scanner.permissionMessage')}
            </Text>
            <TouchableOpacity 
                onPress={requestPermission} 
                className="bg-primary w-full py-4 rounded-xl items-center shadow-lg shadow-primary/20"
            >
                <Text className="text-primary-foreground text-lg font-bold">{t('scanner.grantPermission')}</Text>
            </TouchableOpacity>
        </View>
      </View>
    );
  }

  const handleBarCodeScanned = ({ data }: { data: string }) => {
    if (scanned) return;
    setScanned(true);
    router.replace({ pathname: '/food-details', params: { barcode: data } });
  };

  return (
    <View className="flex-1 bg-black">
      <Stack.Screen options={{ headerShown: false }} />
      <CameraView
        style={{ flex: 1 }}
        facing="back"
        onBarcodeScanned={scanned ? undefined : handleBarCodeScanned}
        barcodeScannerSettings={{
          barcodeTypes: ["ean13", "ean8", "upc_e", "upc_a", "qr"], 
        }}
      >
          <SafeAreaView className="flex-1 justify-between">
            <View className="p-4 items-end">
                <TouchableOpacity 
                    onPress={() => router.back()}
                    className="w-10 h-10 bg-black/50 items-center justify-center rounded-full"
                >
                    <IconSymbol name="xmark" size={20} color="white" />
                </TouchableOpacity>
            </View>

            <View className="flex-1 justify-center items-center">
                <View className="w-64 h-64 border-2 border-white/50 rounded-3xl items-center justify-center relative">
                     <View className="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 border-white rounded-tl-2xl -mt-0.5 -ml-0.5" />
                     <View className="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 border-white rounded-tr-2xl -mt-0.5 -mr-0.5" />
                     <View className="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 border-white rounded-bl-2xl -mb-0.5 -ml-0.5" />
                     <View className="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 border-white rounded-br-2xl -mb-0.5 -mr-0.5" />
                </View>
                <Text className="text-white/80 font-medium text-lg mt-8 bg-black/50 px-6 py-2 rounded-full overflow-hidden">
                    {t('scanner.scanInstruction')}
                </Text>
            </View>
            
             <View className="p-8 items-center">
                 <Text className="text-white/50 text-sm">
                     {t('scanner.alignInstruction')}
                 </Text>
             </View>

          </SafeAreaView>
      </CameraView>
    </View>
  );
}
