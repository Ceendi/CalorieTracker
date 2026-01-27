import React, { useState } from 'react';
import {
  View,
  KeyboardAvoidingView,
  Platform,
  Modal,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useLanguage } from '@/hooks/useLanguage';
import { useColorScheme } from '@/hooks/useColorScheme';
import { Colors } from '@/constants/theme';
import { useFoodSearch } from '@/hooks/useFood';
import type { ProcessedMeal } from '@/services/ai.service';
import { FoodProduct } from '@/types/food';

import { VoiceMealReview } from './confirmation/VoiceMealReview';
import { VoiceMealSearch } from './confirmation/VoiceMealSearch';
import { EditProductModal } from './confirmation/EditProductModal';
import { useVoiceMealLogic } from '@/hooks/useVoiceMealLogic';

interface VoiceMealConfirmationProps {
  visible: boolean;
  meal: ProcessedMeal | null;
  onConfirm: (meal: ProcessedMeal) => void;
  onEdit: () => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function VoiceMealConfirmation({
  visible,
  meal,
  onConfirm,
  onEdit,
  onCancel,
  isLoading,
}: VoiceMealConfirmationProps) {
  const { t } = useLanguage();
  const { colorScheme } = useColorScheme();
  const textColor = Colors[colorScheme ?? 'light'].text;
  const insets = useSafeAreaInsets();
  
  const { 
    localMeal, 
    totals, 
    updateQuantity, 
    removeItem, 
    cycleMealType, 
    getMealTypeLabel, 
    addManualItem 
  } = useVoiceMealLogic({ initialMeal: meal, t });

  const [editingItemIndex, setEditingItemIndex] = useState<number | null>(null);
  const [isEditModalVisible, setIsEditModalVisible] = useState(false);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const { data: searchResults, isLoading: isSearchLoading } = useFoodSearch(searchQuery);
  
  const handleConfirm = () => {
    if (localMeal) onConfirm(localMeal);
  };

  const handleAddManualItemWrapper = (product: FoodProduct) => {
    addManualItem(product);
    setIsSearching(false);
    setSearchQuery('');
  };

  if (!localMeal) return null;

  return (
    <Modal
        visible={visible}
        animationType="slide"
        presentationStyle="overFullScreen"
        transparent={false}
    >
        <View 
            className="flex-1 bg-background"
            style={{ paddingTop: insets.top }}
        >
            <KeyboardAvoidingView 
                behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
                className="flex-1"
                keyboardVerticalOffset={Platform.OS === 'ios' ? -insets.bottom : 0}
            >
                {isSearching ? (
                    <VoiceMealSearch 
                        searchQuery={searchQuery}
                        setSearchQuery={setSearchQuery}
                        setIsSearching={setIsSearching}
                        isSearchLoading={isSearchLoading}
                        searchResults={searchResults}
                        handleAddManualItem={handleAddManualItemWrapper}
                        t={t}
                    />
                ) : (
                    <VoiceMealReview 
                        localMeal={localMeal}
                        onCancel={onCancel}
                        textColor={textColor}
                        cycleMealType={cycleMealType}
                        getMealTypeLabel={getMealTypeLabel}
                        onEditItem={(index) => {
                            setEditingItemIndex(index);
                            setIsEditModalVisible(true);
                        }}
                        handleRemoveItem={removeItem}
                        setIsSearching={setIsSearching}
                        totals={totals}
                        onConfirm={handleConfirm}
                        isLoading={isLoading}
                        t={t}
                    />
                )}
            </KeyboardAvoidingView>
        </View>

        <EditProductModal 
            visible={isEditModalVisible}
            item={editingItemIndex !== null ? localMeal.items[editingItemIndex] : null}
            onClose={() => setIsEditModalVisible(false)}
            onSave={(quantity, unit) => {
                if (editingItemIndex !== null) {
                    updateQuantity(editingItemIndex, quantity, unit);
                }
            }}
            t={t}
        />
    </Modal>
  );
}
