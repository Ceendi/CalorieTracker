import asyncio
import os
import sys
import gzip
import shutil
import uuid
import pandas as pd
import aiohttp
from tqdm import tqdm
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.chdir(BASE_DIR)

ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

from src.core.config import settings  # noqa: E402
from src.food_catalogue.infrastructure.orm_models import FoodModel  # noqa: E402

OFF_CSV_URL = "https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz"
LOCAL_FILENAME = os.path.join(BASE_DIR, "off_dump.csv.gz")
EXTRACTED_FILENAME = os.path.join(BASE_DIR, "off_dump.csv")

BATCH_SIZE = 2000
TARGET_PRODUCTS = 200000


async def download_file():
    if os.path.exists(LOCAL_FILENAME):
        print(f"[1/5] File {LOCAL_FILENAME} already exists. Skipping download.")
        return

    print("[1/5] Downloading Open Food Facts database dump...")
    timeout = aiohttp.ClientTimeout(total=7200)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(OFF_CSV_URL) as response:
            total_size = int(response.headers.get('content-length', 0))
            with open(LOCAL_FILENAME, 'wb') as f, tqdm(
                    desc="Downloading",
                    total=total_size,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
            ) as bar:
                async for chunk in response.content.iter_chunked(1024 * 64):
                    size = f.write(chunk)
                    bar.update(size)


def extract_file():
    if os.path.exists(EXTRACTED_FILENAME):
        print(f"[2/5] File {EXTRACTED_FILENAME} already extracted.")
        return

    print("[2/5] Extracting GZIP...")
    with gzip.open(LOCAL_FILENAME, 'rb') as f_in:
        with open(EXTRACTED_FILENAME, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


def clean_float(val):
    try:
        f = float(val)
        if pd.isna(f):
            return 0.0
        return f
    except (ValueError, TypeError):
        return 0.0


async def process_and_seed():
    print("[3/5] Connecting to database...")
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("[4/5] Analyzing CSV. Strategy: STRICTLY POLAND (Tags or EAN=590)...")

    usecols = [
        'code', 'product_name', 'countries_tags', 'unique_scans_n',
        'energy-kcal_100g', 'proteins_100g', 'fat_100g', 'carbohydrates_100g'
    ]

    collected_chunks = []

    chunk_iterator = pd.read_csv(
        EXTRACTED_FILENAME,
        sep='\t',
        usecols=usecols,
        chunksize=100000,
        low_memory=False,
        on_bad_lines='skip',
        dtype={'code': str}
    )

    for chunk in tqdm(chunk_iterator, desc="Scanning CSV"):
        chunk.columns = chunk.columns.str.strip()

        chunk['unique_scans_n'] = pd.to_numeric(chunk['unique_scans_n'], errors='coerce').fillna(0)

        subset = chunk.dropna(subset=['product_name', 'code']).copy()
        subset = subset[subset['product_name'].str.len() > 2]

        if subset.empty:
            continue

        is_polish_tag = subset['countries_tags'].astype(str).str.contains('poland|polska|pl', case=False, na=False)
        is_polish_ean = subset['code'].str.startswith('590')

        subset = subset[is_polish_tag | is_polish_ean]

        if not subset.empty:
            collected_chunks.append(subset)

    if not collected_chunks:
        print("ERROR: No valid products found matching strict Polish criteria.")
        return

    print("Merging data into memory...")
    df = pd.concat(collected_chunks)

    print(f"Total valid Polish products found: {len(df)}. Sorting by popularity...")

    df = df.sort_values(by='unique_scans_n', ascending=False)

    df = df.drop_duplicates(subset=['code'])

    df = df.head(TARGET_PRODUCTS)

    total_final = len(df)
    print(f"[5/5] Final selection: {total_final} products. Inserting into DB...")

    async with async_session() as session:
        batch = []
        pbar = tqdm(total=total_final, desc="Saving to DB")

        for _, row in df.iterrows():
            code = str(row.get('code', '')).strip()
            if not code or len(code) > 50:
                pbar.update(1)
                continue

            scans = int(row['unique_scans_n'])

            record = {
                "id": uuid.uuid4(),
                "name": str(row.get('product_name', 'Unknown'))[:255],
                "barcode": code,
                "owner_id": None,
                "source": "openfoodfacts",
                "popularity_score": scans,
                "calories": clean_float(row.get('energy-kcal_100g')),
                "protein": clean_float(row.get('proteins_100g')),
                "fat": clean_float(row.get('fat_100g')),
                "carbs": clean_float(row.get('carbohydrates_100g'))
            }

            batch.append(record)

            if len(batch) >= BATCH_SIZE:
                await execute_batch_upsert(session, batch)
                pbar.update(len(batch))
                batch = []

        if batch:
            await execute_batch_upsert(session, batch)
            pbar.update(len(batch))

        pbar.close()

    print("\nSUCCESS! Database has been seeded with strictly Polish products.")


async def execute_batch_upsert(session: AsyncSession, batch: list):
    if not batch:
        return

    seen_barcodes = set()
    unique_batch = []
    for record in batch:
        if record['barcode'] not in seen_barcodes:
            unique_batch.append(record)
            seen_barcodes.add(record['barcode'])

    if not unique_batch:
        return

    stmt = insert(FoodModel).values(unique_batch)

    upsert_stmt = stmt.on_conflict_do_update(
        index_elements=['barcode'],
        set_={
            "name": stmt.excluded.name,
            "popularity_score": stmt.excluded.popularity_score,
            "calories": stmt.excluded.calories,
            "protein": stmt.excluded.protein,
            "fat": stmt.excluded.fat,
            "carbs": stmt.excluded.carbs
        }
    )

    await session.execute(upsert_stmt)
    await session.commit()


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(download_file())
        loop.run_until_complete(loop.run_in_executor(None, extract_file))
        loop.run_until_complete(process_and_seed())
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception as e:
        print(f"\nCritical error: {e}")
    finally:
        loop.close()