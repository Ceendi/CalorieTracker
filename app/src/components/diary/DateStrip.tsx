import React, { useRef, useMemo, useEffect } from 'react';
import { View, Text, TouchableOpacity, FlatList, Dimensions } from 'react-native';
import { format, addDays, isSameDay, startOfDay } from 'date-fns';
import { pl, enUS } from 'date-fns/locale';
import { useLanguage } from '@/hooks/useLanguage';
import { useColorScheme } from '@/hooks/use-color-scheme';

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
        style={{ 
            width: ITEM_WIDTH, 
            height: 80,
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: isSelected ? 10 : 1,
        }}
      >
        <View style={{
            width: ITEM_WIDTH - 6, 
            height: 70, 
            borderRadius: 18,
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: isSelected ? '#4F46E5' : 'transparent',
            ...(isSelected ? {
                shadowColor: '#312E81', 
                shadowOffset: { width: 0, height: 4 }, 
                shadowOpacity: 0.3, 
                shadowRadius: 5, 
                elevation: 6
            } : {})
        }}>
            <Text style={{
                fontSize: 11,
                fontWeight: '700',
                marginBottom: 2,
                textTransform: 'uppercase',
                color: isSelected ? '#E0E7FF' : '#9CA3AF'
            }}>
                {format(item, 'EEE', { locale })}
            </Text>
            <Text style={{
                fontSize: 20, 
                fontWeight: '800', 
                color: isSelected ? '#FFFFFF' : (isDark ? '#FFFFFF' : '#1F2937')
            }}>
                {format(item, 'd')}
            </Text>
            {isToday && !isSelected && (
                <View style={{ width: 4, height: 4, borderRadius: 2, marginTop: 4, backgroundColor: '#6366F1' }} />
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
