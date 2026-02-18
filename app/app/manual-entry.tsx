import { Stack } from "expo-router";
import {
  ScrollView,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Controller } from "react-hook-form";
import { IconSymbol } from "@/components/ui/IconSymbol";
import { useColorScheme } from "@/hooks/useColorScheme";
import { useLanguage } from "@/hooks/useLanguage";
import { Colors } from "@/constants/theme";

import { useManualEntry } from "@/hooks/useManualEntry";
import { MacroInputGrid } from "@/components/food/MacroInputGrid";
import { MealTypeSelector } from "@/components/food/MealTypeSelector";

export default function ManualEntryScreen() {
  const { colorScheme } = useColorScheme();
  const { t } = useLanguage();

  const { control, submit, setValue, watch, isBusy } = useManualEntry();

  const weight = watch("weight");

  return (
    <View className="flex-1 bg-background" testID="manual-entry-screen">
      <Stack.Screen
        options={{
          title: t("manualEntry.title"),
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
            <View className="bg-card rounded-2xl p-4 mb-4 shadow-sm border border-border">
              <Text className="text-sm font-medium text-muted-foreground mb-2">
                {t("manualEntry.nameLabel")}
              </Text>
              <View className="border border-border rounded-xl bg-background h-14 justify-center px-4">
                <Controller
                  control={control}
                  name="name"
                  render={({ field: { onChange, value } }) => (
                    <TextInput
                      testID="manual-entry-name"
                      className="text-foreground w-full py-0"
                      style={{
                        fontSize: 18,
                        paddingVertical: 0,
                        includeFontPadding: false,
                      }}
                      placeholder={t("manualEntry.namePlaceholder")}
                      value={value}
                      onChangeText={onChange}
                      placeholderTextColor={
                        Colors[colorScheme ?? "light"].placeholder
                      }
                    />
                  )}
                />
              </View>
            </View>

            <MacroInputGrid control={control} />

            <View className="bg-card rounded-2xl p-4 mb-4 shadow-sm border border-border">
              <Text className="text-sm font-medium text-muted-foreground mb-2">
                {t("manualEntry.portionLabel")}
              </Text>
              <View className="flex-row items-stretch gap-2 h-14">
                <TouchableOpacity
                  testID="manual-entry-weight-minus"
                  className="w-12 bg-muted/50 rounded-xl items-center justify-center"
                  onPress={() =>
                    setValue("weight", Math.max(10, (Number(weight) || 0) - 10))
                  }
                >
                  <IconSymbol
                    name="minus"
                    size={20}
                    color={Colors[colorScheme ?? "light"].icon}
                  />
                </TouchableOpacity>
                <View className="flex-1 flex-row items-center bg-background rounded-xl px-4 border border-border">
                  <Controller
                    control={control}
                    name="weight"
                    render={({ field: { onChange, value } }) => (
                      <TextInput
                        testID="manual-entry-weight"
                        className="flex-1 font-bold text-foreground text-center"
                        style={{ fontSize: 20, height: "100%" }}
                        value={value?.toString()}
                        onChangeText={onChange}
                        keyboardType="numeric"
                      />
                    )}
                  />
                  <Text className="text-base text-muted-foreground ml-1">
                    g
                  </Text>
                </View>
                <TouchableOpacity
                  testID="manual-entry-weight-plus"
                  className="w-12 bg-muted/50 rounded-xl items-center justify-center"
                  onPress={() => setValue("weight", (Number(weight) || 0) + 10)}
                >
                  <IconSymbol
                    name="plus"
                    size={20}
                    color={Colors[colorScheme ?? "light"].icon}
                  />
                </TouchableOpacity>
              </View>
            </View>

            <Controller
              control={control}
              name="mealType"
              render={({ field: { value, onChange } }) => (
                <MealTypeSelector selectedMeal={value} onSelect={onChange} />
              )}
            />
          </ScrollView>

          <View className="bg-card border-t border-border">
            <SafeAreaView edges={["bottom"]}>
              <View className="p-5">
                <TouchableOpacity
                  testID="manual-entry-save"
                  className={`w-full py-4 rounded-xl items-center ${isBusy ? "bg-primary/70" : "bg-primary"}`}
                  onPress={submit}
                  disabled={isBusy}
                >
                  {isBusy ? (
                    <ActivityIndicator color="white" />
                  ) : (
                    <Text className="text-primary-foreground text-lg font-bold">
                      {t("manualEntry.save")}
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
