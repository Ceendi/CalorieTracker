import { apiClient } from './api.client';
import { CONFIG } from '@/constants/config';
import { storageService } from './storage.service';
import { UnitInfo } from '@/types/food';

export interface ProcessedFoodItem {
  product_id: number | null;
  name: string;
  quantity_grams: number;
  kcal: number;
  protein: number;
  fat: number;
  carbs: number;
  confidence: number;
  unit_matched: string;
  quantity_unit_value: number;
  status: 'matched' | 'not_found' | 'needs_confirmation';
  brand?: string;
  units?: UnitInfo[];
  notes?: string;
}

export interface ProcessedMeal {
  meal_type: string;
  items: ProcessedFoodItem[];
  raw_transcription: string;
  processing_time_ms: number;
}

export interface TranscriptionResult {
  transcription: string;
  language: string;
}

export interface AISystemStatus {
  whisper_available: boolean;
  whisper_device: {
    cuda_available: boolean;
    cuda_device_count: number;
    cuda_device_name?: string;
  };
  spacy_available: boolean;
  llm_available: boolean;
  products_loaded: number;
  ner_confidence_threshold: number;
}

class AIService {
  async processAudio(audioUri: string, language: string = 'pl'): Promise<ProcessedMeal> {
    return this._uploadAudio<ProcessedMeal>('/api/v1/ai/process-audio', audioUri, language);
  }

  async transcribeOnly(audioUri: string, language: string = 'pl'): Promise<TranscriptionResult> {
    return this._uploadAudio<TranscriptionResult>('/api/v1/ai/transcribe', audioUri, language);
  }

  private async _uploadAudio<T>(endpoint: string, audioUri: string, language: string): Promise<T> {
    const formData = new FormData();
    const fileExtension = audioUri.split('.').pop()?.toLowerCase() || 'm4a';
    const mimeType = this.getMimeType(fileExtension);
    
    formData.append('audio', {
      uri: audioUri,
      type: mimeType,
      name: `recording.${fileExtension}`,
    } as any);

    const token = await storageService.getAccessToken();
    const response = await fetch(`${CONFIG.API_URL}${endpoint}?language=${language}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Service Error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async getStatus(): Promise<AISystemStatus> {
    const response = await apiClient.get<AISystemStatus>('/api/v1/ai/status');
    return response.data;
  }

  private getMimeType(extension: string): string {
    const mimeTypes: Record<string, string> = {
      'm4a': 'audio/m4a',
      'mp3': 'audio/mpeg',
      'wav': 'audio/wav',
      'ogg': 'audio/ogg',
      'flac': 'audio/flac',
      'webm': 'audio/webm',
      'mp4': 'video/mp4',
    };
    return mimeTypes[extension] || 'audio/m4a';
  }
}

export const aiService = new AIService();
