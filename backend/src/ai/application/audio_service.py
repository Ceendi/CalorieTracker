import time
from typing import Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.domain.models import MealRecognitionResult
from src.ai.domain.exceptions import (
    AudioProcessingException,
    TranscriptionFailedException
)
from src.ai.application.ports import STTPort, NLUProcessorPort, NLUExtractorPort
from src.ai.infrastructure.stt.whisper_local import WhisperLocalClient
from src.ai.infrastructure.nlu.processor import NaturalLanguageProcessor
from src.ai.application.meal_service import MealRecognitionService
from src.ai.application.dto import ProcessedMealDTO, ProcessedFoodItemDTO
from src.ai.infrastructure.nlu.slm_extractor import SLMExtractor
from src.ai.config import MEAL_TYPE_KEYWORDS, DEFAULT_MEAL_TYPE


class AudioProcessingService:
    """
    Service for processing audio recordings and extracting meal information.

    Uses PgVector-backed hybrid search (vector similarity + PostgreSQL FTS)
    for product matching.
    """

    def __init__(
        self,
        whisper_model_size: str = "medium",
        stt_client: Optional[STTPort] = None,
        nlu_processor: Optional[NLUProcessorPort] = None,
        slm_extractor: Optional[NLUExtractorPort] = None,
    ):
        """
        Initialize the audio processing service.

        Args:
            whisper_model_size: Whisper model size (tiny, base, small, medium, large)
            stt_client: Optional custom STT client
            nlu_processor: Optional custom NLU processor
            slm_extractor: Optional custom SLM extractor
        """
        from src.ai.infrastructure.search import PgVectorSearchService
        from src.ai.infrastructure.embedding import get_embedding_service

        self.stt_client: STTPort = stt_client or WhisperLocalClient(model_size=whisper_model_size)
        self.nlu_processor: NLUProcessorPort = nlu_processor or NaturalLanguageProcessor()

        self._pgvector_search_service = PgVectorSearchService(get_embedding_service())
        logger.info("AudioProcessingService initialized (pgvector mode)")

        if slm_extractor is not None:
            self.slm_extractor: Optional[NLUExtractorPort] = slm_extractor
        else:
            self.slm_extractor = SLMExtractor() if SLMExtractor.is_available() else None

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
        language: str = "pl",
        session: AsyncSession = None
    ) -> ProcessedMealDTO:
        """
        Process audio recording and extract meal information.

        Args:
            audio_bytes: Audio file bytes
            language: Audio language (default: Polish)
            session: Database session (required)

        Returns:
            ProcessedMealDTO with extracted meal items

        Raises:
            TranscriptionFailedException: If audio transcription fails
            AudioProcessingException: If meal extraction fails
            ValueError: If session is not provided
        """
        if session is None:
            raise ValueError("Database session is required")

        start_time = time.time()
        meal_service = self._get_meal_service(session)

        try:
            logger.info("Step 1: Transcribing audio with Whisper...")
            transcription = await self.stt_client.transcribe(
                audio_bytes,
                language=language
            )
            logger.info(f"Transcription: '{transcription}'")

            logger.info("Step 2: Processing with MealRecognitionService (pgvector)...")
            recognition_result = await meal_service.recognize_meal(transcription)

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

    def _get_meal_service(self, session: AsyncSession) -> MealRecognitionService:
        """
        Create MealRecognitionService with PgVectorSearchAdapter.

        Args:
            session: Database session

        Returns:
            MealRecognitionService instance
        """
        from src.ai.infrastructure.search import PgVectorSearchAdapter

        adapter = PgVectorSearchAdapter(
            search_service=self._pgvector_search_service,
            session=session
        )

        return MealRecognitionService(
            vector_engine=adapter,
            nlu_processor=self.nlu_processor,
            slm_extractor=self.slm_extractor
        )

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
                units=product.units,
                notes=product.notes,
                glycemic_index=product.glycemic_index,
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
        """Get the current system status."""
        return {
            "whisper_available": self.stt_client.is_available(),
            "slm_available": (self.slm_extractor is not None and self.slm_extractor.is_available()),
            "search_mode": "pgvector",
            "pgvector_service_ready": self._pgvector_search_service is not None,
        }
