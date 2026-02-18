import json
import asyncio
from typing import Tuple
from loguru import logger
from google import genai
from google.genai import types

from src.ai.domain.models import (
    MealExtraction,
    ExtractedFoodItem,
    MealType,
    ExtractionMethod
)
from src.core.config import settings


VISION_SYSTEM_PROMPT = """
Jesteś ekspertem dietetykiem i analitykiem żywności. Twoim zadaniem jest przeanalizowanie zdjęcia potrawy i wyodrębnienie z niego wszystkich składników wraz z szacowaną wagą i wartościami odżywczymi.

ZASADY:
1. Rozpoznaj wszystkie widoczne składniki.
2. Dla dań złożonych (np. kanapka, sałatka) wymień poszczególne składniki (np. chleb, szynka, masło, pomidor).
3. Dla dań jednorodnych/gotowych (np. pierogi, zupa, lasagne) potraktuj je jako jedną pozycję, chyba że wyraźnie widać dodatki (np. śmietana, boczek).
4. Jednostka i ilość (quantity_value + quantity_unit):
   - Dla produktów policzalnych (jajka, owoce, bułki, pierogi, kotlety, parówki) używaj "sztuka" z liczbą sztuk (np. quantity_value=3, quantity_unit="sztuka").
   - Dla produktów sypkich, płynnych, mięs, wędlin i pozostałych używaj "g" z wagą w gramach.
5. Oszacuj makroskładniki (kcal, białko, tłuszcze, węglowodany) dla CAŁEJ porcji którą widzisz (NIE na 100g, NIE na 1 sztukę — na WSZYSTKO co widzisz danego składnika).
6. Określ typ posiłku (śniadanie, drugie_śniadanie, obiad, podwieczorek, kolacja, przekąska).
7. Używaj nazw BAZOWYCH składników, jakie znajdziesz w bazie wartości odżywczych, np.:
   - "sos pomidorowy" → "przecier pomidorowy"
   - "sos majonezowy" → "majonez"
   - Nie używaj nazw dań złożonych jako składników (np. nie "sos bolognese" tylko osobno "mięso mielone", "przecier pomidorowy").
8. Zwróć wynik TYLKO w formacie JSON zgodnym ze schematem.

Format JSON:
{
  "meal_type": "string (enum)",
  "items": [
    {
      "name": "string (nazwa produktu po polsku, bazowa nazwa składnika)",
      "quantity_value": float (ilość: gramy LUB sztuki w zależności od quantity_unit),
      "quantity_unit": "g | sztuka",
      "kcal": float,
      "protein": float,
      "fat": float,
      "carbs": float,
      "confidence": float (0.0-1.0)
    }
  ]
}
"""


class VisionExtractor:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            logger.warning("GEMINI_API_KEY not set. VisionExtractor will not work.")

    async def extract_from_image(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> Tuple[MealExtraction, float]:
        if not self.client:
            logger.error("VisionExtractor: Client not initialized (missing API key)")
            return self._empty_result("Missing API Key"), 0.0

        try:
            # Since google-genai client calls are synchronous by default in this version or we wrap them
            # We will use asyncio.to_thread to avoid blocking the event loop
            
            response_schema = {
                "type": "OBJECT",
                "properties": {
                    "meal_type": {
                        "type": "STRING",
                        "enum": ["śniadanie", "drugie_śniadanie", "obiad", "podwieczorek", "kolacja", "przekąska"]
                    },
                    "items": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "name": {"type": "STRING"},
                                "quantity_value": {"type": "NUMBER"},
                                "quantity_unit": {"type": "STRING", "enum": ["g", "sztuka"]},
                                "kcal": {"type": "NUMBER"},
                                "protein": {"type": "NUMBER"},
                                "fat": {"type": "NUMBER"},
                                "carbs": {"type": "NUMBER"},
                                "confidence": {"type": "NUMBER"}
                            },
                            "required": ["name", "quantity_value", "quantity_unit", "kcal", "protein", "fat", "carbs"]
                        }
                    }
                },
                "required": ["meal_type", "items"]
            }

            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model='gemini-3-flash-preview',
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=VISION_SYSTEM_PROMPT),
                            types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=response_schema,
                    temperature=0.1
                )
            )

            response_text = response.text
            data = json.loads(response_text)
            return self._parse_json_result(data)

        except Exception as e:
            logger.error(f"Vision extraction failed: {e}")
            return self._empty_result(f"Error: {str(e)}"), 0.0

    def _parse_json_result(self, data: dict) -> Tuple[MealExtraction, float]:
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
                quantity_unit=i.get("quantity_unit", "g"),
                confidence=float(i.get("confidence", 0.9)),
                extraction_method=ExtractionMethod.SLM,
                kcal=float(i.get("kcal", 0)),
                protein=float(i.get("protein", 0)),
                fat=float(i.get("fat", 0)),
                carbs=float(i.get("carbs", 0))
            ))

        extraction = MealExtraction(
            meal_type=meal_type,
            raw_transcription="[Analiza Obrazu]",
            items=items,
            overall_confidence=0.9
        )

        return extraction, 0.9

    def _empty_result(self, reason: str) -> MealExtraction:
        return MealExtraction(
            meal_type=MealType.SNACK,
            raw_transcription=f"Failed: {reason}",
            items=[],
            overall_confidence=0.0
        )
