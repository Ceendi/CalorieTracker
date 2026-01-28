import { apiClient } from './api.client';
import {
  MealPlanListResponseSchema,
  MealPlanSchema,
  DailyTargetsResponseSchema,
  GeneratePlanResponseSchema,
  GenerationStatusResponseSchema,
  MealPlanListResponse,
  MealPlan,
  DailyTargets,
  GeneratePlanResponse,
  GenerationStatusResponse,
  GeneratePlanRequest,
} from '@/schemas/meal-plan';

/**
 * Service for meal plan API operations.
 * Follows the pattern from food.service.ts with Zod validation.
 */
export const mealPlanService = {
  /**
   * List all meal plans for the current user.
   * @param status Optional filter by status (draft, active, archived)
   */
  async listPlans(status?: string): Promise<MealPlanListResponse> {
    const response = await apiClient.get('/api/v1/meal-plans', {
      params: status ? { status_filter: status } : undefined,
    });
    return MealPlanListResponseSchema.parse(response.data);
  },

  /**
   * Get a specific meal plan with all details.
   * @param planId UUID of the meal plan
   */
  async getPlan(planId: string): Promise<MealPlan> {
    const response = await apiClient.get(`/api/v1/meal-plans/${planId}`);
    return MealPlanSchema.parse(response.data);
  },

  /**
   * Delete a meal plan.
   * @param planId UUID of the meal plan
   */
  async deletePlan(planId: string): Promise<void> {
    await apiClient.delete(`/api/v1/meal-plans/${planId}`);
  },

  /**
   * Start async meal plan generation.
   * Returns a task_id for tracking progress.
   * @param request Generation request with preferences
   */
  async startGeneration(request: GeneratePlanRequest): Promise<GeneratePlanResponse> {
    const response = await apiClient.post('/api/v1/meal-plans/generate', request);
    return GeneratePlanResponseSchema.parse(response.data);
  },

  /**
   * Get current generation status (polling endpoint).
   * @param taskId Task ID from startGeneration
   */
  async getGenerationStatus(taskId: string): Promise<GenerationStatusResponse> {
    const response = await apiClient.get(`/api/v1/meal-plans/generate/${taskId}/status`);
    return GenerationStatusResponseSchema.parse(response.data);
  },

  /**
   * Get daily macro targets for the current user.
   * Uses backend calculation based on user profile.
   * @param diet Optional diet type
   */
  async getDailyTargets(diet?: string): Promise<DailyTargets> {
    const response = await apiClient.get('/api/v1/meal-plans/daily-targets', {
      params: diet ? { diet } : undefined,
    });
    return DailyTargetsResponseSchema.parse(response.data);
  },
};
