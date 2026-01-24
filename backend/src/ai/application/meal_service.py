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
from src.ai.infrastructure.matching.vector_engine import HybridSearchEngine
from src.ai.infrastructure.nlu.processor import NaturalLanguageProcessor


class MealRecognitionService:
    DERIVATIVE_KEYWORDS = {
        "mąka", "skrobia", "płatki", "chleb", "bułka", "puree", "placki", "chipsy", "frytki",
        "halloumi", "białko", "białka", "żółtko", "żółtka", "proszek", "pasta", "mix",
        "czekolada", "czekoladowe", "wanilia", "waniliowe", "truskawka", "truskawkowe", "kakao", "kakaowe",
        "topiony", "wędzony"
    }

    FRESH_CATEGORIES = {
        "VEGFRESH", "FRUIFRESH", "DAI", "EGGS", "MEAT", "VEGPOT", "VEGROOT", "FISH"
    }

    def __init__(self,
                 vector_engine: HybridSearchEngine,
                 nlu_processor: NaturalLanguageProcessor,
                 slm_extractor=None):
        self.engine = vector_engine
        self.nlu = nlu_processor
        self.slm_extractor = slm_extractor

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
            candidates = self.engine.search(chunk.text_for_search, top_k=20, alpha=0.2)

            best_match: Optional[SearchCandidate] = None

            candidate_scores = []
            q_norm = chunk.text_for_search.lower()
            q_tokens = set(q_norm.split())

            for candidate in candidates:
                c_norm = candidate.name.lower()
                c_tokens = set(c_norm.split())

                current_score = candidate.score

                if q_norm == c_norm:
                    current_score += 3.0
                elif q_norm in c_norm.split():
                    current_score += 1.0

                if c_norm.startswith(q_norm):
                    current_score += 0.5

                if len(q_tokens) == 1 and len(c_tokens) > 2:
                    current_score -= 0.5

                derivative_in_product = self.DERIVATIVE_KEYWORDS.intersection(c_tokens)
                derivative_in_query = self.DERIVATIVE_KEYWORDS.intersection(q_tokens)

                if derivative_in_product and not derivative_in_query:
                    current_score *= 0.3

                if len(q_tokens) <= 2 and candidate.category in self.FRESH_CATEGORIES:
                    current_score += 0.3

                if not self.nlu.verify_keyword_consistency(chunk.text_for_search, candidate.name):
                    current_score *= 0.4
                    candidate.passed_guard = False
                else:
                    candidate.passed_guard = True

                candidate_scores.append((current_score, candidate))

            candidate_scores.sort(key=lambda x: x[0], reverse=True)

            if candidate_scores:
                best_match = candidate_scores[0][1]
                best_match.score = min(1.0, candidate_scores[0][0])

            if best_match:
                final_confidence = best_match.score * (0.85 if not best_match.passed_guard else 1.0)
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
                    brand=raw_product.get("brand", ""),
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
            return 100.0

        unit = item.quantity_unit.lower()
        val = item.quantity_value

        if any(u in unit for u in ["g", "gram", "ml", "mililitr"]):
            return val
        if "kg" in unit:
            return val * 1000

        if "units" in product:
            for u in product["units"]:
                u_name = u["name"].lower()
                if unit == u_name or unit in u_name:
                    return u["weight_g"] * val

        defaults = {
            "szklanka": 250.0, "szklankę": 250.0,
            "łyżka": 15.0, "łyżkę": 15.0,
            "łyżeczka": 5.0, "łyżeczkę": 5.0,
            "kromka": 35.0, "kromkę": 35.0,
            "plaster": 20.0, "plastry": 20.0,
            "sztuka": 100.0, "sztuki": 100.0, "szt": 100.0,
            "garść": 30.0, "porcja": 150.0
        }

        for k, v in defaults.items():
            if k in unit:
                return v * val

        return 100.0 * val
