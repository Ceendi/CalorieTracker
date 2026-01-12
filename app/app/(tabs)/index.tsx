import React from 'react';
import { View, Text, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '@/hooks/useAuth';
import { IconSymbol } from '@/components/ui/IconSymbol';

export default function HomeScreen() {
  const { user } = useAuth();
  const userName = user?.email?.split('@')[0] || 'User';

  const dailyGoal = 2200;
  const consumed = 1450; 
  const remaining = dailyGoal - consumed;
  const progress = consumed / dailyGoal;

  const macros = [
    { label: 'Protein', current: 110, total: 160, unit: 'g', color: 'bg-purple-100 dark:bg-purple-900', textColor: 'text-purple-600 dark:text-purple-300' },
    { label: 'Carbs', current: 180, total: 250, unit: 'g', color: 'bg-blue-100 dark:bg-blue-900', textColor: 'text-blue-600 dark:text-blue-300' },
    { label: 'Fat', current: 45, total: 70, unit: 'g', color: 'bg-orange-100 dark:bg-orange-900', textColor: 'text-orange-600 dark:text-orange-300' },
  ];

  return (
    <SafeAreaView className="flex-1 bg-gray-50 dark:bg-slate-900">
      <ScrollView contentContainerStyle={{ padding: 20 }}>
        
        <View className="flex-row justify-between items-center mb-6">
          <View>
            <Text className="text-gray-500 dark:text-gray-400 text-sm font-medium">Welcome back,</Text>
            <Text className="text-2xl font-bold text-gray-900 dark:text-white capitalize">{userName}</Text>
          </View>
          <TouchableOpacity className="bg-white dark:bg-slate-800 p-2 rounded-full border border-gray-200 dark:border-gray-700">
             <IconSymbol name="bell.fill" size={20} color="#6B7280" />
          </TouchableOpacity>
        </View>

        <LinearGradient
          colors={['#4F46E5', '#4338CA']}
          className="rounded-3xl p-6 mb-6 shadow-sm"
        >
          <View className="flex-row justify-between items-start mb-4">
             <View>
               <Text className="text-indigo-200 font-medium mb-1">Calories Remaining</Text>
               <Text className="text-4xl font-bold text-white mb-1">{remaining}</Text>
               <Text className="text-indigo-200 text-sm">Goal: {dailyGoal}</Text>
             </View>
             
             <View className="items-center justify-center w-16 h-16 rounded-full border-4 border-white/30">
                <Text className="text-white font-bold">{Math.round(progress * 100)}%</Text>
             </View>
          </View>

          <View className="bg-white/20 h-2 rounded-full overflow-hidden">
             <View style={{ width: `${Math.min(progress * 100, 100)}%` }} className="h-full bg-white rounded-full" />
          </View>
        </LinearGradient>

        <Text className="text-lg font-bold text-gray-900 dark:text-white mb-4">You've eaten</Text>
        <View className="flex-row justify-between mb-8">
          {macros.map((macro) => (
            <View key={macro.label} className={`flex-1 mx-1 p-4 rounded-2xl ${macro.color} items-center`}>
               <Text className={`font-bold text-lg mb-1 ${macro.textColor}`}>{macro.current}<Text className="text-sm font-normal opacity-70">/{macro.total}{macro.unit}</Text></Text>
               <Text className={`text-sm font-medium opacity-80 ${macro.textColor}`}>{macro.label}</Text>
            </View>
          ))}
        </View>

        <Text className="text-lg font-bold text-gray-900 dark:text-white mb-4">Quick Actions</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} className="mb-6">
           {['Scan Meal', 'Log Water', 'Add Exercise'].map((action, index) => (
             <TouchableOpacity key={action} className="mr-3 bg-white dark:bg-slate-800 p-4 rounded-xl border border-gray-100 dark:border-gray-700 flex-row items-center shadow-sm">
                <View className="bg-indigo-50 dark:bg-indigo-900/30 p-2 rounded-full mr-3">
                  <IconSymbol name={index === 0 ? 'barcode.viewfinder' : index === 1 ? 'drop.fill' : 'figure.run'} size={20} color="#4F46E5" />
                </View>
                <Text className="font-semibold text-gray-900 dark:text-white">{action}</Text>
             </TouchableOpacity>
           ))}
        </ScrollView>

      </ScrollView>
    </SafeAreaView>
  );
}
