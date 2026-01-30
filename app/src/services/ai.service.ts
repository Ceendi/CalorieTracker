import { apiClient } from './api.client';
import { CONFIG } from '@/constants/config';
import { storageService } from './storage.service';

import { ProcessedMeal, TranscriptionResult, AISystemStatus } from '@/types/ai';

class AIService {
  async processAudio(audioUri: string, language: string = 'pl'): Promise<ProcessedMeal> {
    return this._uploadAudio<ProcessedMeal>('/api/v1/ai/process-audio', audioUri, language);
  }

  async transcribeOnly(audioUri: string, language: string = 'pl'): Promise<TranscriptionResult> {
    return this._uploadAudio<TranscriptionResult>('/api/v1/ai/transcribe', audioUri, language);
  }

  async processImage(imageUri: string): Promise<ProcessedMeal> {
    return this._uploadImage<ProcessedMeal>('/api/v1/ai/process-image', imageUri);
  }

  private async _uploadAudio<T>(endpoint: string, audioUri: string, language: string): Promise<T> {
    const token = await storageService.getAccessToken();
    const fileExtension = audioUri.split('.').pop()?.toLowerCase() || 'm4a';
    const mimeType = this.getMimeType(fileExtension);
    
    const formData = new FormData();
    formData.append('audio', {
      uri: audioUri,
      type: mimeType,
      name: `recording.${fileExtension}`,
    } as any);

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

  private async _uploadImage<T>(endpoint: string, imageUri: string): Promise<T> {
    const token = await storageService.getAccessToken();
    const fileExtension = imageUri.split('.').pop()?.toLowerCase() || 'jpg';
    
    const formData = new FormData();
    formData.append('image', {
      uri: imageUri,
      type: 'image/jpeg', // Gemini supports jpeg, png, webp. We can assume jpeg/png or detect better if needed.
      name: `photo.${fileExtension}`,
    } as any);

    const response = await fetch(`${CONFIG.API_URL}${endpoint}`, {
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
