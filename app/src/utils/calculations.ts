import { User } from '../types/user';

/**
 * Clamp a number between min and max values
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/**
 * Round a number to specified decimal places
 */
export function roundTo(value: number, decimals: number = 1): number {
  const factor = Math.pow(10, decimals);
  return Math.round(value * factor) / factor;
}

/**
 * @deprecated Use useDailyTargets() hook from @/hooks/useMealPlan instead.
 * This fetches targets from the backend API which uses the same calculation.
 * Kept for fallback purposes when API is unavailable.
 *
 * Calculates the Basal Metabolic Rate (BMR) using the Mifflin-St Jeor equation.
 */
export const calculateBMR = (
    weightKg: number,
    heightCm: number,
    ageYears: number,
    gender: 'male' | 'female' | string
): number => {
    // Mifflin-St Jeor Equation
    let bmr = (10 * weightKg) + (6.25 * heightCm) - (5 * ageYears);

    if (gender === 'male' || gender === 'Male') {
        bmr += 5;
    } else {
        bmr -= 161;
    }

    return bmr;
};

/**
 * @deprecated Use useDailyTargets() hook from @/hooks/useMealPlan instead.
 * This fetches targets from the backend API.
 * Kept for fallback purposes when API is unavailable.
 */
export const ActivityMultipliers: Record<string, number> = {
    sedentary: 1.4,      // little or no exercise
    light: 1.55,         // light exercise 1-3 days/week
    moderate: 1.70,      // moderate exercise 3-5 days/week
    high: 1.85,          // hard exercise 6-7 days/week
    very_high: 2.0       // very hard exercise & physical job
};

/**
 * @deprecated Use useDailyTargets() hook from @/hooks/useMealPlan instead.
 * This fetches targets from the backend API.
 * Kept for fallback purposes when API is unavailable.
 */
export const GoalModifiers: Record<string, number> = {
    lose: 0.8,       // 20% calorie deficit
    maintain: 1.0,   // No adjustment
    gain: 1.15       // 15% calorie surplus
};

/**
 * @deprecated Use useDailyTargets() hook from @/hooks/useMealPlan instead.
 * This fetches targets from the backend API which uses the same calculation.
 * Kept as a fallback when the API is unavailable (offline mode, etc.).
 *
 * Calculates daily calorie and macro goals based on user profile.
 */
export const calculateDailyGoal = (profile: Partial<User>) => {
    if (!profile.weight || !profile.height || !profile.age || !profile.gender) {
        return {
            calories: 2000,
            protein: 160,
            fat: 70,
            carbs: 250
        };
    }

    const bmr = calculateBMR(profile.weight, profile.height, profile.age, profile.gender);

    const activityMultiplier = ActivityMultipliers[profile.activity_level || 'sedentary'] || 1.4;
    const tdee = bmr * activityMultiplier;

    const goalModifier = GoalModifiers[profile.goal || 'maintain'] || 1.0;

    const calories = Math.round(tdee * goalModifier);

    // standard macros split: protein 20%, fat 30%, carbs 50%
    // Protein: 4 kcal/g, Fat: 9 kcal/g, Carbs: 4 kcal/g
    const protein = roundTo((calories * 0.2) / 4, 1);
    const fat = roundTo((calories * 0.3) / 9, 1);
    const carbs = roundTo((calories * 0.5) / 4, 1);

    return { calories, protein, fat, carbs };
};

export const summarizeMealMacros = (items: { kcal: number; protein: number; fat: number; carbs: number }[]) => {
    return items.reduce(
        (acc, item) => ({
            kcal: acc.kcal + item.kcal,
            protein: acc.protein + item.protein,
            fat: acc.fat + item.fat,
            carbs: acc.carbs + item.carbs,
        }),
        { kcal: 0, protein: 0, fat: 0, carbs: 0 }
    );
};

export const calculateItemMacros = (
    currentMacros: { kcal: number; protein: number; fat: number; carbs: number },
    originalGrams: number,
    newQuantity: number,
    gramsPerUnit: number = 1
) => {
    if (newQuantity < 0 || isNaN(newQuantity)) {
        return { kcal: 0, protein: 0, fat: 0, carbs: 0 };
    }
    if (isNaN(currentMacros.kcal) || isNaN(currentMacros.protein)) {
        return { kcal: 0, protein: 0, fat: 0, carbs: 0 };
    }

    const totalGrams = newQuantity * gramsPerUnit;
    const safeOriginalGrams = Math.max(originalGrams || 100, 1);
    const ratio = totalGrams / safeOriginalGrams;

    return {
        kcal: Math.round(currentMacros.kcal * ratio),
        protein: currentMacros.protein * ratio,
        fat: currentMacros.fat * ratio,
        carbs: currentMacros.carbs * ratio,
    };
};
