jest.mock('../../../services/api.client', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    delete: jest.fn(),
    patch: jest.fn(),
  },
}));

import { mealPlanService } from '../../../services/meal-plan.service';
import { apiClient } from '../../../services/api.client';

const mockGet = apiClient.get as jest.Mock;
const mockPost = apiClient.post as jest.Mock;
const mockDelete = (apiClient as any).delete as jest.Mock;
const mockPatch = apiClient.patch as jest.Mock;

beforeEach(() => jest.clearAllMocks());

describe('mealPlanService', () => {
  describe('listPlans', () => {
    it('fetches plans without filter', async () => {
      mockGet.mockResolvedValue({ data: { plans: [] } });
      const result = await mealPlanService.listPlans();
      expect(mockGet).toHaveBeenCalledWith('/api/v1/meal-plans', { params: undefined });
      expect(result.plans).toEqual([]);
    });

    it('fetches plans with status filter', async () => {
      mockGet.mockResolvedValue({ data: { plans: [] } });
      await mealPlanService.listPlans('active');
      expect(mockGet).toHaveBeenCalledWith('/api/v1/meal-plans', { params: { status_filter: 'active' } });
    });
  });

  describe('getPlan', () => {
    it('fetches plan by id', async () => {
      const plan = {
        id: '550e8400-e29b-41d4-a716-446655440000',
        name: 'Plan',
        start_date: '2024-01-15',
        end_date: '2024-01-21',
        status: 'active',
        days: [],
      };
      mockGet.mockResolvedValue({ data: plan });
      const result = await mealPlanService.getPlan('550e8400-e29b-41d4-a716-446655440000');
      expect(result.id).toBe('550e8400-e29b-41d4-a716-446655440000');
    });
  });

  describe('startGeneration', () => {
    it('posts generation request', async () => {
      mockPost.mockResolvedValue({ data: { task_id: 'task-123', message: 'Started' } });
      const result = await mealPlanService.startGeneration({
        start_date: '2024-01-15',
        days: 7,
      });
      expect(mockPost).toHaveBeenCalledWith('/api/v1/meal-plans/generate', expect.objectContaining({ start_date: '2024-01-15' }));
      expect(result.task_id).toBe('task-123');
    });
  });

  describe('getGenerationStatus', () => {
    it('fetches status by task id', async () => {
      mockGet.mockResolvedValue({ data: { status: 'generating', progress: 50 } });
      const result = await mealPlanService.getGenerationStatus('task-123');
      expect(mockGet).toHaveBeenCalledWith('/api/v1/meal-plans/generate/task-123/status');
      expect(result.status).toBe('generating');
    });
  });

  describe('getDailyTargets', () => {
    it('fetches targets without diet', async () => {
      mockGet.mockResolvedValue({ data: { kcal: 2000, protein: 150, fat: 70, carbs: 250 } });
      const result = await mealPlanService.getDailyTargets();
      expect(mockGet).toHaveBeenCalledWith('/api/v1/meal-plans/daily-targets', { params: undefined });
      expect(result.kcal).toBe(2000);
    });

    it('fetches targets with diet parameter', async () => {
      mockGet.mockResolvedValue({ data: { kcal: 1800, protein: 130, fat: 60, carbs: 220 } });
      await mealPlanService.getDailyTargets('vegetarian');
      expect(mockGet).toHaveBeenCalledWith('/api/v1/meal-plans/daily-targets', { params: { diet: 'vegetarian' } });
    });
  });

  describe('deletePlan', () => {
    it('calls delete endpoint', async () => {
      mockDelete.mockResolvedValue({});
      await mealPlanService.deletePlan('plan-123');
      expect(mockDelete).toHaveBeenCalledWith('/api/v1/meal-plans/plan-123');
    });
  });

  describe('updatePlanStatus', () => {
    it('patches plan status', async () => {
      mockPatch.mockResolvedValue({});
      await mealPlanService.updatePlanStatus('plan-123', 'active');
      expect(mockPatch).toHaveBeenCalledWith('/api/v1/meal-plans/plan-123/status', { status: 'active' });
    });
  });
});
