import time
from typing import Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.domain.models import MealRecognitionResult, MealType
from src.ai.infrastructure.nlu.vision_extractor import VisionExtractor
from src.ai.application.meal_service import MealRecognitionService
from src.ai.application.dto import ProcessedMealDTO, ProcessedFoodItemDTO
from src.ai.application.ports import NLUProcessorPort
from src.ai.infrastructure.nlu.processor import NaturalLanguageProcessor


class VisionProcessingService:
    """
    Service for processing food images and extracting meal information.
    Orchestrates VisionExtractor (Gemini) and MealRecognitionService (Vector Search).
    """

    def __init__(
        self,
        nlu_processor: Optional[NLUProcessorPort] = None
    ):
        from src.ai.infrastructure.search import PgVectorSearchService
        from src.ai.infrastructure.embedding import get_embedding_service

        self.nlu_processor: NLUProcessorPort = nlu_processor or NaturalLanguageProcessor()
        self.vision_extractor = VisionExtractor()
        
        self._pgvector_search_service = PgVectorSearchService(get_embedding_service())
        logger.info("VisionProcessingService initialized")

    async def process_image(
        self,
        image_bytes: bytes,
        session: AsyncSession
    ) -> ProcessedMealDTO:
        """
        Process image and extract meal info.
        """
        if session is None:
            raise ValueError("Database session is required")

        start_time = time.time()
        
        logger.info("Step 1: Analyzing image with Gemini Vision...")
        extraction, confidence = await self.vision_extractor.extract_from_image(image_bytes)
        logger.info(f"Gemini Analysis complete. Found {len(extraction.items)} items. Meal Type: {extraction.meal_type}")
        
        if not extraction.items:
            logger.warning("No items found in image.")
        
        logger.info("Step 2: Refining with DB Search...")
        meal_service = self._get_meal_service(session)
        recognition_result = await meal_service.recognize_from_vision_items(extraction.items)
        
        processing_time = (time.time() - start_time) * 1000
        
        response = self._build_dto(
            result=recognition_result,
            meal_type_detected=extraction.meal_type,
            processing_time_ms=processing_time
        )
        
        logger.info(f"Vision Processing complete in {processing_time:.0f}ms")
        return response

    def _get_meal_service(self, session: AsyncSession) -> MealRecognitionService:
        from src.ai.infrastructure.search import PgVectorSearchAdapter

        adapter = PgVectorSearchAdapter(
            search_service=self._pgvector_search_service,
            session=session
        )

        return MealRecognitionService(
            vector_engine=adapter,
            nlu_processor=self.nlu_processor,
            slm_extractor=None # Not needed for vision flow
        )

    def _build_dto(
        self,
        result: MealRecognitionResult,
        meal_type_detected: MealType,
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
                status="matched" if product.match_strategy != "vision_ai_estimate" else "needs_confirmation",
                units=product.units,
                notes=product.notes
            ))

        # Unmatched chunks should ideally be empty for vision flow as we force fallback,
        # but just in case:
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
                notes="Produkt nie rozpoznany.",
                units=[]
            ))

        return ProcessedMealDTO(
            meal_type=meal_type_detected.value, # Convert Enum to str
            items=items,
            raw_transcription="[Analiza Obrazu]",
            processing_time_ms=processing_time_ms
        )

    def get_system_status(self) -> dict:
        return {
            "gemini_vision_available": self.vision_extractor.client is not None,
            "pgvector_service_ready": self._pgvector_search_service is not None
        }
