"""
Tests for VisionExtractor.

Target: src/ai/infrastructure/nlu/vision_extractor.py
Mocks: google.genai.Client, settings.GEMINI_API_KEY
"""

import json
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from src.ai.domain.models import MealType, MealExtraction


# ============================================================================
# TestInit
# ============================================================================


class TestInit:
    def test_client_created_when_api_key_present(self):
        with patch("src.ai.infrastructure.nlu.vision_extractor.settings") as mock_settings, \
             patch("src.ai.infrastructure.nlu.vision_extractor.genai") as mock_genai:
            mock_settings.GEMINI_API_KEY = "test-key"
            mock_genai.Client.return_value = MagicMock()

            from src.ai.infrastructure.nlu.vision_extractor import VisionExtractor
            extractor = VisionExtractor()

            assert extractor.client is not None
            mock_genai.Client.assert_called_once_with(api_key="test-key")

    def test_no_client_when_key_missing(self):
        with patch("src.ai.infrastructure.nlu.vision_extractor.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = None

            from src.ai.infrastructure.nlu.vision_extractor import VisionExtractor
            extractor = VisionExtractor()

            assert extractor.client is None


# ============================================================================
# TestExtractFromImage
# ============================================================================


class TestExtractFromImage:
    @pytest.mark.asyncio
    async def test_empty_result_when_no_client(self):
        with patch("src.ai.infrastructure.nlu.vision_extractor.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = None

            from src.ai.infrastructure.nlu.vision_extractor import VisionExtractor
            extractor = VisionExtractor()

        result, confidence = await extractor.extract_from_image(b"fake_image")
        assert isinstance(result, MealExtraction)
        assert len(result.items) == 0
        assert confidence == 0.0

    @pytest.mark.asyncio
    async def test_happy_path_with_mocked_response(self):
        with patch("src.ai.infrastructure.nlu.vision_extractor.settings") as mock_settings, \
             patch("src.ai.infrastructure.nlu.vision_extractor.genai") as mock_genai, \
             patch("src.ai.infrastructure.nlu.vision_extractor.asyncio") as mock_asyncio:
            mock_settings.GEMINI_API_KEY = "test-key"
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client

            response_data = {
                "meal_type": "obiad",
                "items": [
                    {
                        "name": "ryż biały",
                        "quantity_value": 200.0,
                        "quantity_unit": "g",
                        "kcal": 260.0,
                        "protein": 5.0,
                        "fat": 0.5,
                        "carbs": 56.0,
                        "confidence": 0.85,
                    }
                ],
            }

            mock_response = MagicMock()
            mock_response.text = json.dumps(response_data)
            mock_asyncio.to_thread = AsyncMock(return_value=mock_response)

            from src.ai.infrastructure.nlu.vision_extractor import VisionExtractor
            extractor = VisionExtractor()
            result, confidence = await extractor.extract_from_image(b"image_bytes")

        assert isinstance(result, MealExtraction)
        assert len(result.items) == 1
        assert result.items[0].name == "ryż biały"
        assert result.meal_type == MealType.LUNCH

    @pytest.mark.asyncio
    async def test_handles_api_exception(self):
        with patch("src.ai.infrastructure.nlu.vision_extractor.settings") as mock_settings, \
             patch("src.ai.infrastructure.nlu.vision_extractor.genai") as mock_genai, \
             patch("src.ai.infrastructure.nlu.vision_extractor.asyncio") as mock_asyncio:
            mock_settings.GEMINI_API_KEY = "test-key"
            mock_genai.Client.return_value = MagicMock()
            mock_asyncio.to_thread = AsyncMock(side_effect=Exception("API Error"))

            from src.ai.infrastructure.nlu.vision_extractor import VisionExtractor
            extractor = VisionExtractor()
            result, confidence = await extractor.extract_from_image(b"image_bytes")

        assert len(result.items) == 0
        assert confidence == 0.0
        assert "Error" in result.raw_transcription


# ============================================================================
# TestParseJsonResult
# ============================================================================


class TestParseJsonResult:
    def _make_extractor(self):
        with patch("src.ai.infrastructure.nlu.vision_extractor.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = None
            from src.ai.infrastructure.nlu.vision_extractor import VisionExtractor
            return VisionExtractor()

    def test_sniadanie_maps_to_breakfast(self):
        ext = self._make_extractor()
        result, _ = ext._parse_json_result({"meal_type": "śniadanie", "items": []})
        assert result.meal_type == MealType.BREAKFAST

    def test_obiad_maps_to_lunch(self):
        ext = self._make_extractor()
        result, _ = ext._parse_json_result({"meal_type": "obiad", "items": []})
        assert result.meal_type == MealType.LUNCH

    def test_kolacja_maps_to_dinner(self):
        ext = self._make_extractor()
        result, _ = ext._parse_json_result({"meal_type": "kolacja", "items": []})
        assert result.meal_type == MealType.DINNER

    def test_unknown_maps_to_snack(self):
        ext = self._make_extractor()
        result, _ = ext._parse_json_result({"meal_type": "unknown_type", "items": []})
        assert result.meal_type == MealType.SNACK

    def test_items_with_all_fields(self):
        ext = self._make_extractor()
        data = {
            "meal_type": "obiad",
            "items": [
                {
                    "name": "pierś z kurczaka",
                    "quantity_value": 150.0,
                    "quantity_unit": "g",
                    "kcal": 165.0,
                    "protein": 31.0,
                    "fat": 3.6,
                    "carbs": 0.0,
                    "confidence": 0.92,
                }
            ],
        }
        result, _ = ext._parse_json_result(data)
        assert len(result.items) == 1
        item = result.items[0]
        assert item.name == "pierś z kurczaka"
        assert item.quantity_value == 150.0
        assert item.kcal == 165.0
        assert item.confidence == 0.92

    def test_default_confidence(self):
        ext = self._make_extractor()
        data = {
            "meal_type": "obiad",
            "items": [
                {
                    "name": "ryż",
                    "quantity_value": 100.0,
                    "quantity_unit": "g",
                    "kcal": 130.0,
                    "protein": 2.7,
                    "fat": 0.3,
                    "carbs": 28.0,
                    # no confidence field
                }
            ],
        }
        result, _ = ext._parse_json_result(data)
        assert result.items[0].confidence == 0.9  # default

    def test_empty_items_list(self):
        ext = self._make_extractor()
        result, _ = ext._parse_json_result({"meal_type": "przekąska", "items": []})
        assert len(result.items) == 0
        assert result.meal_type == MealType.SNACK

    def test_przekaska_maps_to_snack(self):
        ext = self._make_extractor()
        result, _ = ext._parse_json_result({"meal_type": "przekąska", "items": []})
        assert result.meal_type == MealType.SNACK
