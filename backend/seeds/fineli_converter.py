"""
Fineli to Polish JSON Converter
================================
Converts Finnish Fineli food database CSV files to Polish-friendly JSON format.

Output:
    seeds/fineli_products.json
"""

import csv
import json
from pathlib import Path
from dataclasses import dataclass, field
import re

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_PATH = BASE_DIR / "fineli_products.json"

NUTRIENT_CODES = {
    "ENERC": "energy_kj",
    "PROT": "protein",
    "FAT": "fat",
    "CHOAVL": "carbs",
}

UNIT_MAPPING = {
    "KPL_S": ("Sztuka (mała)", 1, True),
    "KPL_M": ("Sztuka (średnia)", 2, True),
    "KPL_L": ("Sztuka (duża)", 3, True),
    "RKL": ("Łyżka", 4, False),
    "TL": ("Łyżeczka", 5, False),
    "DL": ("Szklanka", 6, False),
    "PORTS": ("Porcja (mała)", 10, False),
    "PORTM": ("Porcja (średnia)", 11, False),
    "PORTL": ("Porcja (duża)", 12, False),
}

INCLUDED_CATEGORIES = {
    "VEGFRESH", "VEGCANN", "VEGPOT", "VEGDISH", "VEGJUICE",
    "FRUFRESH", "BERFRESH", "FRUBDISH", "FRUBJUIC",
    "MEATCUTS", "MSTEAK", "POULTRY", "SAUSAGE", "SAUSCUTS", "MEATPROD",
    "FISH", "SEAFOOD", "FISHPROD",
    "MILKFF", "MILKHF", "MILKLF", "SMILK", "CREAM", "SOUCREAM",
    "YOGHURT", "CURD", "CHEESUNC", "CHEESPRO", "CHEESCUR",
    "BUTTER", "BUTTEHIG", "BUTTELOW",
    "EGGS", "EGGMIX",
    "FLOUR", "PORR", "CERBAR", "CERBRKF",
    "LEGUMES", "LEGUPROD",
    "OIL", "FATCOOK", "FATANIM", "VEGFATHI", "VEGFATLO",
    "SUGADD", "INGRMISC", "SPICES", "SAVSAUCE", "SPISAUCE",
    "BRWHITE", "BRRYE", "BRMIX", "BUN",
}

EXCLUDED_PATTERNS = [
    r"PORO", r"LAKKA", r"MESIMARJ", r"RUISLEIP", r"KARJALAN", r"KALAKUK",
    r"INFANT", r"TEOLLINEN", r"RAVINTOLA", r"ELK", r"TALKKUNA",
    r"LINGONBERRY", r"SEA BUCKTHORN", r"ROWANBERRY", r"FINNISH OVEN",
    r"SISKONMAKKARA", r"LAUANTAI", r"HÄRKIS",
]

EXCLUDED_IDS = {
    125, 142, 602, 641, 565, 570, 568, 593, 657, 653, 655, 658, 516, 682,
    809, 810, 811, 825, 815, 816, 1023, 1000, 1001, 1025, 1005, 1006, 1007,
    1268, 1032, 1107, 1108, 1111, 1278, 1279, 1280, 1289, 1290, 1298,
    1503, 1507, 1506, 1516, 1518, 1530, 1531, 1532, 1546, 1547, 1582,
    3005, 3006, 3014, 3015, 3222, 3231, 3232, 6026, 7610, 7647, 8001,
    8004, 8008, 8011, 7090, 11146, 11132, 11157, 11123, 11124,
    606, 612, 616, 627, 11572, 11581, 675, 684, 689, 637, 642, 644, 691,
    29232, 11145, 29064, 11165, 30423, 11568, 11092, 29772, 30275,
    30316, 30319, 30612, 30614, 30616, 30617, 30619, 30621, 30629,
    31487, 31488, 31496, 31543, 31809, 31832, 31833,
    31834, 31835, 31837, 31838, 31839, 31840, 31841, 31842, 31845, 31846,
    31847, 31848, 31854, 31859, 31856, 31857, 31858, 31860, 31861,
    31862, 31863, 31868, 31869, 31870, 31871, 31872, 31877, 31879, 31881,
    32459, 32460, 32461, 32462, 32463, 32465, 32466, 32467, 32468,
    32469, 32470, 32472, 33663, 33664, 33666, 33670, 35637,
    33756, 33783, 33847, 33866, 33867, 32515, 32570,
    34242, 34246, 34247, 33212, 33214, 33215, 33216, 33219, 33059,
    35295, 33660, 33708, 35160, 33704, 33673, 33674, 33677, 33680,
    33694, 33699, 35128, 35219, 34842, 31659, 31660, 31864, 31865, 31867,
    32511, 33531, 35560, 32730,
    33100, 33101, 33103, 31945, 33342, 33344, 32664, 32665, 32666,
    32667, 32668, 32669, 32670, 32671, 32672, 31888, 32673, 32676,
    33080, 35501, 33160, 33161, 31926, 33169, 34079, 34080, 35169,
    33098, 32947, 32949, 32950, 32951, 32678, 32679, 32680, 31947,
    31911, 31946, 32013, 32015, 32062, 32067, 32080, 32084, 32085,
    32088, 32142, 32145, 32068, 32070, 32071, 33125, 33134, 33727,
    32959, 32966, 32976, 32960, 32975, 32980,
    32065, 32073, 33124, 33135, 33848, 35008, 35009,
    33395, 33396, 33397, 33402, 32783, 32121, 32130, 33185,
    33163, 33730, 33732, 33132, 33133, 35195, 33136, 33890, 34971,
    32602, 32155, 32157, 32159, 32161, 32186, 32898, 32899,
    33561, 33562, 32163, 32197, 32722, 34184, 34220, 32354, 32437,
    33486, 33487, 33488, 33489, 34942, 34944, 35203, 32357, 32431,
    33496, 34914, 34932, 35565, 35566, 32366, 32367, 32418, 32562,
    32774, 32849, 32422, 32423, 32424, 32446, 32447,
    32438, 32439, 32440, 32444, 32445, 32441, 32442, 32443,
    32473, 32474, 32541, 32567, 33168, 33190, 33554, 33555, 33556,
    34841, 34980, 32477, 32479, 32481, 33594, 33720, 33721, 32568,
    32592, 32593, 32594, 32595, 32596, 32597, 32599,
    32735, 32737, 33141, 33142, 33295, 33298, 33245, 33280, 33284,
    33675, 33678, 33679, 33681, 33682, 33042, 31891, 31894, 31900,
    33111, 33117, 33671, 33689, 33710, 33714, 35177, 34862, 34998,
    34984, 35199, 35634, 35636, 33760, 33790, 33791, 33792,
    33852, 33903, 33924, 34127, 33729, 34786, 34966, 34970, 35603,
    33466, 33587, 29819, 30428, 30443, 30456, 34265, 34679,
    32900, 32901, 32906, 32907, 35153, 35172,
    34902, 34904, 35628, 35190, 35193, 35629, 35630, 34948, 34964,
    34637, 34639, 35632, 35633, 34724, 34726
}

MANUAL_TRANSLATIONS = {
    40: "Baton zbożowy (ogólny)",
    313: "Mieszanka warzywna (mrożona)",
    351: "Dynia w occie / marynowana",
}

try:
    from translations_map import TRANSLATION_MAP
except ImportError:
    print("Warning: Could not import translations_map.py. Translations will be missing.")
    TRANSLATION_MAP = {}


@dataclass
class UnitInfo:
    name_pl: str
    weight_g: float
    priority: int


@dataclass
class FineliProduct:
    food_id: int
    name_en: str
    name_fi: str
    category: str
    process_type: str
    energy_kj: float = 0.0
    protein: float = 0.0
    fat: float = 0.0
    carbs: float = 0.0
    units: list = field(default_factory=list)

    @property
    def kcal_100g(self) -> float:
        return round(self.energy_kj / 4.184, 1)

    def to_dict(self) -> dict:
        sorted_units = sorted(self.units, key=lambda u: u.priority)
        selected = sorted_units[:5]

        name_pl = TRANSLATION_MAP.get(self.name_en, "")
        if not name_pl and self.food_id in MANUAL_TRANSLATIONS:
            name_pl = MANUAL_TRANSLATIONS[self.food_id]

        return {
            "id": self.food_id,
            "name_en": self.name_en,
            "name_pl": name_pl,
            "category": self.category,
            "kcal_100g": self.kcal_100g,
            "protein_100g": round(self.protein, 1),
            "fat_100g": round(self.fat, 1),
            "carbs_100g": round(self.carbs, 1),
            "units": [
                {"name": u.name_pl, "weight_g": round(u.weight_g, 1)}
                for u in selected
            ]
        }


def parse_finnish_decimal(value: str) -> float:
    if not value or value.strip() == "":
        return 0.0
    try:
        cleaned = value.strip().replace(",", ".")
        return float(cleaned)
    except (ValueError, AttributeError):
        return 0.0


def is_excluded_product(name_fi: str) -> bool:
    name_upper = name_fi.upper()
    for pattern in EXCLUDED_PATTERNS:
        if re.search(pattern, name_upper):
            return True
    return False


def is_category_included(fuclass: str, igclass: str) -> bool:
    return fuclass in INCLUDED_CATEGORIES or igclass in INCLUDED_CATEGORIES


def load_csv(filename: str, delimiter=";") -> list[dict]:
    filepath = DATA_DIR / filename
    encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]

    for encoding in encodings:
        try:
            with open(filepath, "r", encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                return list(reader)
        except (UnicodeDecodeError, UnicodeError):
            continue

    raise ValueError(f"Could not read {filename} with any known encoding")


def load_foods() -> dict[int, dict]:
    rows = load_csv("food.csv")
    result = {}
    for row in rows:
        try:
            food_id = int(row["FOODID"])
            result[food_id] = {
                "name_fi": row.get("FOODNAME", ""),
                "food_type": row.get("FOODTYPE", ""),
                "process": row.get("PROCESS", ""),
                "fuclass": row.get("FUCLASS", ""),
                "igclass": row.get("IGCLASS", ""),
            }
        except (ValueError, KeyError):
            continue
    return result


def load_names_en() -> dict[int, str]:
    rows = load_csv("foodname_EN.csv")
    result = {}
    for row in rows:
        try:
            food_id = int(row["FOODID"])
            result[food_id] = row.get("FOODNAME", "").strip()
        except (ValueError, KeyError):
            continue
    return result


def load_nutrients() -> dict[int, dict[str, float]]:
    rows = load_csv("component_value.csv")
    result = {}

    for row in rows:
        try:
            food_id = int(row["FOODID"])
            nutrient_code = row.get("EUFDNAME", "")
            value = parse_finnish_decimal(row.get("BESTLOC", "0"))

            if nutrient_code in NUTRIENT_CODES:
                if food_id not in result:
                    result[food_id] = {}
                result[food_id][NUTRIENT_CODES[nutrient_code]] = value
        except (ValueError, KeyError):
            continue

    return result


def load_units() -> dict[int, list[tuple[str, float]]]:
    rows = load_csv("foodaddunit.csv")
    result = {}

    for row in rows:
        try:
            food_id = int(row["FOODID"])
            unit_code = row.get("FOODUNIT", "")
            mass = parse_finnish_decimal(row.get("MASS", "0"))

            if unit_code in UNIT_MAPPING and mass > 0:
                if food_id not in result:
                    result[food_id] = []
                result[food_id].append((unit_code, mass))
        except (ValueError, KeyError):
            continue

    return result


def build_products() -> list[FineliProduct]:
    print("Loading CSV files...")

    foods = load_foods()
    names_en = load_names_en()
    nutrients = load_nutrients()
    units = load_units()

    print(f"  Foods: {len(foods)}")
    print(f"  English names: {len(names_en)}")
    print(f"  Nutrient entries: {len(nutrients)}")
    print(f"  Unit entries: {len(units)}")

    products = []
    skipped_category = 0
    skipped_pattern = 0
    skipped_no_name = 0
    skipped_id = 0

    for food_id, food_data in foods.items():
        if food_id not in names_en:
            skipped_no_name += 1
            continue

        if food_id in EXCLUDED_IDS:
            skipped_id += 1
            continue

        if not is_category_included(food_data["fuclass"], food_data["igclass"]):
            skipped_category += 1
            continue

        if is_excluded_product(food_data["name_fi"]):
            skipped_pattern += 1
            continue

        nutrient_data = nutrients.get(food_id, {})

        product = FineliProduct(
            food_id=food_id,
            name_en=names_en[food_id],
            name_fi=food_data["name_fi"],
            category=food_data["fuclass"],
            process_type=food_data["process"],
            energy_kj=nutrient_data.get("energy_kj", 0),
            protein=nutrient_data.get("protein", 0),
            fat=nutrient_data.get("fat", 0),
            carbs=nutrient_data.get("carbs", 0),
        )

        if food_id in units:
            for unit_code, mass in units[food_id]:
                unit_name_pl, priority, _ = UNIT_MAPPING[unit_code]
                weight_g = mass

                if unit_code == "DL":
                    weight_g = mass * 2.5

                product.units.append(UnitInfo(
                    name_pl=unit_name_pl,
                    weight_g=weight_g,
                    priority=priority
                ))

        products.append(product)

    print(f"\nFiltering results:")
    print(f"  Skipped (no English name): {skipped_no_name}")
    print(f"  Skipped (category): {skipped_category}")
    print(f"  Skipped (Finnish-specific): {skipped_pattern}")
    print(f"  Skipped (excluded ID): {skipped_id}")
    print(f"  Included: {len(products)}")

    return products


def main():
    print("=" * 60)
    print("Fineli to Polish JSON Converter")
    print("=" * 60)

    products = build_products()

    output = {
        "source": "Fineli (Finnish Food Composition Database)",
        "note": "Polish translations applied from translations_map.py",
        "glass_conversion": "Szklanka = DL × 2.5 (250ml Polish standard)",
        "products": [p.to_dict() for p in products]
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(products)} products to {OUTPUT_PATH}")

    if products:
        sample = products[0]
        print(f"\nSample product:")
        print(f"  ID: {sample.food_id}")
        print(f"  EN: {sample.name_en}")
        print(f"  kcal: {sample.kcal_100g}")
        print(f"  P/F/C: {sample.protein}/{sample.fat}/{sample.carbs}")
        print(f"  Units: {len(sample.units)}")


if __name__ == "__main__":
    main()
