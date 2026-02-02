import re
import time
from typing import List, Optional, Dict
from loguru import logger

from src.ai.domain.models import (
    IngredientChunk,
    SearchCandidate,
    MatchedProduct,
    MealRecognitionResult,
    ExtractedFoodItem
)
from src.ai.application.ports import SearchEnginePort, NLUProcessorPort, NLUExtractorPort
from src.ai.config import (
    DERIVATIVE_KEYWORDS,
    FRESH_CATEGORIES,
    DEFAULT_UNIT_GRAMS,
    DEFAULT_PORTION_GRAMS,
    MEAL_RECOGNITION_CONFIG as CONFIG
)


class MealRecognitionService:
    """
    Service for recognizing food items from text using pgvector hybrid search.

    Uses PgVectorSearchAdapter for database-backed semantic search.
    """

    def __init__(
        self,
        vector_engine: SearchEnginePort,
        nlu_processor: NLUProcessorPort,
        slm_extractor: Optional[NLUExtractorPort] = None
    ):
        self.engine = vector_engine
        self.nlu = nlu_processor
        self.slm_extractor = slm_extractor

    async def _search(
        self,
        query: str,
        top_k: int = 20,
        alpha: float = 0.3
    ) -> List[SearchCandidate]:
        """
        Search for products using pgvector hybrid search.

        Args:
            query: Search query
            top_k: Maximum results
            alpha: Hybrid search balance (vector vs FTS)

        Returns:
            List of SearchCandidate objects
        """
        return await self.engine.search(query, top_k=top_k, alpha=alpha)

    async def recognize_from_vision_items(
        self,
        extracted_items: List[ExtractedFoodItem]
    ) -> MealRecognitionResult:
        """
        Process items already extracted by Vision AI.
        Prioritizes DB match for macros. If no match, falls back to Gemini's macros.
        """
        start_time = time.time()
        logger.info(f"Processing {len(extracted_items)} vision items")

        matched_products: List[MatchedProduct] = []
        unmatched_chunks: List[str] = []

        for item in extracted_items:
            normalized_name = self.nlu.normalize_text(item.name)
            
            # 1. Search in DB
            candidates = await self._search(normalized_name, top_k=20, alpha=CONFIG.HYBRID_SEARCH_ALPHA)
            
            best_match: Optional[SearchCandidate] = None
            if candidates:
                # Basic scoring similar to recognize_meal but reduced since we have structured input
                candidate_scores = []
                q_norm = normalized_name.lower()
                
                for candidate in candidates:
                    c_norm = candidate.name.lower()
                    current_score = candidate.score
                    
                    if q_norm == c_norm:
                        current_score += CONFIG.EXACT_MATCH_BOOST
                    elif q_norm in c_norm.split():
                        current_score += CONFIG.TOKEN_MATCH_BOOST
                        
                    candidate_scores.append((current_score, candidate))
                
                candidate_scores.sort(key=lambda x: x[0], reverse=True)
                if candidate_scores:
                    best_match = candidate_scores[0][1]
                    best_match.score = max(0.0, min(1.0, candidate_scores[0][0]))

            # 2. Decide: Use DB or Fallback
            use_db_match = False
            if best_match and best_match.score > 0.4: # Threshold for accepting DB match
                use_db_match = True
            
            final_grams = item.quantity_value # Default to what Gemini saw
            
            if use_db_match and best_match:
                raw_product = self.engine.get_product_by_id(best_match.product_id)
                
                final_grams = item.quantity_value
                qty_scale = final_grams / 100.0
                
                matched = MatchedProduct(
                    product_id=best_match.product_id,
                    name_pl=best_match.name,
                    name_en=raw_product.get("name_en", ""),
                    quantity_grams=round(final_grams, 1),
                    kcal=round(raw_product.get("kcal_100g", 0) * qty_scale, 1),
                    protein=round(raw_product.get("protein_100g", 0) * qty_scale, 1),
                    fat=round(raw_product.get("fat_100g", 0) * qty_scale, 1),
                    carbs=round(raw_product.get("carbs_100g", 0) * qty_scale, 1),
                    match_confidence=round(best_match.score, 3),
                    unit_matched=item.quantity_unit,
                    quantity_unit_value=item.quantity_value,
                    original_query=item.name,
                    match_strategy="vision_vector_hybrid",
                    units=[
                        {
                            "label": u.get("name"),
                            "unit": u.get("name"),
                            "grams": u.get("weight_g")
                        } 
                        for u in raw_product.get("units", []) 
                        if u.get("name") and u.get("weight_g")
                    ],
                    notes=f"Vision Match. Score: {best_match.score:.2f}",
                    alternatives=candidates[1:]
                )
                matched_products.append(matched)
            else:
                # FALLBACK to Gemini Macros
                matched = MatchedProduct(
                    product_id="00000000-0000-0000-0000-000000000000", # Placeholder for AI-generated
                    name_pl=item.name,
                    name_en=item.name,
                    quantity_grams=round(item.quantity_value, 1),
                    kcal=round(item.kcal or 0, 1),
                    protein=round(item.protein or 0, 1),
                    fat=round(item.fat or 0, 1),
                    carbs=round(item.carbs or 0, 1),
                    match_confidence=item.confidence,
                    unit_matched=item.quantity_unit,
                    quantity_unit_value=item.quantity_value,
                    original_query=item.name,
                    match_strategy="vision_ai_estimate",
                    notes="AI Estimated Values (No DB match)",
                    units=[],
                    alternatives=[]
                )
                matched_products.append(matched)

        processing_time = (time.time() - start_time) * 1000
        overall_confidence = (
            sum(p.confidence for p in matched_products) / len(matched_products)
            if matched_products else 0.0
        )
        
        return MealRecognitionResult(
            matched_products=matched_products,
            unmatched_chunks=unmatched_chunks,
            overall_confidence=round(overall_confidence, 3),
            processing_time_ms=round(processing_time, 2)
        )

    async def recognize_meal(self, text: str) -> MealRecognitionResult:
        start_time = time.time()
        logger.info(f"Processing meal description: '{text}'")

        chunks = []
        is_slm_used = False

        if self.slm_extractor and self.slm_extractor.is_available():
            try:
                extraction, _ = await self.slm_extractor.extract(text)
                logger.debug(f"SLM Output: {[i.name for i in extraction.items]}")

                for item in extraction.items:
                    normalized_name = self.nlu.normalize_text(item.name)
                    chunks.append(IngredientChunk(
                        original_text=item.name,
                        text_for_search=normalized_name,
                        quantity_value=item.quantity_value,
                        quantity_unit=item.quantity_unit,
                        is_composite=False
                    ))
                is_slm_used = True
                logger.info(f"SLM Extraction success: {len(chunks)} items")
            except Exception as e:
                logger.error(f"SLM Extraction failed: {e}, falling back to Regex")

        if not chunks and not is_slm_used:
            chunks = self.nlu.process_text(text)

        matched_products: List[MatchedProduct] = []
        unmatched_chunks: List[str] = []

        for chunk in chunks:
            candidates = await self._search(chunk.text_for_search, top_k=20, alpha=CONFIG.HYBRID_SEARCH_ALPHA)

            best_match: Optional[SearchCandidate] = None

            candidate_scores = []
            q_norm = chunk.text_for_search.lower()
            q_tokens = set(q_norm.split())

            for candidate in candidates:
                c_norm = candidate.name.lower()
                c_tokens = set(c_norm.split())

                current_score = candidate.score

                if q_norm == c_norm:
                    current_score += CONFIG.EXACT_MATCH_BOOST
                elif q_norm in c_norm.split():
                    current_score += CONFIG.TOKEN_MATCH_BOOST

                if c_norm.startswith(q_norm):
                    current_score += CONFIG.PREFIX_MATCH_BOOST

                if len(q_tokens) == 1 and len(c_tokens) > 2:
                    current_score -= CONFIG.MULTI_TOKEN_PENALTY

                derivative_in_product = DERIVATIVE_KEYWORDS.intersection(c_tokens)
                derivative_in_query = DERIVATIVE_KEYWORDS.intersection(q_tokens)

                if derivative_in_product and not derivative_in_query:
                    current_score *= CONFIG.DERIVATIVE_PENALTY_MULTIPLIER

                if len(q_tokens) <= 2 and candidate.category in FRESH_CATEGORIES:
                    current_score += CONFIG.FRESH_CATEGORY_BOOST

                if not self.nlu.verify_keyword_consistency(chunk.text_for_search, candidate.name):
                    current_score *= CONFIG.GUARD_FAIL_MULTIPLIER
                    candidate.passed_guard = False
                else:
                    candidate.passed_guard = True

                candidate_scores.append((current_score, candidate))

            candidate_scores.sort(key=lambda x: x[0], reverse=True)

            if candidate_scores:
                best_match = candidate_scores[0][1]
                best_match.score = max(0.0, min(1.0, candidate_scores[0][0]))

            if best_match:
                confidence_multiplier = CONFIG.GUARD_FAIL_CONFIDENCE_MULTIPLIER if not best_match.passed_guard else 1.0
                final_confidence = best_match.score * confidence_multiplier
                raw_product = self.engine.get_product_by_id(best_match.product_id)

                temp_item = ExtractedFoodItem(
                    name=chunk.original_text,
                    quantity_value=chunk.quantity_value or 1.0,
                    quantity_unit=chunk.quantity_unit or "porcja"
                )

                grams = self._calculate_grams(temp_item, raw_product)
                qty_scale = grams / 100.0

                matched = MatchedProduct(
                    product_id=best_match.product_id,
                    name_pl=best_match.name,
                    name_en=raw_product.get("name_en", ""),
                    quantity_grams=round(grams, 1),
                    kcal=round(raw_product.get("kcal_100g", 0) * qty_scale, 1),
                    protein=round(raw_product.get("protein_100g", 0) * qty_scale, 1),
                    fat=round(raw_product.get("fat_100g", 0) * qty_scale, 1),
                    carbs=round(raw_product.get("carbs_100g", 0) * qty_scale, 1),
                    match_confidence=round(final_confidence, 3),
                    unit_matched=temp_item.quantity_unit,
                    quantity_unit_value=temp_item.quantity_value,
                    original_query=chunk.original_text,
                    match_strategy="semantic_search",
                    units=[
                        {
                            "label": u.get("name"),
                            "unit": u.get("name"),
                            "grams": u.get("weight_g")
                        } 
                        for u in raw_product.get("units", []) 
                        if u.get("name") and u.get("weight_g")
                    ],
                    notes=f"E5 Score: {best_match.score:.2f}, Guard: {best_match.passed_guard}",
                    alternatives=candidates[1:]
                )
                matched_products.append(matched)
            else:
                unmatched_chunks.append(chunk.original_text)

        processing_time = (time.time() - start_time) * 1000
        overall_confidence = (
            sum(p.confidence for p in matched_products) / len(matched_products)
            if matched_products else 0.0
        )

        logger.info(
            f"Recognition complete: {len(matched_products)} items matched, {len(unmatched_chunks)} failed. "
            f"Time: {processing_time:.2f}ms")

        return MealRecognitionResult(
            matched_products=matched_products,
            unmatched_chunks=unmatched_chunks,
            overall_confidence=round(overall_confidence, 3),
            processing_time_ms=round(processing_time, 2)
        )

    def _calculate_grams(self, item: ExtractedFoodItem, product: Optional[Dict]) -> float:
        if not product:
            return DEFAULT_PORTION_GRAMS

        unit = item.quantity_unit.lower()
        val = item.quantity_value

        if re.match(r'^(g|gramy?|gram[óo]w|ml|mililitr[óy]?|mililit(?:rów)?)$', unit, re.IGNORECASE):
            return val
        if re.match(r'^kg$', unit, re.IGNORECASE):
            return val * 1000

        if "units" in product:
            for u in product["units"]:
                u_name = u["name"].lower()
                if unit == u_name or unit in u_name:
                    return u["weight_g"] * val

        for keyword, grams in DEFAULT_UNIT_GRAMS.items():
            if keyword in unit:
                return grams * val

        return DEFAULT_PORTION_GRAMS * val
