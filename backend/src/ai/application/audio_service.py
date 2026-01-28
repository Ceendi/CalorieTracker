import time
from typing import List, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

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
    """
    Service for processing audio recordings and extracting meal information.

    Supports two search modes:
    1. In-memory HybridSearchEngine (legacy): Uses fineli_products loaded from JSON
    2. PgVectorSearchAdapter (new): Uses database-backed pgvector hybrid search

    For pgvector mode, pass use_pgvector=True and provide session when calling
    process_audio(). The adapter will be created per-request with the session.
    """

    def __init__(
        self,
        fineli_products: Optional[List[dict]] = None,
        whisper_model_size: str = "medium",
        stt_client: Optional[STTPort] = None,
        vector_engine: Optional[SearchEnginePort] = None,
        nlu_processor: Optional[NLUProcessorPort] = None,
        slm_extractor: Optional[NLUExtractorPort] = None,
        use_pgvector: bool = False,
    ):
        """
        Initialize the audio processing service.

        Args:
            fineli_products: Legacy product list for in-memory search (optional if use_pgvector=True)
            whisper_model_size: Whisper model size (tiny, base, small, medium, large)
            stt_client: Optional custom STT client
            vector_engine: Optional custom search engine
            nlu_processor: Optional custom NLU processor
            slm_extractor: Optional custom SLM extractor
            use_pgvector: If True, uses PgVectorSearchAdapter instead of HybridSearchEngine
        """
        self.fineli_products = fineli_products or []
        self.use_pgvector = use_pgvector
        self._pgvector_search_service = None

        self.stt_client: STTPort = stt_client or WhisperLocalClient(model_size=whisper_model_size)
        self.nlu_processor: NLUProcessorPort = nlu_processor or NaturalLanguageProcessor()

        # Initialize vector engine based on mode
        if use_pgvector:
            # For pgvector mode, we'll create the adapter per-request with session
            # Store the search service for later use
            from src.ai.infrastructure.search import PgVectorSearchService
            from src.ai.infrastructure.embedding import get_embedding_service

            self._pgvector_search_service = PgVectorSearchService(get_embedding_service())
            # Placeholder engine - will be replaced with adapter per request
            self.vector_engine = None
            logger.info("AudioProcessingService initialized in pgvector mode")
        else:
            # Legacy in-memory mode
            self.vector_engine: SearchEnginePort = vector_engine or HybridSearchEngine()
            logger.info("AudioProcessingService initialized in legacy in-memory mode")

        if slm_extractor is not None:
            self.slm_extractor: Optional[NLUExtractorPort] = slm_extractor
        else:
            self.slm_extractor = SLMExtractor() if SLMExtractor.is_available() else None

        # MealRecognitionService will be created per-request for pgvector mode
        self.meal_service = None
        if not use_pgvector and self.vector_engine:
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
        language: str = "pl",
        session: Optional[AsyncSession] = None
    ) -> ProcessedMealDTO:
        """
        Process audio recording and extract meal information.

        Args:
            audio_bytes: Audio file bytes
            language: Audio language (default: Polish)
            session: Database session (required for pgvector mode)

        Returns:
            ProcessedMealDTO with extracted meal items

        Raises:
            TranscriptionFailedException: If audio transcription fails
            AudioProcessingException: If meal extraction fails
            ValueError: If session is required but not provided
        """
        start_time = time.time()

        # Validate session requirement for pgvector mode
        if self.use_pgvector and session is None:
            raise ValueError("Database session is required for pgvector mode")

        # Create meal service with appropriate search engine
        meal_service = self._get_meal_service(session)

        try:
            logger.info("Step 1: Transcribing audio with Whisper...")
            transcription = await self.stt_client.transcribe(
                audio_bytes,
                language=language
            )
            logger.info(f"Transcription: '{transcription}'")

            search_mode = "pgvector" if self.use_pgvector else "in-memory hybrid"
            logger.info(f"Step 2: Processing with MealRecognitionService ({search_mode})...")
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

    def _get_meal_service(
        self,
        session: Optional[AsyncSession] = None
    ) -> MealRecognitionService:
        """
        Get or create MealRecognitionService with appropriate search engine.

        For pgvector mode, creates a new service with PgVectorSearchAdapter
        bound to the provided session.

        Args:
            session: Database session (required for pgvector mode)

        Returns:
            MealRecognitionService instance
        """
        if self.use_pgvector:
            # Create adapter with session for this request
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
        else:
            # Return pre-built service for legacy mode
            return self.meal_service
    
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
        """
        Get the current system status.

        Returns status of all components including search mode.
        """
        if self.use_pgvector:
            search_status = {
                "search_mode": "pgvector",
                "pgvector_service_ready": self._pgvector_search_service is not None,
                "hybrid_engine_initialized": True,  # pgvector is always "initialized"
                "products_loaded": 0  # Products are in database, not memory
            }
        else:
            search_status = {
                "search_mode": "in_memory",
                "pgvector_service_ready": False,
                "hybrid_engine_initialized": (
                    self.vector_engine is not None and
                    hasattr(self.vector_engine, 'embeddings') and
                    self.vector_engine.embeddings is not None
                ),
                "products_loaded": len(self.fineli_products)
            }

        return {
            "whisper_available": self.stt_client.is_available(),
            "slm_available": (self.slm_extractor is not None and self.slm_extractor.is_available()),
            **search_status
        }
