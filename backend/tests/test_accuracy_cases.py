import sys
import os
import asyncio
import json
from loguru import logger

from src.ai.infrastructure.matching.vector_engine import HybridSearchEngine
from src.ai.infrastructure.nlu.processor import NaturalLanguageProcessor
from src.ai.application.meal_service import MealRecognitionService

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

TEST_CASES = [
    {
        "query": "ziemniaki",
        "expected": ["ziemniak", "ziemniaki gotowane", "ziemniaki"],
        "forbidden": ["omlet", "placki", "zapiekanka"]
    },
    {
        "query": "omlet z bananem",
        "expected": ["jajk", "banan"],
        "forbidden": ["omlet z warzywami", "omlet z serem"]
    }
]


async def run_accuracy_tests():
    logger.info("Loading products...")
    path = os.path.join(os.path.dirname(__file__), '..', 'seeds', 'fineli_products.json')
    with open(path, 'r', encoding='utf-8') as f:
        products = json.load(f)["products"]

    potato_exists = any(p['name_pl'].lower() in ['ziemniak', 'ziemniaki'] for p in products)
    if not potato_exists:
        print("WARN: 'Ziemniak' missing in DB. Injecting mock for testing.")
        products.append({
            "id": 99999,
            "name_pl": "Ziemniak",
            "name_en": "Potato",
            "category": "VEGROOT",
            "kcal_100g": 77,
            "units": [{"name": "sztuka", "weight_g": 90}]
        })

    engine = HybridSearchEngine()
    engine.index_products(products)

    from src.ai.infrastructure.nlu.slm_extractor import SLMExtractor

    logger.info("Initializing SLM Extractor...")
    slm_extractor = SLMExtractor()

    processor = NaturalLanguageProcessor()
    service = MealRecognitionService(engine, processor, slm_extractor=slm_extractor)

    passed = 0
    for case in TEST_CASES:
        print(f"\nTESTING: {case['query']}")
        result = await service.recognize_meal(case["query"])

        matched_names = [p.name_pl.lower() for p in result.matched_products]
        print(f"RESULTS: {', '.join(matched_names)}")

        for p in result.matched_products:
            print(f"  > {p.name_pl} (Conf: {p.match_confidence}, Note: {p.notes})")

        success = True
        for exp in case["expected"]:
            if not any(exp in name for name in matched_names):
                print(f"❌ MISSING EXPECTED: {exp}")
                success = False

        for forb in case["forbidden"]:
            if any(forb in name for name in matched_names):
                print(f"❌ FOUND FORBIDDEN: {forb}")
                success = False

        if success:
            print("✅ PASS")
            passed += 1
        else:
            print("❌ FAIL")

    print("\nDEBUG: RAW SEARCH 'ziemniak'")
    cands = engine.search("ziemniak", top_k=10)
    for c in cands:
        print(f"- {c.name} (Score: {c.score:.3f}, Cat: {c.category})")

    print("\nDEBUG: RAW SEARCH 'jajko'")
    cands = engine.search("jajko", top_k=10)
    for c in cands:
        print(f"- {c.name} (Score: {c.score:.3f}, Cat: {c.category})")

    print(f"\nScore: {passed}/{len(TEST_CASES)}")


if __name__ == "__main__":
    asyncio.run(run_accuracy_tests())
