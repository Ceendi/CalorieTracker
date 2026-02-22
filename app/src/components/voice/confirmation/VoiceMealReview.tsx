import React from "react";
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  Pressable,
} from "react-native";
import { IconSymbol } from "@/components/ui/IconSymbol";
import { VoiceMealSummary } from "./VoiceMealSummary";
import { ProcessedMeal, ProcessedFoodItem } from "@/types/ai";
import { useColorScheme } from "@/hooks/useColorScheme";
import { Colors } from "@/constants/theme";
import { calculateGL } from "@/utils/glycemicLoad";

const FoodItemReview = React.memo(
  ({
    item,
    onPress,
    onRemove,
    t,
  }: {
    item: ProcessedFoodItem;
    onPress: () => void;
    onRemove: () => void;
    t: (key: string) => string;
  }) => {
    const { colorScheme } = useColorScheme();
    const theme = colorScheme ?? "light";

    return (
      <Pressable
        onPress={onPress}
        className="mb-3 p-4 bg-card rounded-2xl border border-border shadow-sm"
      >
        <View className="flex-row justify-between items-start mb-2">
          <View className="flex-1">
            <View className="flex-row items-center gap-1.5 mb-0.5">
              <Text className="text-base font-black text-foreground leading-tight">
                {item.name}
              </Text>
              {(item.source === "fineli" || item.source === "kunachowicz") && (
                <IconSymbol
                  name="checkmark.seal.fill"
                  size={14}
                  color={Colors[theme].tint}
                />
              )}
              <IconSymbol name="pencil" size={11} color={Colors[theme].tint} />
            </View>
            {item.brand && (
              <Text className="text-xs text-muted-foreground font-medium">
                {item.brand}
              </Text>
            )}
          </View>
          <TouchableOpacity
            onPress={onRemove}
            className="p-2 -mr-2 -mt-2 opacity-50"
          >
            <IconSymbol
              name="xmark"
              size={16}
              color={Colors[theme].tabIconDefault}
            />
          </TouchableOpacity>
        </View>

        <View className="flex-row items-center justify-between">
          <View className="flex-row items-baseline gap-1">
            <Text className="text-xl font-black text-foreground">
              {item.unit_matched === "g" || item.unit_matched === "gram"
                ? item.quantity_grams
                : item.quantity_unit_value}
            </Text>
            <Text className="text-xs font-bold text-muted-foreground uppercase">
              {item.unit_matched === "g" || item.unit_matched === "gram"
                ? "g"
                : item.unit_matched}
            </Text>
          </View>

          <View className="items-end">
            <Text className="text-base font-bold text-foreground">
              {Math.round(item.kcal)}{" "}
              <Text className="text-[10px] text-muted-foreground font-normal">
                kcal
              </Text>
            </Text>
            {item.glycemic_index != null && item.carbs != null && (
              (() => {
                const gl = calculateGL(item.glycemic_index, item.carbs);
                const color =
                    gl.label === 'low' ? 'text-green-600 dark:text-green-400'
                    : gl.label === 'medium' ? 'text-amber-600 dark:text-amber-400'
                    : 'text-red-600 dark:text-red-400';
                return (
                    <Text className={`text-xs font-bold mt-0.5 ${color}`}>
                        {t('foodDetails.gl.title')} {Math.round(gl.value)}
                    </Text>
                );
              })()
            )}
          </View>
        </View>
      </Pressable>
    );
  },
);

FoodItemReview.displayName = "FoodItemReview";

interface VoiceMealReviewProps {
  localMeal: ProcessedMeal;
  onCancel: () => void;
  textColor: string;
  cycleMealType: () => void;
  getMealTypeLabel: (type: string) => string;
  onEditItem: (index: number) => void;
  handleRemoveItem: (index: number) => void;
  setIsSearching: (val: boolean) => void;
  totals: { kcal: number; protein: number; fat: number; carbs: number };
  onConfirm: () => void;
  isLoading?: boolean;
  t: (key: string) => string;
}

export const VoiceMealReview = ({
  localMeal,
  onCancel,
  textColor,
  cycleMealType,
  getMealTypeLabel,
  onEditItem,
  handleRemoveItem,
  setIsSearching,
  totals,
  onConfirm,
  isLoading,
  t,
}: VoiceMealReviewProps) => {
  const { colorScheme } = useColorScheme();

  if (!localMeal) return null;

  const theme = colorScheme ?? "light";

  return (
    <View className="flex-1 bg-background">
      <View className="px-4 pt-4 pb-4 bg-background/50 border-b border-border/30">
        <View className="flex-row justify-between items-center mb-3">
          <TouchableOpacity
            onPress={onCancel}
            className="p-2 -ml-2 rounded-full"
          >
            <IconSymbol name="xmark" size={22} color={textColor} />
          </TouchableOpacity>
          <View className="items-end">
            <Text className="text-xs font-semibold text-muted-foreground mb-1">
              {t("addFood.confirmProducts")}
            </Text>
            <TouchableOpacity
              className="flex-row items-center gap-1.5 bg-card px-3 py-1.5 rounded-full border border-border"
              onPress={cycleMealType}
            >
              <Text className="text-base font-black text-foreground capitalize">
                {getMealTypeLabel(localMeal.meal_type)}
              </Text>
              <IconSymbol
                name="chevron.down"
                size={12}
                color={Colors[theme].tint}
              />
            </TouchableOpacity>
          </View>
        </View>

        {localMeal.raw_transcription && (
          <View className="bg-primary/10 p-2.5 rounded-lg border-l-4 border-primary">
            <Text className="text-indigo-900 dark:text-indigo-200 text-xs italic leading-snug">
              &quot;{localMeal.raw_transcription}&quot;
            </Text>
          </View>
        )}
      </View>

      <View className="flex-1">
        <ScrollView
          className="flex-1"
          contentContainerStyle={{
            flexGrow: 1,
            paddingBottom: 100,
            paddingTop: 16,
            paddingHorizontal: 16,
          }}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {(localMeal.items || []).map(
            (item: ProcessedFoodItem, index: number) => (
              <FoodItemReview
                key={index}
                item={item}
                onPress={() => onEditItem(index)}
                onRemove={() => handleRemoveItem(index)}
                t={t}
              />
            ),
          )}

          <TouchableOpacity
            onPress={() => setIsSearching(true)}
            className="mt-2 mb-8 flex-row items-center justify-center p-4 border-2 border-dashed border-border rounded-2xl"
          >
            <IconSymbol
              name="plus"
              size={20}
              color={Colors[theme].tabIconDefault}
            />
            <Text className="text-muted-foreground font-semibold ml-2">
              {t("addFood.searchToConfirm")}
            </Text>
          </TouchableOpacity>
        </ScrollView>

        <VoiceMealSummary
          totals={totals}
          onConfirm={onConfirm}
          isLoading={isLoading}
          t={t}
        />
      </View>
    </View>
  );
};
