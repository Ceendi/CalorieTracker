import { Stack, useLocalSearchParams, useRouter } from "expo-router";
import {
  ScrollView,
  Text,
  View,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  TouchableOpacity,
} from "react-native";
import { useState, useEffect } from "react";
import { useFoodBarcode } from "@/hooks/useFood";
import { foodService } from "@/services/food.service";
import { FoodProduct } from "@/types/food";
import { IconSymbol } from "@/components/ui/IconSymbol";
import { useColorScheme } from "@/hooks/useColorScheme";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLanguage } from "@/hooks/useLanguage";
import { Colors } from "@/constants/theme";

import { useFoodEntry } from "@/hooks/useFoodEntry";
import { NutrientSummary } from "@/components/food/NutrientSummary";
import { MealTypeSelector } from "@/components/food/MealTypeSelector";
import { QuantitySelector } from "@/components/food/QuantitySelector";
import { calculateGL } from "@/utils/glycemicLoad";

export default function FoodDetailsScreen() {
  const params = useLocalSearchParams<{
    entryId?: string;
    initialAmount?: string;
    initialMealType?: string;
    initialUnitLabel?: string;
    initialUnitGrams?: string;
    initialUnitQuantity?: string;
    barcode?: string;
    item?: string;
    date?: string;
  }>();

  const router = useRouter();
  const { t } = useLanguage();
  const { colorScheme } = useColorScheme();

  const [food, setFood] = useState<FoodProduct | null>(null);

  const {
    data: barcodeFood,
    isLoading: isLoadingBarcode,
    error: barcodeError,
  } = useFoodBarcode(params.barcode || null);

  useEffect(() => {
    if (barcodeFood) {
      setFood(barcodeFood);
    } else if (params.item) {
      try {
        const parsed = JSON.parse(params.item);
        setFood(parsed);

        if (
          params.entryId &&
          parsed.id &&
          (!parsed.units || parsed.units.length === 0)
        ) {
          foodService
            .getFoodById(parsed.id)
            .then((fullProduct) => {
              if (fullProduct && fullProduct.units) {
                setFood((prev) =>
                  prev ? { ...prev, units: fullProduct.units } : prev,
                );
              }
            })
            .catch(console.error);
        }
      } catch (e) {
        console.error("Failed to parse item", e);
      }
    }
  }, [barcodeFood, params.item, params.entryId]);

  useEffect(() => {
    if (barcodeError) {
      Alert.alert(t("foodDetails.errorTitle"), t("foodDetails.notFound"), [
        { text: "OK", onPress: () => router.back() },
      ]);
    }
  }, [barcodeError, router, t]);

  const {
    quantity,
    setQuantity,
    selectedUnit,
    setSelectedUnit,
    selectedMeal,
    setSelectedMeal,
    macros,
    saveEntry,
    isBusy: isSaving,
  } = useFoodEntry(food, params);

  const isGlobalBusy = isSaving || (isLoadingBarcode && !food);

  if (isLoadingBarcode && !food) {
    return (
      <View className="flex-1 justify-center items-center bg-background">
        <Stack.Screen
          options={{
            title: t("foodDetails.loading"),
            headerBackTitle: t("settings.cancel"),
          }}
        />
        <ActivityIndicator
          size="large"
          color={Colors[colorScheme ?? "light"].tint}
        />
      </View>
    );
  }

  if (!food && !isLoadingBarcode && !barcodeError && !params.item) {
    return (
      <View className="flex-1 justify-center items-center bg-background">
        <Stack.Screen
          options={{
            title: t("foodDetails.errorTitle"),
            headerBackTitle: t("settings.cancel"),
          }}
        />
        <Text className="text-muted-foreground">{t("foodDetails.noData")}</Text>
      </View>
    );
  }

  if (!food) return null;

  return (
    <View className="flex-1 bg-background" testID="food-details-screen">
      <Stack.Screen
        options={{
          title: params.entryId ? t("dashboard.edit") : t("foodDetails.title"),
          headerBackTitle: t("settings.cancel"),
        }}
      />
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        className="flex-1"
        keyboardVerticalOffset={Platform.OS === "ios" ? 100 : 0}
      >
        <View className="flex-1">
          <ScrollView
            contentContainerStyle={{ padding: 20 }}
            keyboardDismissMode="on-drag"
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}
          >
            <View className="mb-6">
              <Text
                testID="food-details-name"
                className="text-2xl font-bold text-foreground pt-1"
                style={{ lineHeight: 32 }}
              >
                {food.name}
                {food.source === "fineli" && (
                  <Text style={{ lineHeight: 32 }}>
                    {" "}
                    <IconSymbol
                      name="checkmark.seal.fill"
                      size={20}
                      color={Colors[colorScheme ?? "light"].primary}
                    />
                  </Text>
                )}
              </Text>
              {food.brand && food.brand.length > 0 && (
                <Text className="text-base text-muted-foreground mt-1">
                  {food.brand}
                </Text>
              )}
            </View>

            <QuantitySelector
              quantity={quantity}
              onChangeQuantity={setQuantity}
              selectedUnit={selectedUnit}
              onSelectUnit={setSelectedUnit}
              units={food.units}
            />

            <MealTypeSelector
              selectedMeal={selectedMeal}
              onSelect={setSelectedMeal}
            />

            <NutrientSummary
              calories={macros.calories}
              protein={macros.protein}
              fat={macros.fat}
              carbs={macros.carbs}
            />

            {food.glycemic_index != null && (
              (() => {
                const gl = calculateGL(food.glycemic_index, macros.carbs);
                const badgeColor =
                  gl.label === 'niski'
                    ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400'
                    : gl.label === 'średni'
                    ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400'
                    : 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400';
                return (
                  <View className="flex-row items-center bg-card rounded-2xl px-5 py-3 mb-6 border border-border shadow-sm gap-3">
                    <View className="flex-1">
                      <Text className="text-xs text-muted-foreground mb-0.5">
                        Ładunek glikemiczny porcji
                      </Text>
                      <Text className="text-base font-bold text-foreground">
                        ŁG {gl.value} <Text className="text-xs font-normal text-muted-foreground">(IG {food.glycemic_index})</Text>
                      </Text>
                    </View>
                    <View className={`px-3 py-1 rounded-full ${badgeColor}`}>
                      <Text className="text-xs font-bold capitalize">{gl.label}</Text>
                    </View>
                  </View>
                );
              })()
            )}
          </ScrollView>

          <View className="bg-card border-t border-border">
            <SafeAreaView edges={["bottom"]}>
              <View className="p-5">
                <TouchableOpacity
                  testID="food-details-save"
                  className={`w-full py-4 rounded-xl items-center ${isGlobalBusy ? "bg-primary/70" : "bg-primary"}`}
                  onPress={saveEntry}
                  disabled={isGlobalBusy}
                >
                  {isGlobalBusy ? (
                    <ActivityIndicator color="white" />
                  ) : (
                    <Text className="text-white text-lg font-bold">
                      {params.entryId
                        ? t("manualEntry.save")
                        : t("foodDetails.addToDiary")}
                    </Text>
                  )}
                </TouchableOpacity>
              </View>
            </SafeAreaView>
          </View>
        </View>
      </KeyboardAvoidingView>
    </View>
  );
}
