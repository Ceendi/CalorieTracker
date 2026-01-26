import json
import asyncio
from typing import Tuple, Any, cast
from loguru import logger

from src.ai.infrastructure.nlu.base import BaseNLUExtractor
from src.ai.infrastructure.nlu.slm_loader import SLMLoader
from src.ai.domain.models import (
    MealExtraction,
    ExtractedFoodItem,
    MealType,
    ExtractionMethod
)
from src.ai.config import SLM_SYSTEM_PROMPT, SLM_MAX_TOKENS, SLM_TEMPERATURE

try:
    from llama_cpp import Llama, LlamaGrammar
except ImportError:
    Llama = None
    LlamaGrammar = None


class SLMExtractor(BaseNLUExtractor):
    def __init__(self):
        self.loader = SLMLoader()
        self._grammar = None
        
    def get_grammar(self) -> Any:
        if self._grammar is not None:
            return self._grammar
            
        schema = {
            "type": "object",
            "properties": {
                "meal_type": {
                    "type": "string",
                    "enum": ["śniadanie", "drugie_śniadanie", "obiad", "podwieczorek", "kolacja", "przekąska"]
                },
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "quantity_value": {"type": "number"},
                            "quantity_unit": {"type": "string"}
                        },
                        "required": ["name", "quantity_value", "quantity_unit"]
                    }
                }
            },
            "required": ["meal_type", "items"]
        }
        
        if LlamaGrammar is None:
            logger.warning("LlamaGrammar is not available (import failed)")
            return None

        try:
            self._grammar = LlamaGrammar.from_json_schema(json.dumps(schema))
        except Exception as e:
            logger.error(f"Failed to compile grammar: {e}")
            self._grammar = None
            
        return self._grammar

    async def extract(self, text: str) -> Tuple[MealExtraction, float]:
        model = self.loader.load_model()
        if model is None:
            logger.error("SLM Model not loaded")
            return MealExtraction(
                meal_type=MealType.SNACK,
                raw_transcription=text,
                items=[],
                overall_confidence=0.0
            ), 0.0

        grammar = self.get_grammar()
        
        prompt = self._build_prompt(text)

        model_any = cast(Any, model)
        
        output = await asyncio.to_thread(
            model_any.create_completion,
            prompt=prompt,
            max_tokens=SLM_MAX_TOKENS,
            temperature=SLM_TEMPERATURE,
            grammar=grammar,
            stop=["<|eot_id|>"]
        )
        
        text_response = output['choices'][0]['text']
        logger.debug(f"SLM raw response: {text_response}")
        
        try:
            data = json.loads(text_response)
            return self._parse_json_result(data, text)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse SLM JSON: {text_response}")
            return MealExtraction(
                meal_type=MealType.SNACK,
                raw_transcription=text,
                items=[],
                overall_confidence=0.0
            ), 0.0

    def _build_prompt(self, text: str) -> str:
        return (
            f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{SLM_SYSTEM_PROMPT}<|eot_id|>"
            f"<|start_header_id|>user<|end_header_id|>\n\n{text}<|eot_id|>"
            f"<|start_header_id|>assistant<|end_header_id|>\n\n"
        )
        
    def _parse_json_result(self, data: dict, raw_text: str) -> Tuple[MealExtraction, float]:
        meal_map = {
            "śniadanie": MealType.BREAKFAST,
            "drugie_śniadanie": MealType.LUNCH, 
            "obiad": MealType.LUNCH, 
            "podwieczorek": MealType.SNACK,
            "kolacja": MealType.DINNER,
            "przekąska": MealType.SNACK
        }
        
        meal_str = data.get("meal_type", "przekąska")
        meal_type = meal_map.get(meal_str, MealType.SNACK)
        
        items = []
        for i in data.get("items", []):
            items.append(ExtractedFoodItem(
                name=i["name"],
                quantity_value=float(i["quantity_value"]),
                quantity_unit=i["quantity_unit"],
                confidence=0.95, 
                extraction_method=ExtractionMethod.SLM
            ))
            
        extraction = MealExtraction(
            meal_type=meal_type,
            raw_transcription=raw_text,
            items=items,
            overall_confidence=0.9
        )
        
        return extraction, 0.9

    @classmethod
    def is_available(cls) -> bool:
        return Llama is not None
