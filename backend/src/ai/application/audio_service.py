import time
from typing import List, Optional
from loguru import logger

from src.ai.domain.models import (
    MealRecognitionResult
)
from src.ai.domain.exceptions import (
    AudioProcessingException,
    TranscriptionFailedException
)
from src.ai.application.ports import STTPort, SearchEnginePort, NLUProcessorPort, NLUExtractorPort
from src.ai.infrastructure.stt.whisper_local import WhisperLocalClient
from src.ai.infrastructure.matching.vector_engine import HybridSearchEngine
from src.ai.infrastructure.nlu.processor import NaturalLanguageProcessor
from src.ai.application.meal_service import MealRecognitionService
from src.ai.application.dto import ProcessedMealDTO, ProcessedFoodItemDTO
from src.ai.infrastructure.nlu.slm_extractor import SLMExtractor
from src.ai.config import MEAL_TYPE_KEYWORDS, DEFAULT_MEAL_TYPE


class AudioProcessingService:
    def __init__(
        self,
        fineli_products: List[dict],
        whisper_model_size: str = "medium",
        stt_client: Optional[STTPort] = None,
        vector_engine: Optional[SearchEnginePort] = None,
        nlu_processor: Optional[NLUProcessorPort] = None,
        slm_extractor: Optional[NLUExtractorPort] = None,
    ):
        self.fineli_products = fineli_products

        self.stt_client: STTPort = stt_client or WhisperLocalClient(model_size=whisper_model_size)
        self.vector_engine: SearchEnginePort = vector_engine or HybridSearchEngine()
        self.nlu_processor: NLUProcessorPort = nlu_processor or NaturalLanguageProcessor()

        if slm_extractor is not None:
            self.slm_extractor: Optional[NLUExtractorPort] = slm_extractor
        else:
            self.slm_extractor = SLMExtractor() if SLMExtractor.is_available() else None

        self.meal_service = MealRecognitionService(
            vector_engine=self.vector_engine,
            nlu_processor=self.nlu_processor,
            slm_extractor=self.slm_extractor
        )

    async def warmup(self):
        logger.info("Warming up AudioProcessingService...")
        
        if self.stt_client:
            logger.info("Loading Whisper model...")
            await self.stt_client.load_model()
            
            if self.slm_extractor and self.slm_extractor.is_available():
                logger.info("Loading SLM model (Bielik)...")
                import asyncio
                await asyncio.to_thread(self.slm_extractor.loader.load_model)
            
        logger.info("AudioProcessingService warmup complete.")

    async def process_audio(
        self, 
        audio_bytes: bytes,
        language: str = "pl"
    ) -> ProcessedMealDTO:
        start_time = time.time()
        
        try:
            logger.info("Step 1: Transcribing audio with Whisper...")
            transcription = await self.stt_client.transcribe(
                audio_bytes, 
                language=language
            )
            logger.info(f"Transcription: '{transcription}'")

            logger.info("Step 2: Processing with MealRecognitionService (SLM + Hybrid Search)...")
            recognition_result = await self.meal_service.recognize_meal(transcription)
            
            processing_time = (time.time() - start_time) * 1000
            
            response = self._build_dto(
                result=recognition_result,
                transcription=transcription,
                processing_time_ms=processing_time
            )
            
            logger.info(
                f"Processing complete in {processing_time:.0f}ms: "
                f"{len(response.items)} items"
            )
            
            return response
            
        except TranscriptionFailedException as e:
            logger.error(f"Transcription failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Audio processing failed: {e}")
            raise AudioProcessingException(f"Processing failed: {str(e)}")
    
    def _build_dto(
        self,
        result: MealRecognitionResult,
        transcription: str,
        processing_time_ms: float
    ) -> ProcessedMealDTO:
        items = []
        
        for product in result.matched_products:
            items.append(ProcessedFoodItemDTO(
                product_id=product.product_id,
                name=product.name,
                quantity_grams=product.quantity_grams,
                kcal=product.kcal,
                protein=product.protein,
                fat=product.fat,
                carbs=product.carbs,
                confidence=product.confidence,
                unit_matched=product.unit_matched,
                quantity_unit_value=product.quantity_unit_value,
                status="matched",
                brand=product.brand,
                units=product.units,
                notes=product.notes
            ))
        
        for chunk in result.unmatched_chunks:
            items.append(ProcessedFoodItemDTO(
                product_id=None,
                name=chunk,
                quantity_grams=100.0,
                kcal=0.0,
                protein=0.0,
                fat=0.0,
                carbs=0.0,
                confidence=0.0,
                unit_matched="porcja",
                quantity_unit_value=1.0,
                status="not_found",
                notes="Produkt nie znaleziony w bazie. Wymaga weryfikacji.",
                brand=None,
                units=[]
            ))
            
        meal_type = self._detect_meal_type_simple(transcription)
        
        return ProcessedMealDTO(
            meal_type=meal_type, 
            items=items,
            raw_transcription=transcription,
            processing_time_ms=processing_time_ms
        )
    
    def _detect_meal_type_simple(self, text: str) -> str:
        text_lower = text.lower()
        for keyword, meal_type in MEAL_TYPE_KEYWORDS.items():
            if keyword in text_lower:
                return meal_type
        return DEFAULT_MEAL_TYPE

    async def transcribe_only(
        self, 
        audio_bytes: bytes,
        language: str = "pl"
    ) -> str:
        return await self.stt_client.transcribe(audio_bytes, language)
    
    def get_system_status(self) -> dict:
        return {
            "whisper_available": self.stt_client.is_available(),
            "slm_available": (self.slm_extractor is not None and self.slm_extractor.is_available()),
            "hybrid_engine_initialized": (self.vector_engine.embeddings is not None),
            "products_loaded": len(self.fineli_products)
        }
