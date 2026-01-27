import React, { useState } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  Modal,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ActivityIndicator,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { IconSymbol } from "@/components/ui/IconSymbol";
import { useFoodSearch } from "@/hooks/useFood";
import { useMealDraft } from "@/hooks/useMealDraft";
import { useLanguage } from "@/hooks/useLanguage";
import { useColorScheme } from "@/hooks/useColorScheme";
import { Colors } from "@/constants/theme";

import { MealDraft, MealDraftItem } from "@/types/meal-draft";
import { FoodProduct, MealType } from "@/types/food";
import { ProcessedMeal } from "@/services/ai.service";

// Reuse VoiceMealSearch component
import { VoiceMealSearch } from "@/components/voice/confirmation/VoiceMealSearch";
import { EditProductModal } from "@/components/voice/confirmation/EditProductModal";

interface MealConfirmationModalProps {
  visible: boolean;
  initialMeal?: MealDraft | ProcessedMeal | null;
  mealType?: MealType;
  title?: string;
  onConfirm: (draft: MealDraft) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

/**
 * Universal Meal Confirmation Modal
 * Can be used for:
 * - Voice meal confirmation (with ProcessedMeal)
 * - Manual meal adding (empty draft with mealType)
 * - Editing existing entries (with MealDraft)
 */
export function MealConfirmationModal({
  visible,
  initialMeal,
  mealType,
  title,
  onConfirm,
  onCancel,
  isLoading,
}: MealConfirmationModalProps) {
  const { t } = useLanguage();
  const { colorScheme } = useColorScheme();
  const insets = useSafeAreaInsets();
  const theme = colorScheme ?? "light";

  const {
    draft,
    totals,
    addItem,
    removeItem,
    updateItemQuantity,
    cycleMealType,
    getMealTypeLabel,
    isEmpty,
    itemCount,
  } = useMealDraft({ initialMeal, mealType, t });

  const [isSearching, setIsSearching] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [editingItemIndex, setEditingItemIndex] = useState<number | null>(null);
  const [isEditModalVisible, setIsEditModalVisible] = useState(false);

  const { data: searchResults, isLoading: isSearchLoading } =
    useFoodSearch(searchQuery);

  const handleConfirm = () => {
    if (draft) onConfirm(draft);
  };

  const handleAddProduct = (product: FoodProduct) => {
    addItem(product, 100);
    setIsSearching(false);
    setSearchQuery("");
  };

  if (!draft) return null;

  const modalTitle =
    title ||
    (draft.source === "voice"
      ? t("addFood.confirmMeal") || "Confirm Meal"
      : t("addFood.addMeal") || "Add Meal");

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onCancel}
    >
      <View className="flex-1 bg-background" style={{ paddingTop: insets.top }}>
        <KeyboardAvoidingView
          behavior={Platform.OS === "ios" ? "padding" : "height"}
          className="flex-1"
        >
          {isSearching ? (
            <VoiceMealSearch
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              setIsSearching={setIsSearching}
              isSearchLoading={isSearchLoading}
              searchResults={searchResults}
              handleAddManualItem={handleAddProduct}
              t={t}
            />
          ) : (
            <View className="flex-1">
              {/* Header */}
              <View className="px-4 pt-4 pb-3 bg-background border-b border-border">
                <View className="flex-row justify-between items-center">
                  <TouchableOpacity onPress={onCancel} className="p-2 -ml-2">
                    <IconSymbol
                      name="xmark"
                      size={22}
                      color={Colors[theme].text}
                    />
                  </TouchableOpacity>

                  <Text className="text-lg font-bold text-foreground">
                    {modalTitle}
                  </Text>

                  <TouchableOpacity
                    className="flex-row items-center gap-1.5 bg-card px-3 py-1.5 rounded-full border border-border"
                    onPress={cycleMealType}
                  >
                    <Text className="text-sm font-bold text-foreground capitalize">
                      {getMealTypeLabel(draft.meal_type as string)}
                    </Text>
                    <IconSymbol
                      name="chevron.down"
                      size={12}
                      color={Colors[theme].tint}
                    />
                  </TouchableOpacity>
                </View>

                {/* Transcription (voice only) */}
                {draft.raw_transcription && (
                  <View className="mt-3 bg-primary/10 p-2.5 rounded-lg border-l-4 border-primary">
                    <Text className="text-indigo-900 dark:text-indigo-200 text-xs italic">
                      &quot;{draft.raw_transcription}&quot;
                    </Text>
                  </View>
                )}
              </View>

              {/* Items List */}
              <ScrollView
                className="flex-1"
                contentContainerStyle={{ padding: 16, paddingBottom: 100 }}
                keyboardShouldPersistTaps="handled"
                showsVerticalScrollIndicator={false}
              >
                {draft.items.map((item, index) => (
                  <MealItemCard
                    key={index}
                    item={item}
                    onPress={() => {
                      setEditingItemIndex(index);
                      setIsEditModalVisible(true);
                    }}
                    onRemove={() => removeItem(index)}
                  />
                ))}

                {/* Add Product Button */}
                <TouchableOpacity
                  onPress={() => setIsSearching(true)}
                  className="mt-2 mb-8 flex-row items-center justify-center p-4 border-2 border-dashed border-border rounded-2xl"
                >
                  <IconSymbol
                    name="plus"
                    size={20}
                    color={Colors[theme].mutedForeground}
                  />
                  <Text className="text-muted-foreground font-semibold ml-2">
                    {t("addFood.addProduct") || "Add product"}
                  </Text>
                </TouchableOpacity>

                {/* Empty State */}
                {isEmpty && (
                  <View className="items-center py-10 opacity-60">
                    <IconSymbol
                      name="fork.knife"
                      size={48}
                      color={Colors[theme].mutedForeground}
                    />
                    <Text className="text-muted-foreground mt-4 text-center">
                      {t("addFood.emptyMeal") || "No products added yet"}
                    </Text>
                    <Text className="text-muted-foreground text-sm text-center mt-1">
                      {t("addFood.tapToAdd") ||
                        "Tap the button above to add products"}
                    </Text>
                  </View>
                )}
              </ScrollView>

              {/* Summary Footer */}
              <View
                className="bg-card border-t border-border px-4 py-4"
                style={{ paddingBottom: insets.bottom + 16 }}
              >
                {/* Macros Summary */}
                <View className="flex-row justify-between mb-4 px-2">
                  <MacroSummaryItem
                    label={t("manualEntry.calories")}
                    value={Math.round(totals.kcal)}
                    unit="kcal"
                    highlight
                  />
                  <MacroSummaryItem
                    label={t("manualEntry.protein")}
                    value={Math.round(totals.protein)}
                    unit="g"
                  />
                  <MacroSummaryItem
                    label={t("manualEntry.fat")}
                    value={Math.round(totals.fat)}
                    unit="g"
                  />
                  <MacroSummaryItem
                    label={t("manualEntry.carbs")}
                    value={Math.round(totals.carbs)}
                    unit="g"
                  />
                </View>

                {/* Confirm Button */}
                <TouchableOpacity
                  onPress={handleConfirm}
                  disabled={isEmpty || isLoading}
                  className={`w-full py-4 rounded-xl items-center ${isEmpty || isLoading ? "bg-primary/50" : "bg-primary"}`}
                >
                  {isLoading ? (
                    <ActivityIndicator color="white" />
                  ) : (
                    <Text className="text-primary-foreground text-lg font-bold">
                      {t("addFood.addToDiary") || "Add to Diary"} ({itemCount})
                    </Text>
                  )}
                </TouchableOpacity>
              </View>
            </View>
          )}
        </KeyboardAvoidingView>
      </View>

      {/* Edit Item Modal */}
      <EditProductModal
        visible={isEditModalVisible}
        item={
          editingItemIndex !== null
            ? convertToProcessedItem(draft.items[editingItemIndex])
            : null
        }
        onClose={() => setIsEditModalVisible(false)}
        onSave={(quantity, unit) => {
          if (editingItemIndex !== null) {
            updateItemQuantity(editingItemIndex, quantity, unit);
          }
        }}
        t={t}
      />
    </Modal>
  );
}

// Helper component for meal item card
function MealItemCard({
  item,
  onPress,
  onRemove,
}: {
  item: MealDraftItem;
  onPress: () => void;
  onRemove: () => void;
}) {
  return (
    <Pressable
      onPress={onPress}
      className="mb-3 p-4 bg-card rounded-2xl border border-border shadow-sm"
    >
      <View className="flex-row justify-between items-start mb-2">
        <View className="flex-1">
          <View className="flex-row items-center gap-1.5 mb-0.5">
            <Text className="text-base font-bold text-foreground">
              {item.name}
            </Text>
            <IconSymbol name="pencil" size={11} color="#6366f1" />
          </View>
          {item.brand && (
            <Text className="text-xs text-muted-foreground">{item.brand}</Text>
          )}
        </View>
        <TouchableOpacity
          onPress={onRemove}
          className="p-2 -mr-2 -mt-2 opacity-50"
        >
          <IconSymbol name="xmark" size={16} color="#9CA3AF" />
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
        </View>
      </View>
    </Pressable>
  );
}

// Helper component for macro summary
function MacroSummaryItem({
  label,
  value,
  unit,
  highlight,
}: {
  label: string;
  value: number;
  unit: string;
  highlight?: boolean;
}) {
  return (
    <View className="items-center">
      <Text className="text-[10px] font-bold text-muted-foreground uppercase mb-0.5">
        {label}
      </Text>
      <Text
        className={`text-base font-black ${highlight ? "text-primary" : "text-foreground"}`}
      >
        {value}
        <Text className="text-xs font-normal text-muted-foreground">
          {" "}
          {unit}
        </Text>
      </Text>
    </View>
  );
}

// Convert MealDraftItem to ProcessedFoodItem for EditProductModal compatibility
function convertToProcessedItem(item: MealDraftItem) {
  return {
    product_id: item.product_id ? parseInt(item.product_id) : null,
    name: item.name,
    quantity_grams: item.quantity_grams,
    kcal: item.kcal,
    protein: item.protein,
    fat: item.fat,
    carbs: item.carbs,
    confidence: item.confidence || 1,
    unit_matched: item.unit_matched,
    quantity_unit_value: item.quantity_unit_value,
    status: item.status || "matched",
    brand: item.brand,
    units: item.units,
  };
}
