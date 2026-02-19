import { userService } from '../../../services/user.service';
import { apiClient } from '../../../services/api.client';

jest.mock('../../../services/api.client', () => ({
  apiClient: {
    patch: jest.fn(),
  },
}));

const mockPatch = apiClient.patch as jest.Mock;

beforeEach(() => jest.clearAllMocks());

describe('userService', () => {
  describe('updateProfile', () => {
    it('sends PATCH to /users/me', async () => {
      mockPatch.mockResolvedValue({ data: { id: 'user-1', weight: 85 } });
      const result = await userService.updateProfile({ weight: 85, height: 180 });
      expect(mockPatch).toHaveBeenCalledWith('/users/me', { weight: 85, height: 180 });
      expect(result.weight).toBe(85);
    });
  });
});
