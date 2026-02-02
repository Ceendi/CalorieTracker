import re
from typing import List, Tuple, Optional

from src.ai.domain.models import IngredientChunk


class NaturalLanguageProcessor:
    POLISH_NUMERALS = {
        "jeden": 1.0, "jedna": 1.0, "jedno": 1.0, "jedną": 1.0,
        "dwa": 2.0, "dwie": 2.0, "dwóch": 2.0, "dwoje": 2.0, "dwiema": 2.0,
        "trzy": 3.0, "trzech": 3.0, "trzema": 3.0,
        "cztery": 4.0, "czterech": 4.0, "czterema": 4.0,
        "pięć": 5.0, "pięciu": 5.0, "pięcioma": 5.0,
        "sześć": 6.0, "sześciu": 6.0,
        "siedem": 7.0, "siedmiu": 7.0,
        "osiem": 8.0, "ośmiu": 8.0,
        "dziewięć": 9.0, "dziewięciu": 9.0,
        "dziesięć": 10.0, "dziesięciu": 10.0,
        "pół": 0.5, "półtora": 1.5, "półtorej": 1.5,
        "kilka": 3.0, "parę": 2.0, "pare": 2.0,
    }

    def __init__(self):
        pass

    SYNONYMS = {
        # Ziemniaki / Potatoes
        "pyry": "ziemniaki", "pyra": "ziemniak",
        "kartofle": "ziemniaki", "kartofel": "ziemniak",
        "kartofli": "ziemniaki", "kartofla": "ziemniak",
        "ziemniaków": "ziemniaki", "ziemniaka": "ziemniak",

        # Kasze / Groats
        "gryczka": "kasza gryczana", "gryczki": "kasza gryczana",
        "jaglanka": "kasza jaglana", "jaglanki": "kasza jaglana",
        "pęczak": "kasza pęczak", "pęczaku": "kasza pęczak",

        # Nabiał / Dairy
        "twaróżek": "twaróg", "twarożek": "twaróg", "twarogu": "twaróg",
        "sery": "ser", "sera": "ser", "serów": "ser",
        "jogurty": "jogurt", "jogurtu": "jogurt",
        "mleka": "mleko",
        "śmietany": "śmietana", "śmietanki": "śmietanka",

        # Jaja / Eggs
        "jajka": "jajko", "jajek": "jajko", "jaj": "jajko",
        "jajeczko": "jajko", "jajeczka": "jajko",

        # Mięso / Meat
        "filet": "pierś", "fileta": "pierś", "filety": "pierś",
        "piersi": "pierś", "piersią": "pierś",
        "parówki": "parówka", "parówek": "parówka",
        "kiełbasy": "kiełbasa", "kiełbasę": "kiełbasa", "kiełbas": "kiełbasa",
        "szynki": "szynka", "szynkę": "szynka",
        "boczku": "boczek", "boczki": "boczek",
        "kotlety": "kotlet", "kotleta": "kotlet",

        # Warzywa / Vegetables
        "pomidory": "pomidor", "pomidorów": "pomidor", "pomidora": "pomidor",
        "ogórki": "ogórek", "ogórków": "ogórek", "ogórka": "ogórek",
        "cebuli": "cebula", "cebulę": "cebula", "cebulki": "cebula",
        "marchewki": "marchew", "marchewkę": "marchew", "marchwi": "marchew",
        "papryki": "papryka", "paprykę": "papryka",
        "kapusty": "kapusta", "kapustę": "kapusta",
        "sałaty": "sałata", "sałatę": "sałata",
        "buraki": "burak", "buraków": "burak", "buraka": "burak",
        "szpinaku": "szpinak",

        # Owoce / Fruits
        "jabłka": "jabłko", "jabłek": "jabłko", "jabłkiem": "jabłko",
        "banany": "banan", "bananów": "banan", "banana": "banan",
        "pomarańcze": "pomarańcza", "pomarańczy": "pomarańcza",
        "gruszki": "gruszka", "gruszek": "gruszka",
        "truskawki": "truskawka", "truskawek": "truskawka",
        "maliny": "malina", "malin": "malina",
        "winogrona": "winogrono", "winogron": "winogrono",

        # Pieczywo / Bread
        "chleba": "chleb", "chlebek": "chleb",
        "bułki": "bułka", "bułek": "bułka", "bułkę": "bułka",
        "tosty": "tost", "tostów": "tost",
        "rogaliki": "rogalik", "rogalików": "rogalik",

        # Makarony i ryż / Pasta and rice
        "makaronu": "makaron", "makarony": "makaron",
        "spaghetti": "makaron spaghetti", "spagetti": "makaron spaghetti",
        "penne": "makaron penne", "tagliatelle": "makaron tagliatelle",
        "ryżu": "ryż",

        # Napoje / Beverages
        "kawy": "kawa", "kawę": "kawa", "kawka": "kawa",
        "herbaty": "herbata", "herbatę": "herbata", "herbatka": "herbata",

        # Sosy / Sauces → bazowe składniki
        "sos pomidorowy": "przecier pomidorowy",
        "sosu pomidorowego": "przecier pomidorowy",
        "sosie pomidorowym": "przecier pomidorowy",
        "sos majonezowy": "majonez",

        # Regionalne / Regional
        "żurek": "żur", "żurku": "żur",
        "kluski": "kluska", "klusek": "kluska",
        "pierogi": "pieróg", "pierogów": "pieróg",
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
        "makaron": ["makaron", "spaghet", "penne", "tagliatelle", "pasta"],
        "fasola": ["fasol", "fasolka"],
        "ryż": [r"\bryż\b", r"\bryżu\b", "rice"],
        "kasza": ["kasza", "kaszy"],
        "kapusta": ["kapust"],
        "zupa": [r"\bzup[aęy]\b", r"\bzupk"],
        "surówka": ["surówk"],
        "sałatka": ["sałatk", "sałata"],
    }

    def normalize_text(self, text: str) -> str:
        text_lower = text.lower()
        for informal, standard in self.SYNONYMS.items():
            text_lower = re.sub(rf'\b{re.escape(informal)}\b', standard, text_lower)
        # Remove consecutive duplicate words caused by synonym expansion
        # e.g. "makaron spaghetti" → synonym "spaghetti"→"makaron spaghetti" → "makaron makaron spaghetti"
        text_lower = re.sub(r'\b(\w+)(\s+\1)+\b', r'\1', text_lower)
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
            (r'\b(garść|szczypta|odrobina|trochę|dużo|mało)\b', False),
        ]

        val, unit = None, None
        cleaned_text = chunk

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

                cleaned_text = chunk[:match.start()] + chunk[match.end():]
                cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
                break

        if val is None:
            cleaned_text, val = self._extract_polish_numeral(cleaned_text)

        return cleaned_text if cleaned_text else chunk, val, unit

    def _extract_polish_numeral(self, text: str) -> Tuple[str, Optional[float]]:
        text_lower = text.lower()
        for word, num in self.POLISH_NUMERALS.items():
            pattern = rf'\b{re.escape(word)}\b'
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                cleaned = text[:match.start()] + text[match.end():]
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                return cleaned, num
        return text, None

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
            query_has = any(
                re.search(s, query_lower) if "\\" in s else s in query_lower
                for s in synonyms
            )
            product_has = any(
                re.search(s, product_lower) if "\\" in s else s in product_lower
                for s in synonyms
            )

            # Forward: query mentions category X but product doesn't
            if query_has and not product_has:
                return False
            # Reverse: product contains category Y but query doesn't mention it
            if product_has and not query_has:
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
