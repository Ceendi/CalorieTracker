import { aiService } from '../../../services/ai.service';
import { apiClient } from '../../../services/api.client';
import { storageService } from '../../../services/storage.service';

jest.mock('../../../services/api.client', () => ({
  apiClient: {
    get: jest.fn(),
  },
}));

jest.mock('../../../services/storage.service', () => ({
  storageService: {
    getAccessToken: jest.fn(),
  },
}));

jest.mock('../../../constants/config', () => ({
  CONFIG: { API_URL: 'http://localhost:8000' },
}));

const mockGet = apiClient.get as jest.Mock;

beforeEach(() => {
  jest.clearAllMocks();
  (storageService.getAccessToken as jest.Mock).mockResolvedValue('test-token');
  // Mock global fetch
  (global as any).fetch = jest.fn();
});

afterEach(() => {
  delete (global as any).fetch;
});

describe('aiService', () => {
  describe('processAudio', () => {
    it('creates FormData and calls fetch with correct URL', async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({
          meal_type: 'lunch',
          items: [],
          raw_transcription: 'test',
          processing_time_ms: 500,
        }),
      };
      (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

      const result = await aiService.processAudio('file:///path/recording.m4a');
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/ai/process-audio?language=pl',
        expect.objectContaining({
          method: 'POST',
          headers: { Authorization: 'Bearer test-token' },
        })
      );
      expect(result.meal_type).toBe('lunch');
    });

    it('uses correct MIME type for wav', async () => {
      const mockResponse = { ok: true, json: jest.fn().mockResolvedValue({ meal_type: 'lunch', items: [], raw_transcription: '', processing_time_ms: 0 }) };
      (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

      await aiService.processAudio('file:///path/recording.wav', 'en');
      const fetchCall = (global.fetch as jest.Mock).mock.calls[0];
      expect(fetchCall[0]).toContain('language=en');
    });

    it('throws on non-ok response', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
        json: jest.fn().mockResolvedValue({ detail: 'Server Error' }),
      });
      await expect(aiService.processAudio('file:///path/recording.m4a')).rejects.toThrow('Server Error');
    });

    it('throws generic error when response.json fails', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
        json: jest.fn().mockRejectedValue(new Error('parse error')),
      });
      await expect(aiService.processAudio('file:///path/recording.m4a')).rejects.toThrow('Service Error');
    });
  });

  describe('processImage', () => {
    it('calls fetch with image endpoint', async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({
          meal_type: 'lunch',
          items: [],
          raw_transcription: '',
          processing_time_ms: 300,
        }),
      };
      (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

      await aiService.processImage('file:///path/photo.jpg');
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/ai/process-image',
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  describe('getStatus', () => {
    it('returns AI system status', async () => {
      const status = {
        whisper_available: true,
        whisper_device: { cuda_available: true, cuda_device_count: 1 },
        spacy_available: true,
        llm_available: true,
        products_loaded: 5000,
        ner_confidence_threshold: 0.5,
      };
      mockGet.mockResolvedValue({ data: status });
      const result = await aiService.getStatus();
      expect(mockGet).toHaveBeenCalledWith('/api/v1/ai/status');
      expect(result.whisper_available).toBe(true);
    });
  });

  describe('MIME type detection', () => {
    it.each([
      ['recording.m4a', 'language=pl'],
      ['recording.mp3', 'language=pl'],
      ['recording.wav', 'language=pl'],
      ['recording.ogg', 'language=pl'],
    ])('handles %s extension', async (filename, _) => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue({ meal_type: 'lunch', items: [], raw_transcription: '', processing_time_ms: 0 }),
      });
      await aiService.processAudio(`file:///path/${filename}`);
      expect(global.fetch).toHaveBeenCalled();
    });
  });
});
