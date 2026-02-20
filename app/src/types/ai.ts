import { UnitInfo } from './food';

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
  source?: string; // 'public' | 'fineli' | 'openfoodfacts' | 'user'
  glycemic_index?: number | null;
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
