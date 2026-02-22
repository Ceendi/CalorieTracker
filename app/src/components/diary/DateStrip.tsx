import React, { useRef, useMemo, useCallback } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  FlatList,
  Dimensions,
  StyleSheet,
} from "react-native";
import { format, addDays, isSameDay, startOfDay } from "date-fns";
import { pl, enUS } from "date-fns/locale";
import { useLanguage } from "@/hooks/useLanguage";
import { useColorScheme } from "@/hooks/useColorScheme";
import { Colors } from "@/constants/theme";

interface DateStripProps {
  selectedDate: Date;
  onSelectDate: (date: Date) => void;
}

interface DateItemProps {
  item: Date;
  isSelected: boolean;
  isToday: boolean;
  colorScheme: "light" | "dark" | null | undefined;
  locale: typeof pl | typeof enUS;
  onPress: () => void;
}

const ITEM_WIDTH = Dimensions.get("window").width / 7;

// Using StyleSheet instead of className to avoid NativeWind's react-native-css-interop
// trying to access navigation context inside FlatList (which causes the error)
const DateItem = React.memo(function DateItem({
  item,
  isSelected,
  isToday,
  colorScheme,
  locale,
  onPress,
}: DateItemProps) {
  const tintColor = Colors[colorScheme ?? "light"].tint;

  return (
    <TouchableOpacity
      onPress={onPress}
      activeOpacity={0.7}
      style={[
        styles.itemContainer,
        { width: ITEM_WIDTH, zIndex: isSelected ? 10 : 0 },
      ]}
    >
      <View
        style={[
          styles.itemInner,
          {
            width: ITEM_WIDTH - 6,
            backgroundColor: isSelected
              ? tintColor
              : Colors[colorScheme ?? "light"].card,
            borderColor: isSelected
              ? tintColor
              : Colors[colorScheme ?? "light"].border,
          },
          isSelected && styles.itemSelected,
        ]}
      >
        <Text
          style={[
            styles.dayText,
            { color: isSelected ? "#E0E7FF" : "#9CA3AF" },
          ]}
        >
          {format(item, "EEE", { locale })}
        </Text>
        <Text
          style={[
            styles.dateText,
            {
              color: isSelected
                ? "#FFFFFF"
                : Colors[colorScheme ?? "light"].text,
            },
          ]}
        >
          {format(item, "d")}
        </Text>
        {isToday && !isSelected && (
          <View style={[styles.todayDot, { backgroundColor: tintColor }]} />
        )}
      </View>
    </TouchableOpacity>
  );
});

const styles = StyleSheet.create({
  itemContainer: {
    height: 80,
    alignItems: "center",
    justifyContent: "center",
  },
  itemInner: {
    height: 70,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    overflow: "hidden",
  },
  itemSelected: {
    shadowColor: "#312E81",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 4,
  },
  dayText: {
    fontSize: 11,
    fontWeight: "700",
    marginBottom: 2,
    textTransform: "uppercase",
  },
  dateText: {
    fontSize: 20,
    fontWeight: "800",
  },
  todayDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    marginTop: 4,
  },
  container: {
    marginBottom: 8,
    marginHorizontal: -20,
    overflow: "visible",
  },
});

export function DateStrip({ selectedDate, onSelectDate }: DateStripProps) {
  const { language } = useLanguage();
  const { colorScheme } = useColorScheme();
  const locale = language === "pl" ? pl : enUS;
  const flatListRef = useRef<FlatList>(null);

  const dates = useMemo(() => {
    const today = startOfDay(new Date());
    const range = [];
    for (let i = 30; i >= -30; i--) {
      range.push(addDays(today, i));
    }
    return range;
  }, []);

  const todayIndex = dates.findIndex((d) => isSameDay(d, new Date()));

  // Note: Removed automatic scrollToIndex on selectedDate change
  // as it caused visual "jump" when user clicks on a date.
  // The user is clicking on a visible date anyway, so no scroll needed.

  const renderItem = useCallback(
    ({ item }: { item: Date }) => {
      const isSelected = isSameDay(item, selectedDate);
      const isToday = isSameDay(item, new Date());

      return (
        <DateItem
          item={item}
          isSelected={isSelected}
          isToday={isToday}
          colorScheme={colorScheme}
          locale={locale}
          onPress={() => onSelectDate(item)}
        />
      );
    },
    [selectedDate, colorScheme, locale, onSelectDate],
  );

  return (
    <View style={styles.container}>
      <FlatList
        inverted
        ref={flatListRef}
        data={dates}
        renderItem={renderItem}
        keyExtractor={(item) => item.toISOString()}
        horizontal
        showsHorizontalScrollIndicator={false}
        style={{ overflow: "visible" }}
        contentContainerStyle={{
          paddingHorizontal: 0,
          paddingVertical: 10,
        }}
        getItemLayout={(data, index) => ({
          length: ITEM_WIDTH,
          offset: ITEM_WIDTH * index,
          index,
        })}
        initialScrollIndex={todayIndex}
        snapToInterval={ITEM_WIDTH}
        snapToAlignment="start"
        decelerationRate="fast"
        onScrollToIndexFailed={(info) => {
          setTimeout(() => {
            flatListRef.current?.scrollToIndex({
              index: info.index,
              animated: false,
              viewPosition: 0,
            });
          }, 100);
        }}
        extraData={selectedDate}
      />
    </View>
  );
}
