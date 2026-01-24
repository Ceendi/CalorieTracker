import re
from typing import List, Tuple, Optional

from src.ai.domain.models import IngredientChunk


class NaturalLanguageProcessor:
    def __init__(self):
        pass

    SYNONYMS = {
        "pyry": "ziemniaki", "pyra": "ziemniak",
        "kartofle": "ziemniaki", "kartofel": "ziemniak",
        "kartofli": "ziemniaki",
        "gryczka": "kasza gryczana", "gryczki": "kasza gryczana",
        "twaróżek": "twaróg",
        "filet": "pierś", "fileta": "pierś",
        "jajka": "jajko", "jajek": "jajko",
        "sery": "ser",
        "parówki": "parówka",
    }

    COMPOSITE_DISHES = {
        "kanapka": ["chleb żytni", "masło"],
        "kanapki": ["chleb żytni", "masło"],
        "jajecznica": ["jajko", "masło"],
        "jajecznicę": ["jajko", "masło"],
        "owsianka": ["płatki owsiane", "mleko"],
        "owsianki": ["płatki owsiane", "mleko"],
    }

    CRITICAL_KEYWORDS = {
        "kurczak": ["kurczak", "kurcz", "drobiow", "chicken"],
        "indyk": ["indyk", "turkey"],
        "wieprzowina": ["wieprzow", "schab", "pork"],
        "wołowina": ["wołow", "beef"],
        "ziemniak": ["ziemniak", "kartofl", "pyry", "potato"],
        "batat": ["batat", "sweet potato"],
        "mleko": ["mleko", "milk"],
        "mleko roślinne": ["sojow", "migdał", "owsian", "kokosow"],
        "masło": [r"\bmasło\b", r"\bmasle\b"],
        "pomidor": [r"\bpomidor\b", r"\bpomidorow"],
        "ogórek": [r"\bogórek\b", r"\bogórk"],
        "jajko": [r"\bjajk\b", r"\bjajeczn"],
        "chleb": [r"\bchleb\b", r"\bpieczyw", r"\bbułk", r"\btost"],
    }

    def normalize_text(self, text: str) -> str:
        text_lower = text.lower()
        for informal, standard in self.SYNONYMS.items():
            text_lower = re.sub(rf'\b{re.escape(informal)}\b', standard, text_lower)
        return text_lower

    def _split_into_chunks(self, text: str) -> List[str]:
        text = re.sub(r'\s+(?:i|oraz|a także|plus)\s+', ', ', text, flags=re.IGNORECASE)
        raw_chunks = re.split(r'[,;]+', text)

        chunks = [c.strip() for c in raw_chunks if c.strip()]
        return chunks

    def _extract_quantity(self, chunk: str) -> Tuple[str, Optional[float], Optional[str]]:
        patterns = [
            (r'(\d+(?:[,.]\d+)?)\s*(g|gram[όwy]*|ml|mililitr[όw]*|sztuk[iy]?|szt\.?|kg|litr[όw]*)\b', True),
            (r'\b(pół|półtora|półtorej)\s*(szklanki|szklankę|szklanka|łyżeczki|łyżeczka|łyżki|łyżka)\b', False),
            (r'\b(szklanka|szklankę|łyżka|łyżkę|łyżeczka|łyżeczkę|kromka|kromkę|plaster|plasterek)\b', False),
            (r'\b(garść|szczypta|odrobina|trochę)\b', False),
        ]

        val, unit = None, None

        for pattern, is_numeric in patterns:
            match = re.search(pattern, chunk, re.IGNORECASE)
            if match:
                if is_numeric:
                    val_str = match.group(1).replace(',', '.')
                    val = float(val_str)
                    unit = match.group(2)
                else:
                    word_qty = match.group(1).lower()
                    if "pół" in word_qty:
                        val = 0.5
                        unit = match.group(2) if len(match.groups()) > 1 else word_qty
                    else:
                        val = 1.0
                        unit = match.group(1)
                break

        return chunk, val, unit

    def _handle_composite_dish(self, chunk: str) -> List[str]:
        chunk_lower = chunk.lower()
        for dish, ingredients in self.COMPOSITE_DISHES.items():
            if dish in chunk_lower:
                expanded = ingredients.copy()

                extra_match = re.search(r'\s+ze?\s+(.+)', chunk_lower)
                if extra_match:
                    extras_raw = extra_match.group(1).strip()
                    extras_split = re.split(r'\s+(?:i|oraz|a także|plus)\s+|[,;]+', extras_raw)
                    for e in extras_split:
                        if e.strip():
                            expanded.append(e.strip())
                return expanded
        return [chunk]

    def verify_keyword_consistency(self, query: str, product_name: str) -> bool:
        query_lower = query.lower()
        product_lower = product_name.lower()

        for category, synonyms in self.CRITICAL_KEYWORDS.items():
            has_word = any(re.search(s, query_lower) if "\\" in s else s in query_lower for s in synonyms)

            if has_word:
                if not any(re.search(s, product_lower) if "\\" in s else s in product_lower for s in synonyms):
                    if category == "masło" and "masłowa" in product_lower and "masło" not in product_lower:
                        return False

                    return False
        return True

    def process_text(self, text: str) -> List[IngredientChunk]:
        if not text:
            return []

        text = self.normalize_text(text)
        raw_chunks = self._split_into_chunks(text)

        processed_chunks = []
        for raw_c in raw_chunks:
            sub_ingredients = self._handle_composite_dish(raw_c)

            for ing_text in sub_ingredients:
                cleaned, val, unit = self._extract_quantity(ing_text)

                processed_chunks.append(IngredientChunk(
                    original_text=ing_text,
                    text_for_search=cleaned,
                    quantity_value=val,
                    quantity_unit=unit,
                    is_composite=len(sub_ingredients) > 1
                ))

        return processed_chunks
