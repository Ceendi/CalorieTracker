import React, { useRef, useMemo, useEffect } from 'react';
import { View, Text, TouchableOpacity, FlatList, Dimensions } from 'react-native';
import { format, addDays, isSameDay, startOfDay } from 'date-fns';
import { pl, enUS } from 'date-fns/locale';
import { useLanguage } from '@/hooks/useLanguage';
import { useColorScheme } from '@/hooks/useColorScheme';
import { Colors } from '@/constants/theme';

interface DateStripProps {
  selectedDate: Date;
  onSelectDate: (date: Date) => void;
}

const ITEM_WIDTH = Dimensions.get('window').width / 7;

export function DateStrip({ selectedDate, onSelectDate }: DateStripProps) {
  const { language } = useLanguage();
  const { colorScheme } = useColorScheme();
  const locale = language === 'pl' ? pl : enUS;
  const isDark = colorScheme === 'dark';
  const flatListRef = useRef<FlatList>(null);

  const dates = useMemo(() => {
    const today = startOfDay(new Date());
    const range = [];
    for (let i = 30; i >= -30; i--) {
        range.push(addDays(today, i));
    }
    return range;
  }, []);

  const selectedIndex = dates.findIndex(d => isSameDay(d, selectedDate));
  const todayIndex = dates.findIndex(d => isSameDay(d, new Date()));

  useEffect(() => {
      if (selectedIndex !== -1 && flatListRef.current) {
          flatListRef.current.scrollToIndex({
              index: selectedIndex,
              animated: true,
              viewPosition: 0
          });
      }
  }, [selectedDate]); 

  const renderItem = ({ item }: { item: Date }) => {
    const isSelected = isSameDay(item, selectedDate);
    const isToday = isSameDay(item, new Date());

    return (
      <TouchableOpacity
        onPress={() => onSelectDate(item)}
        activeOpacity={0.7}
        style={{ width: ITEM_WIDTH }}
        className={`h-20 items-center justify-center ${isSelected ? 'z-10' : 'z-0'}`}
      >
        <View 
            style={{ 
                width: ITEM_WIDTH - 6,
                backgroundColor: isSelected ? Colors[colorScheme ?? 'light'].tint : 'transparent'
            }}
            className={`h-[70px] rounded-2xl items-center justify-center ${isSelected ? 'shadow-md shadow-indigo-900/30' : ''}`}
        >
            <Text className={`text-[11px] font-bold mb-0.5 uppercase ${isSelected ? 'text-indigo-100' : 'text-gray-400'}`}>
                {format(item, 'EEE', { locale })}
            </Text>
            <Text className={`text-xl font-extrabold ${isSelected ? 'text-white' : 'text-foreground'}`}>
                {format(item, 'd')}
            </Text>
            {isToday && !isSelected && (
                <View className="w-1 h-1 rounded-full mt-1" style={{ backgroundColor: Colors[colorScheme ?? 'light'].tint }} />
            )}
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View className="mb-2" style={{ marginHorizontal: -20, overflow: 'visible' }}>
       <FlatList
          inverted 
          ref={flatListRef}
          data={dates}
          renderItem={renderItem}
          keyExtractor={item => item.toISOString()}
          horizontal
          showsHorizontalScrollIndicator={false}
          style={{ overflow: 'visible' }}
          contentContainerStyle={{ 
              paddingHorizontal: 0,
              paddingVertical: 10, 
          }}
          getItemLayout={(data, index) => (
            { length: ITEM_WIDTH, offset: ITEM_WIDTH * index, index }
          )}
          initialScrollIndex={todayIndex} 
          snapToInterval={ITEM_WIDTH}
          snapToAlignment="start"
          decelerationRate="fast"
          onScrollToIndexFailed={info => {
              setTimeout(() => {
                  flatListRef.current?.scrollToIndex({ index: info.index, animated: false, viewPosition: 0 });
              }, 100);
          }}
       />
    </View>
  );
}
