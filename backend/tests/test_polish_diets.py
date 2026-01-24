import asyncio
import sys
import os
import json
from tabulate import tabulate

from src.ai.infrastructure.matching.vector_engine import HybridSearchEngine
from src.ai.infrastructure.nlu.processor import NaturalLanguageProcessor
from src.ai.infrastructure.nlu.slm_extractor import SLMExtractor
from src.ai.application.meal_service import MealRecognitionService

script_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.abspath(os.path.join(script_dir, '..'))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

SCENARIOS = [
    # --- ŚNIADANIA (Breakfast) ---
    "Dwie kromki chleba razowego z masłem i szynką",
    "Bułka kajzerka z twarogiem półtłustym i szczypiorkiem",
    "Jajecznica z 3 jaj na boczku z pomidorem",
    "Parówki z ketchupem i chlebem",
    "Płatki owsiane na mleku z bananem i orzechami",
    "Kanapka z serem żółtym i ogórkiem kiszonym",

    # --- OBIADY (Lunch/Dinner) ---
    "Kotlet schabowy z ziemniakami i mizerią",
    "Kotlet mielony z buraczkami i kaszą gryczaną",
    "Pierś z kurczaka smażona z ryżem i warzywami na patelnię",
    "Pierś z kurczaka smażona z ryżem i warzywami na patelnię",
    "Zupa pomidorowa z makaronem i śmietaną",
    "Rosół z makaronem i marchewką",
    "Zjadłem talerz żurku z jajkiem i kiełbasą",
    "5 pierogów ruskich ze śmietaną i cebulką",
    "Bigos z chlebem i kiełbasą",
    "Gołąbki w sosie pomidorowym z ziemniakami",
    "Placki ziemniaczane ze śmietaną i cukrem",
    "Kotlet mielony z buraczkami i kaszą gryczaną",
    "Barszcz czerwony z uszkami",
    "Kopytka z masłem i bułką tartą",
    "Fasolka po bretońsku z chlebem",

    # --- KOLACJE i PRZEKĄSKI (Supper/Snacks) ---
    "Sałatka jarzynowa z majonezem i chlebem",
    "Kefir i drożdżówka z serem",
    "Zapiekanka z pieczarkami i serem (na bagietce)",
    "Dwa jabłka i jeden banan",
    "Jogurt naturalny z musli",
    "Serek wiejski z rzodkiewką i szczypiorkiem",
    "Kawa z mlekiem i cukrem",
    "Pączek z lukrem",
    "Kiełbasa śląska z grilla z musztardą i chlebem",
    "Śledź w oleju z cebulą",
    "Tost z serem i szynką (sandwich)"
]


async def run_benchmark():
    print(f"Loading products database...")
    seeds_path = os.path.join(backend_root, 'seeds', 'fineli_products.json')
    if not os.path.exists(seeds_path):
        print(f"ERROR: Cannot find {seeds_path}")
        return

    with open(seeds_path, 'r', encoding='utf-8') as f:
        products = json.load(f)["products"]

    patch_path = os.path.join(backend_root, 'seeds', 'staples_patch.json')
    if os.path.exists(patch_path):
        print(f"Loading staples patch...")
        with open(patch_path, 'r', encoding='utf-8') as f:
            patch = json.load(f)
            products.extend(patch)

    print("Initializing AI Services...")
    engine = HybridSearchEngine()
    engine.index_products(products)

    slm = SLMExtractor() if SLMExtractor.is_available() else None
    if slm:
        print("SLM (Bielik) is ACTIVE.")
    else:
        print("SLM is NOT active (using Regex fallback).")

    nlu = NaturalLanguageProcessor()
    service = MealRecognitionService(engine, nlu, slm_extractor=slm)

    print(f"\nRunning {len(SCENARIOS)} scenarios...\n")

    results_table = []

    for i, text in enumerate(SCENARIOS, 1):
        print(f"\n--- Scenario {i}: {text} ---")
        try:
            result = await service.recognize_meal(text)

            rows = []
            for p in result.matched_products:
                print(f"  MATCH: {p.name_pl} | {p.quantity_grams}g | Conf: {p.match_confidence:.2f}")
                print(f"         (Notes: {p.notes})")
                rows.append(f"{p.name_pl} ({p.quantity_grams}g)")

            if result.unmatched_chunks:
                print(f"  UNMATCHED: {result.unmatched_chunks}")

            results_table.append([
                text,
                len(result.matched_products),
                ", ".join(rows),
                str(result.unmatched_chunks) if result.unmatched_chunks else "-"
            ])

        except Exception as e:
            print(f"FAILED: {e}")
            import traceback
            traceback.print_exc()

    print("\n\n=== BENCHMARK REPORT ===")
    print(tabulate(results_table, headers=["Scenario", "Count", "Matches", "Unmatched"], tablefmt="grid"))


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_benchmark())
