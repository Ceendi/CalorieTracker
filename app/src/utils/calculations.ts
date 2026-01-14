import { User } from './validators';

/**
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
    
    return Math.round(bmr);
};

export const ActivityMultipliers: Record<string, number> = {
    sedentary: 1.2,      // little or no exercise
    light: 1.375,        // light exercise 1-3 days/week
    moderate: 1.55,      // moderate exercise 3-5 days/week
    high: 1.725,         // hard exercise 6-7 days/week
    very_high: 1.9       // very hard exercise & physical job
};

export const GoalModifiers: Record<string, number> = {
    lose: -500,      // ~0.5kg per week
    maintain: 0,
    gain: 300        // moderate surplus for muscle gain
};

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
    
    const activityMultiplier = ActivityMultipliers[profile.activity_level || 'sedentary'] || 1.2;
    const tdee = bmr * activityMultiplier;
    
    const goalModifier = GoalModifiers[profile.goal || 'maintain'] || 0;
    
    const calories = Math.round(tdee + goalModifier);

    // standard macros split: protein 20%, fat 30%, carbs 50%
    // protein: 4 kcal/g
    // fat: 9 kcal/g
    // carbs: 4 kcal/g
    const protein = Math.round((calories * 0.2) / 4);
    const fat = Math.round((calories * 0.3) / 9);
    const carbs = Math.round((calories * 0.5) / 4);

    return { calories, protein, fat, carbs };
};
