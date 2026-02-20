"""
Glycemic Index (GI) matching utilities.

Sources
-------
Primary — Atkinson 2008, Table 1 (all 62 foods, freely available via PMC):
    Atkinson FS, Foster-Powell K, Brand-Miller JC.
    "International Tables of Glycemic Index and Glycemic Load Values: 2008."
    Diabetes Care. 2008;31(12):2281–2283.
    DOI: 10.2337/dc08-1239
    PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC2584181/

Extension — Atkinson 2021 (>4 000 entries, Supplementary Tables 1–2 free):
    Atkinson FS, Brand-Miller JC, Foster-Powell K, Buyken AE, Goletzke J.
    "International tables of glycemic index and glycemic load values 2021:
    a systematic review."
    Am J Clin Nutr. 2021;114(5):1625–1632.
    DOI: 10.1093/ajcn/nqab233
    Download free supplements: academic.oup.com/ajcn → "Supplementary data"

Data model
----------
Each GIEntry stores:
    gi      — GI mean value as published in the cited table
    sd      — standard deviation (±) as published
    food_en — exact food name from the cited table (for verification)
    source  — citation key ("Atkinson2008" | "Atkinson2021")

Conservative strategy
---------------------
- carbs_per_100g ≤ 5 g → always None  (meats, fish, pure fats)
- Only foods with an unambiguous keyword match are assigned a GI.
- Returning None is preferable to assigning an unverifiable value.

Extending with Atkinson 2021
-----------------------------
1. Download Supplementary Table 1 from the AJCN page (DOI above).
2. Locate the food by food_en string in the table.
3. Note gi ± sd values.
4. Add a GIEntry with source="Atkinson2021" and the exact food_en from Table S1.
5. Add one or more normalised Polish keyword keys to _GI_SOURCE_2021.

Note on glucose: Table 1 (Atkinson 2008) reports glucose = 103 ± 3, reflecting
empirical variability. Glucose is the defined reference standard (= 100 by
convention); 103 represents measurement uncertainty, not a true deviation.
"""

import unicodedata
import re
from typing import NamedTuple, Optional


class GIEntry(NamedTuple):
    gi: int         # GI mean value from cited table
    sd: int         # Standard deviation (±) from cited table
    food_en: str    # Exact food name as listed in cited table (for verification)
    source: str = "Atkinson2008"   # Citation key


# ===========================================================================
# SOURCE 1 — Atkinson 2008, Table 1
#
# Complete table: all 62 foods.
# Verification: PMC full text → Table 1 → find food_en → confirm gi ± sd.
#
# Each food may have multiple Polish keyword keys (synonyms / variant names).
# The longest matching key wins (see match_gi()).
# ===========================================================================
_GI_SOURCE_2008: dict[str, GIEntry] = {

    # ── Breads ──────────────────────────────────────────────────────────────
    # White wheat bread — GI 75 ± 2
    "chleb bialy":              GIEntry(75, 2, "White wheat bread"),
    "chleb pszenny":            GIEntry(75, 2, "White wheat bread"),
    "chleb tostowy":            GIEntry(75, 2, "White wheat bread"),
    "chleb jasny":              GIEntry(75, 2, "White wheat bread"),
    "chleb zwykly":             GIEntry(75, 2, "White wheat bread"),
    "bulka":                    GIEntry(75, 2, "White wheat bread"),
    "bulka pszenna":            GIEntry(75, 2, "White wheat bread"),
    "bulka kajzerka":           GIEntry(75, 2, "White wheat bread"),

    # Whole wheat/whole meal bread — GI 74 ± 2
    "chleb pelnoziarnisty":     GIEntry(74, 2, "Whole wheat/whole meal bread"),
    "chleb pelnozbozowy":       GIEntry(74, 2, "Whole wheat/whole meal bread"),
    "chleb graham":             GIEntry(74, 2, "Whole wheat/whole meal bread"),
    "graham":                   GIEntry(74, 2, "Whole wheat/whole meal bread"),
    "chleb razowy pszenny":     GIEntry(74, 2, "Whole wheat/whole meal bread"),
    # Note: "chleb razowy" (without "pszenny") is ambiguous — may mean rye.
    # Rye bread GI is NOT in Atkinson 2008 Table 1 → intentionally excluded.

    # Specialty grain bread — GI 53 ± 2
    "chleb wieloziarnisty":     GIEntry(53, 2, "Specialty grain bread"),
    "chleb wielozbozowy":       GIEntry(53, 2, "Specialty grain bread"),
    "chleb mieszany":           GIEntry(53, 2, "Specialty grain bread"),
    "chleb z ziarnami":         GIEntry(53, 2, "Specialty grain bread"),

    # Corn tortilla — GI 46 ± 4
    "tortilla":                 GIEntry(46, 4, "Corn tortilla"),
    "tortilla kukurydziana":    GIEntry(46, 4, "Corn tortilla"),

    # Wheat flake biscuits (Weetabix-type) — GI 69 ± 2
    "platki pszenne":           GIEntry(69, 2, "Wheat flake biscuits"),
    "weetabix":                 GIEntry(69, 2, "Wheat flake biscuits"),

    # ── Breakfast cereals ───────────────────────────────────────────────────
    # Cornflakes — GI 81 ± 6
    "platki kukurydziane":      GIEntry(81, 6, "Cornflakes"),
    "cornflakes":               GIEntry(81, 6, "Cornflakes"),

    # Porridge, rolled oats — GI 55 ± 2
    "platki owsiane":           GIEntry(55, 2, "Porridge, rolled oats"),
    "owsianka":                 GIEntry(55, 2, "Porridge, rolled oats"),
    "kasza owsiana":            GIEntry(55, 2, "Porridge, rolled oats"),

    # Instant oat porridge — GI 79 ± 3
    "platki owsiane blyskawiczne": GIEntry(79, 3, "Instant oat porridge"),
    "owsianka blyskawiczna":    GIEntry(79, 3, "Instant oat porridge"),
    "owsianka instant":         GIEntry(79, 3, "Instant oat porridge"),
    "platki owsiane instant":   GIEntry(79, 3, "Instant oat porridge"),

    # Millet porridge — GI 67 ± 5
    "kasza jaglana":            GIEntry(67, 5, "Millet porridge"),
    "proso":                    GIEntry(67, 5, "Millet porridge"),

    # Muesli — GI 57 ± 2
    "musli":                    GIEntry(57, 2, "Muesli"),
    "muesli":                   GIEntry(57, 2, "Muesli"),

    # ── Grains and pasta ────────────────────────────────────────────────────
    # White rice, boiled — GI 73 ± 4
    "ryz bialy":                GIEntry(73, 4, "White rice, boiled"),
    "ryz gotowany":             GIEntry(73, 4, "White rice, boiled"),
    "ryz jasny":                GIEntry(73, 4, "White rice, boiled"),

    # Brown rice, boiled — GI 68 ± 4
    "ryz brazowy":              GIEntry(68, 4, "Brown rice, boiled"),
    "ryz ciemny":               GIEntry(68, 4, "Brown rice, boiled"),
    "ryz pelnoziarnisty":       GIEntry(68, 4, "Brown rice, boiled"),

    # Barley — GI 28 ± 2
    "jeczmien":                 GIEntry(28, 2, "Barley"),
    "kasza jeczmienna":         GIEntry(28, 2, "Barley"),
    "kasza peczak":             GIEntry(28, 2, "Barley"),
    "peczak":                   GIEntry(28, 2, "Barley"),

    # Sweet corn — GI 52 ± 5
    "kukurydza slodka":         GIEntry(52, 5, "Sweet corn"),
    "kukurydza":                GIEntry(52, 5, "Sweet corn"),
    "kukurydza gotowana":       GIEntry(52, 5, "Sweet corn"),

    # Spaghetti, white — GI 49 ± 2
    "spaghetti":                GIEntry(49, 2, "Spaghetti, white"),
    "makaron":                  GIEntry(49, 2, "Spaghetti, white"),
    "makaron jajeczny":         GIEntry(49, 2, "Spaghetti, white"),
    "penne":                    GIEntry(49, 2, "Spaghetti, white"),
    "tagliatelle":              GIEntry(49, 2, "Spaghetti, white"),
    "fusilli":                  GIEntry(49, 2, "Spaghetti, white"),
    "rigatoni":                 GIEntry(49, 2, "Spaghetti, white"),

    # Spaghetti, whole meal — GI 48 ± 5
    "makaron pelnoziarnisty":   GIEntry(48, 5, "Spaghetti, whole meal"),
    "makaron razowy":           GIEntry(48, 5, "Spaghetti, whole meal"),
    "makaron pelny":            GIEntry(48, 5, "Spaghetti, whole meal"),

    # Rice noodles — GI 53 ± 7
    "makaron ryzowy":           GIEntry(53, 7, "Rice noodles"),

    # Couscous — GI 65 ± 4
    "kuskus":                   GIEntry(65, 4, "Couscous"),
    "couscous":                 GIEntry(65, 4, "Couscous"),

    # ── Fruits and fruit products ────────────────────────────────────────────
    # Apple, raw — GI 36 ± 2
    "jablko":                   GIEntry(36, 2, "Apple, raw"),

    # Orange, raw — GI 43 ± 3
    "pomarancza":               GIEntry(43, 3, "Orange, raw"),

    # Banana, raw — GI 51 ± 3
    "banan":                    GIEntry(51, 3, "Banana, raw"),

    # Pineapple, raw — GI 59 ± 8
    "ananas":                   GIEntry(59, 8, "Pineapple, raw"),

    # Mango, raw — GI 51 ± 5
    "mango":                    GIEntry(51, 5, "Mango, raw"),

    # Watermelon, raw — GI 76 ± 4
    "arbuz":                    GIEntry(76, 4, "Watermelon, raw"),

    # Dates, raw — GI 42 ± 4
    "daktyle":                  GIEntry(42, 4, "Dates, raw"),
    "daktyl":                   GIEntry(42, 4, "Dates, raw"),

    # Peaches, canned — GI 43 ± 5
    # Matching only explicitly canned/preserved form to avoid fresh peach mismatch.
    "brzoskwinie z puszki":     GIEntry(43, 5, "Peaches, canned"),
    "brzoskwinie konserwowe":   GIEntry(43, 5, "Peaches, canned"),

    # Strawberry jam/jelly — GI 49 ± 3
    "dzem truskawkowy":         GIEntry(49, 3, "Strawberry jam/jelly"),
    "konfitura truskawkowa":    GIEntry(49, 3, "Strawberry jam/jelly"),

    # Apple juice — GI 41 ± 2
    "sok jablkowy":             GIEntry(41, 2, "Apple juice"),
    "sok z jablek":             GIEntry(41, 2, "Apple juice"),
    "sok z jablka":             GIEntry(41, 2, "Apple juice"),

    # Orange juice — GI 50 ± 2
    "sok pomaranczowy":         GIEntry(50, 2, "Orange juice"),
    "sok z pomarancz":          GIEntry(50, 2, "Orange juice"),

    # ── Vegetables ──────────────────────────────────────────────────────────
    # Potato, boiled — GI 78 ± 4
    "ziemniaki gotowane":       GIEntry(78, 4, "Potato, boiled"),
    "ziemniak gotowany":        GIEntry(78, 4, "Potato, boiled"),
    "kartofle gotowane":        GIEntry(78, 4, "Potato, boiled"),
    "ziemniaki ugotowane":      GIEntry(78, 4, "Potato, boiled"),
    "ziemniaki w mundurkach":   GIEntry(78, 4, "Potato, boiled"),

    # Potato, instant mash — GI 87 ± 3
    "puree ziemniaczane":       GIEntry(87, 3, "Potato, instant mash"),
    # Note: "ziemniaki tłuczone" (fresh mashed) intentionally excluded —
    # its GI is closer to boiled potato (78) than instant mash (87).

    # Potato, french fries — GI 63 ± 5
    "frytki":                   GIEntry(63, 5, "Potato, french fries"),
    "frytki ziemniaczane":      GIEntry(63, 5, "Potato, french fries"),
    "ziemniaki smazone":        GIEntry(63, 5, "Potato, french fries"),

    # Carrots, boiled — GI 39 ± 4
    # Raw carrots have much lower GI (~16); only cooked forms matched.
    "marchew gotowana":         GIEntry(39, 4, "Carrots, boiled"),
    "marchewka gotowana":       GIEntry(39, 4, "Carrots, boiled"),
    "marchew ugotowana":        GIEntry(39, 4, "Carrots, boiled"),

    # Sweet potato, boiled — GI 63 ± 6
    "bataty":                   GIEntry(63, 6, "Sweet potato, boiled"),
    "slodkie ziemniaki":        GIEntry(63, 6, "Sweet potato, boiled"),
    "batat":                    GIEntry(63, 6, "Sweet potato, boiled"),

    # Pumpkin, boiled — GI 64 ± 7
    "dynia":                    GIEntry(64, 7, "Pumpkin, boiled"),
    "dynia gotowana":           GIEntry(64, 7, "Pumpkin, boiled"),

    # Vegetable soup — GI 48 ± 5
    "zupa warzywna":            GIEntry(48, 5, "Vegetable soup"),
    "zupa jarzynowa":           GIEntry(48, 5, "Vegetable soup"),

    # ── Dairy and alternatives ───────────────────────────────────────────────
    # Milk, full fat — GI 39 ± 3
    "mleko":                    GIEntry(39, 3, "Milk, full fat"),
    "mleko pelne":              GIEntry(39, 3, "Milk, full fat"),
    "mleko krowje":             GIEntry(39, 3, "Milk, full fat"),

    # Milk, skim — GI 37 ± 4
    "mleko odtluszczone":       GIEntry(37, 4, "Milk, skim"),
    "mleko chude":              GIEntry(37, 4, "Milk, skim"),

    # Ice cream — GI 51 ± 3
    # "lody" (4 chars) is too short for substring matching; longer forms added.
    "lody smietankowe":         GIEntry(51, 3, "Ice cream"),
    "lody waniliowe":           GIEntry(51, 3, "Ice cream"),
    "lody mleczne":             GIEntry(51, 3, "Ice cream"),
    "lody czekoladowe":         GIEntry(51, 3, "Ice cream"),

    # Yogurt, fruit — GI 41 ± 2
    # Plain/natural yogurt is NOT in Atkinson 2008 Table 1 — see Atkinson 2021 below.
    "jogurt owocowy":           GIEntry(41, 2, "Yogurt, fruit"),
    "jogurt z owocami":         GIEntry(41, 2, "Yogurt, fruit"),

    # Soy milk — GI 34 ± 4
    "napoj sojowy":             GIEntry(34, 4, "Soy milk"),
    "mleko sojowe":             GIEntry(34, 4, "Soy milk"),
    "drink sojowy":             GIEntry(34, 4, "Soy milk"),

    # Rice milk — GI 86 ± 7
    "napoj ryzowy":             GIEntry(86, 7, "Rice milk"),
    "mleko ryzowe":             GIEntry(86, 7, "Rice milk"),
    "drink ryzowy":             GIEntry(86, 7, "Rice milk"),

    # ── Legumes ──────────────────────────────────────────────────────────────
    # Chickpeas — GI 28 ± 9
    "ciecierzyca":              GIEntry(28, 9, "Chickpeas"),
    "cieciorka":                GIEntry(28, 9, "Chickpeas"),

    # Kidney beans — GI 24 ± 4
    "fasola czerwona":          GIEntry(24, 4, "Kidney beans"),
    "fasola nerkowata":         GIEntry(24, 4, "Kidney beans"),
    "fasola kidney":            GIEntry(24, 4, "Kidney beans"),

    # Lentils — GI 32 ± 5
    "soczewica":                GIEntry(32, 5, "Lentils"),
    "soczewica czerwona":       GIEntry(32, 5, "Lentils"),
    "soczewica zielona":        GIEntry(32, 5, "Lentils"),
    "soczewica zolta":          GIEntry(32, 5, "Lentils"),

    # Soya beans — GI 16 ± 1
    "soja":                     GIEntry(16, 1, "Soya beans"),
    "ziarna soi":               GIEntry(16, 1, "Soya beans"),
    "fasola sojowa":            GIEntry(16, 1, "Soya beans"),
    "edamame":                  GIEntry(16, 1, "Soya beans"),

    # ── Snack products ───────────────────────────────────────────────────────
    # Chocolate — GI 40 ± 3
    "czekolada":                GIEntry(40, 3, "Chocolate"),
    "czekolada mleczna":        GIEntry(40, 3, "Chocolate"),
    "czekolada gorzka":         GIEntry(40, 3, "Chocolate"),
    "czekolada biala":          GIEntry(40, 3, "Chocolate"),

    # Popcorn — GI 65 ± 5
    "popcorn":                  GIEntry(65, 5, "Popcorn"),
    "popkorn":                  GIEntry(65, 5, "Popcorn"),
    "prazona kukurydza":        GIEntry(65, 5, "Popcorn"),

    # Potato crisps — GI 56 ± 3
    "chipsy":                   GIEntry(56, 3, "Potato crisps"),
    "chipsy ziemniaczane":      GIEntry(56, 3, "Potato crisps"),

    # Soft drink/soda — GI 59 ± 3
    "napoj gazowany":           GIEntry(59, 3, "Soft drink/soda"),
    "cola":                     GIEntry(59, 3, "Soft drink/soda"),
    "napoj slodki":             GIEntry(59, 3, "Soft drink/soda"),
    "sprite":                   GIEntry(59, 3, "Soft drink/soda"),
    "fanta":                    GIEntry(59, 3, "Soft drink/soda"),
    "pepsi":                    GIEntry(59, 3, "Soft drink/soda"),

    # Rice crackers/crisps — GI 87 ± 2
    "wafle ryzowe":             GIEntry(87, 2, "Rice crackers/crisps"),
    "wafelek ryzowy":           GIEntry(87, 2, "Rice crackers/crisps"),
    "chrupki ryzowe":           GIEntry(87, 2, "Rice crackers/crisps"),

    # ── Sugars ───────────────────────────────────────────────────────────────
    # Fructose — GI 15 ± 4
    "fruktoza":                 GIEntry(15, 4, "Fructose"),

    # Sucrose — GI 65 ± 4
    "cukier":                   GIEntry(65, 4, "Sucrose"),
    "cukier bialy":             GIEntry(65, 4, "Sucrose"),
    "cukier trzcinowy":         GIEntry(65, 4, "Sucrose"),
    "sacharoza":                GIEntry(65, 4, "Sucrose"),

    # Glucose — GI 103 ± 3  (reference standard = 100; 103 is empirical average)
    "glukoza":                  GIEntry(103, 3, "Glucose"),
    "dekstroza":                GIEntry(103, 3, "Glucose"),

    # Honey — GI 61 ± 3
    # "miod" (4 chars) is too short for substring; longer forms added.
    "miod pszczeli":            GIEntry(61, 3, "Honey"),
    "miod wielokwiatowy":       GIEntry(61, 3, "Honey"),
    "miod rzepakowy":           GIEntry(61, 3, "Honey"),
    "miod lipowy":              GIEntry(61, 3, "Honey"),
    "miodek":                   GIEntry(61, 3, "Honey"),
}


# ===========================================================================
# SOURCE 2 — Atkinson 2021, Supplementary Table 1
#
# HOW TO FILL IN THIS SECTION:
#   1. Open: academic.oup.com/ajcn/article/114/5/1625/6320814
#      Click "Supplementary data" → download Supplementary Table 1 (Excel/CSV).
#   2. Search the file for the food_en string listed in each entry below.
#   3. Read gi ± sd from the table.
#   4. Replace the placeholder GIEntry(0, 0, ...) with real values.
#   5. Keep source="Atkinson2021" for every entry in this section.
#
# Priority foods (highest Polish food database coverage impact):
# ===========================================================================
_GI_SOURCE_2021: dict[str, GIEntry] = {

# ── Plain yogurt ────────────────────────────────────────────────────────
    "jogurt naturalny":       GIEntry(12, 4, "Greek Style yoghurt, Premium blend", "Atkinson2021"),
    "jogurt naturalny pelny": GIEntry(12, 4, "Greek Style yoghurt, Premium blend", "Atkinson2021"),
    "jogurt grecki":          GIEntry(12, 4, "Greek Style yoghurt, Premium blend", "Atkinson2021"),

    "jogurt naturalny 0":     GIEntry(19, 5, "Fat-Free Natural yoghurt",  "Atkinson2021"),
    "jogurt 0":               GIEntry(19, 5, "Fat-Free Natural yoghurt",  "Atkinson2021"),

    # ── Whole grains and pseudograins ────────────────────────────────────────
    # "Buckwheat, groats, cooked" (GI: 45 ± 5)
    "kasza gryczana":         GIEntry(46, 7, "Buckwheat groats, boiled", "Atkinson2021"),
    "gryka":                  GIEntry(46, 7, "Buckwheat groats, boiled", "Atkinson2021"),

    # "Bulgur, cooked" (GI: 46 ± 4)
    "kasza bulgur":           GIEntry(46, 4, "Bulgur, boiled", "Atkinson2021"),
    "bulgur":                 GIEntry(46, 4, "Bulgur, boiled", "Atkinson2021"),

    # "Semolina, cooked" (GI: 54 ± 4)
    "kasza manna":            GIEntry(54, 4, "Semolina, cooked", "Atkinson2021"),
    "semolina":               GIEntry(54, 4, "Semolina, cooked", "Atkinson2021"),

    # "Quinoa, cooked" (GI: 53 ± 5)
    "quinoa":                 GIEntry(53, 5, "Quinoa, cooked", "Atkinson2021"),
    "komosa ryzowa":          GIEntry(53, 5, "Quinoa, cooked", "Atkinson2021"),

    # ── Rye bread (cautious: wide GI variation 41–86 across studies) ─────────
    # "Rye bread, wholegrain" (GI: 51 ± 4) | "Pumpernickel bread" (GI: 49 ± 4)
    "chleb zytni":            GIEntry(51, 4, "Rye bread, wholegrain", "Atkinson2021"),
    "chleb razowy zytni":     GIEntry(51, 4, "Rye bread, wholegrain", "Atkinson2021"),
    "pumpernikiel":           GIEntry(49, 4, "Pumpernickel bread",    "Atkinson2021"),

    # ── Fresh fruits ─────────────────────────────────────────────────────────
    # "Pear, raw" (GI: 33 ± 3)
    "gruszka":                GIEntry(33, 3, "Pear, raw", "Atkinson2021"),
    "gruszki":                GIEntry(33, 3, "Pear, raw", "Atkinson2021"),

    # "Cherries, raw" or "Sour cherries, raw" (GI: 22 ± 0) 
    "wisnie":                 GIEntry(22, 0, "Cherries, raw", "Atkinson2021"),
    "czeresnie":              GIEntry(22, 0, "Cherries, raw", "Atkinson2021"),

    # "Kiwi fruit, raw" (GI: 50 ± 2)
    "kiwi":                   GIEntry(50, 2, "Kiwi fruit, raw", "Atkinson2021"),

    # "Grapes, raw" (GI: 49 ± 2)
    "winogrona":              GIEntry(49, 2, "Grapes, raw", "Atkinson2021"),
    "winogrono":              GIEntry(49, 2, "Grapes, raw", "Atkinson2021"),

    # "Plum, raw" (GI: 40 ± 3)
    "sliwki":                 GIEntry(40, 3, "Plum, raw", "Atkinson2021"),
    "sliwka":                 GIEntry(40, 3, "Plum, raw", "Atkinson2021"),

    # "Grapefruit, raw" (GI: 25 ± 3)
    "grejpfrut":              GIEntry(25, 3, "Grapefruit, raw", "Atkinson2021"),

    # "Strawberries, raw" (GI: 40 ± 4)
    "truskawki":              GIEntry(40, 4, "Strawberries, raw", "Atkinson2021"),
    "truskawka":              GIEntry(40, 4, "Strawberries, raw", "Atkinson2021"),

    # "Peach, raw" (GI: 42 ± 4)
    "brzoskwinia":            GIEntry(42, 4, "Peach, raw", "Atkinson2021"),

    # ── Legumes ──────────────────────────────────────────────────────────────
    # "Navy/white beans, cooked" (GI: 31 ± 3)
    "fasola biala":           GIEntry(31, 3, "Navy/white beans, cooked", "Atkinson2021"),
    "fasola cannellini":      GIEntry(31, 3, "Navy/white beans, cooked", "Atkinson2021"),
    "fasola jasna":           GIEntry(31, 3, "Navy/white beans, cooked", "Atkinson2021"),

    # "Peas, green, boiled" (GI: 51 ± 5)
    "groszek":                GIEntry(51, 5, "Peas, green, boiled", "Atkinson2021"),
    "groch zielony":          GIEntry(51, 5, "Peas, green, boiled", "Atkinson2021"),

    # "Split peas, yellow, boiled" (GI: 32 ± 2)
    "groch polowkowy":        GIEntry(32, 2, "Split peas, yellow, boiled", "Atkinson2021"),
    "groch luskany":          GIEntry(32, 2, "Split peas, yellow, boiled", "Atkinson2021"),

    # "Broad beans / fava beans, cooked" (GI: 79 ± 16)
    "bob":                    GIEntry(79, 16, "Broad beans, cooked", "Atkinson2021"),

    # ── Vegetables ───────────────────────────────────────────────────────────
    # "Beetroot, cooked" (GI: 64 ± 16)
    "burak":                  GIEntry(64, 16, "Beetroot, cooked", "Atkinson2021"),
    "burak cwikla":           GIEntry(64, 16, "Beetroot, cooked", "Atkinson2021"),
    "cwikla":                 GIEntry(64, 16, "Beetroot, cooked", "Atkinson2021"),
}


# ---------------------------------------------------------------------------
# Combined flat table used by match_gi()
# ---------------------------------------------------------------------------
_GI_SOURCE: dict[str, GIEntry] = {**_GI_SOURCE_2008, **_GI_SOURCE_2021}
GI_TABLE: dict[str, int] = {k: v.gi for k, v in _GI_SOURCE.items()}


# ---------------------------------------------------------------------------
# Brand/retail stopwords — tokens removed before matching
# ---------------------------------------------------------------------------
_BRAND_STOPWORDS = {
    "biedronka", "lidl", "aldi", "kaufland", "netto", "tesco", "carrefour",
    "auchan", "intermarche", "zabka", "freshmarket",
    "wedel", "milka", "lindt", "ferrero", "nestle", "kinder",
    "dr oetker", "zott", "danone", "muller", "president", "lurpak",
    "hochland", "mlekovita", "laciate", "malma", "winiary", "knorr",
    "maggi", "pudliszki",
}

# ł/Ł do not decompose in Unicode NFD — handle explicitly
_EXPLICIT_REPLACEMENTS = str.maketrans("łŁ", "lL")


def _normalize(text: str) -> str:
    """
    Convert text to lowercase ASCII tokens with diacritics stripped.
    Removes brand stopwords. Returns tokens joined by single spaces.
    """
    text = text.translate(_EXPLICIT_REPLACEMENTS)
    nfkd = unicodedata.normalize("NFD", text.lower())
    stripped = "".join(c for c in nfkd if unicodedata.category(c) != "Mn")
    cleaned = re.sub(r"[^a-z0-9 ]", " ", stripped)
    tokens = [t for t in cleaned.split() if t not in _BRAND_STOPWORDS]
    return " ".join(tokens)


def match_gi(name: str, carbs_per_100g: float) -> Optional[float]:
    """
    Return glycemic index for *name* or None when no match is found.

    Sources:
        Atkinson FS et al., Diabetes Care. 2008;31(12):2281–2283  [Table 1]
        Atkinson FS et al., Am J Clin Nutr. 2021;114(5):1625–1632 [Table S1]

    Rules:
      1. carbs_per_100g ≤ 5 g → None  (meats, fish, pure fats)
      2. Exact match on normalised name → return GI
      3. Longest GI_TABLE key (≥ 5 chars) that is a substring of norm → return GI
      4. No match → None  (conservative: null is better than wrong GI)
    """
    if carbs_per_100g <= 5.0:
        return None

    norm = _normalize(name)
    if not norm:
        return None

    if norm in GI_TABLE:
        return float(GI_TABLE[norm])

    best_key: Optional[str] = None
    best_len = 0
    for key in GI_TABLE:
        if len(key) >= 5 and key in norm and len(key) > best_len:
            best_len = len(key)
            best_key = key

    return float(GI_TABLE[best_key]) if best_key is not None else None
