import logging
import re
from typing import Optional, Any, Dict, List

import httpx

from src.food_catalogue.application.gi_utils import match_gi
from src.food_catalogue.application.ports import ExternalFoodProviderPort
from src.food_catalogue.config import settings
from src.food_catalogue.domain.entities import Food, Nutrition

logger = logging.getLogger(__name__)


class OpenFoodFactsAdapter(ExternalFoodProviderPort):
    def __init__(self):
        self.timeout = settings.OFF_TIMEOUT_SEC
        self.base_url = settings.OFF_BASE_URL
        self.search_url = settings.OFF_SEARCH_URL
        self.user_agent = settings.OFF_USER_AGENT

    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        if value is None:
            return default

        if isinstance(value, (int, float)):
            return float(value)

        try:
            s_value = str(value).replace(',', '.').strip()

            match = re.search(r"(\d+(\.\d+)?)", s_value)

            if match:
                return float(match.group(1))
            return default
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse float value: '{value}'. Error: {e}")
            return default

    def _extract_nutrition(self, data: Dict[str, Any]) -> Nutrition:
        nutr = data.get("nutriments", {})

        calories = self._safe_float(nutr.get("energy-kcal_100g"))

        if calories == 0:
            kj = self._safe_float(nutr.get("energy_100g"))
            if kj > 0:
                calories = round(kj / 4.184, 1)

        return Nutrition(
            kcal_per_100g=calories,
            protein_per_100g=self._safe_float(nutr.get("proteins_100g")),
            fat_per_100g=self._safe_float(nutr.get("fat_100g")),
            carbs_per_100g=self._safe_float(nutr.get("carbohydrates_100g")),
        )

    async def fetch_by_barcode(self, barcode: str) -> Optional[Food]:
        url = f"{self.base_url}/product/{barcode}.json"

        # force ipv4
        transport = httpx.AsyncHTTPTransport(local_address="0.0.0.0")

        async with httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._get_headers(),
                transport=transport
        ) as client:
            try:
                response = await client.get(url)

                if response.status_code == 404:
                    logger.info(f"OFF: Product {barcode} not found (404).")
                    return None

                response.raise_for_status()
                data = response.json()

                if data.get("status") != 1:
                    logger.info(f"OFF: Product {barcode} logical status is {data.get('status')}.")
                    return None

                product_data = data.get("product", {})
                nutrition = self._extract_nutrition(product_data)

                name = product_data.get("product_name") or product_data.get("generic_name") or "Unknown Product"
                return Food(
                    id=None,
                    name=name,
                    barcode=barcode,
                    nutrition=nutrition,
                    source="external",
                    glycemic_index=match_gi(name, nutrition.carbs_per_100g),
                )
            except httpx.HTTPError as e:
                logger.error(f"OFF HTTP Error fetching barcode {barcode}: {str(e)}")
                return None
            except Exception as e:
                logger.exception(f"Unexpected error parsing barcode {barcode}: {str(e)}")
                return None

    async def search(self, query: str, limit: int = 20) -> List[Food]:
        fields = ",".join([
            "code",
            "product_name",
            "generic_name",
            "brands",
            "nutriments",
            "image_front_small_url"
        ])
        params = {
            "search_terms": query,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "fields": fields,
            "page_size": limit,
            "page": 1
        }

        # force ipv4
        transport = httpx.AsyncHTTPTransport(local_address="0.0.0.0")

        async with httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._get_headers(),
                transport=transport
        ) as client:
            try:
                response = await client.get(self.search_url, params=params)

                if response.status_code != 200:
                    logger.warning(f"OFF Search returned statys {response.status_code} for query '{query}'.")
                    return []

                data = response.json()
                raw_products = data.get("products", [])
                results = []

                for p in raw_products:
                    try:
                        nutrition = self._extract_nutrition(p)
                        name = p.get("product_name") or p.get("generic_name") or "Unknown Product"
                        barcode = p.get("code")

                        if not barcode:
                            continue

                        results.append(Food(
                            id=None,
                            name=name,
                            barcode=barcode,
                            nutrition=nutrition,
                            source="external",
                            glycemic_index=match_gi(name, nutrition.carbs_per_100g),
                        ))
                    except Exception as inner_e:
                        logger.debug(f"Skipping malformed product in search results: {inner_e}")
                        continue

                return results

            except httpx.HTTPError as e:
                logger.error(f"OFF HTTP Search error for '{query}': {str(e)}")
                return []
            except Exception as e:
                logger.exception(f"Unexpected error searching query '{query}': {str(e)}")
                return []
