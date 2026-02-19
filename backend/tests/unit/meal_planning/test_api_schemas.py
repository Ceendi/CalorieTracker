"""
Unit tests for meal planning Pydantic API schemas.

Tests GeneratePlanRequest validation (days range), PlanPreferencesSchema defaults,
and ORM model mapping methods.
"""
import pytest
from datetime import date
from uuid import uuid4
from unittest.mock import MagicMock

from pydantic import ValidationError

from src.meal_planning.api.schemas import (
    GeneratePlanRequest,
    PlanPreferencesSchema,
    IngredientSchema,
    DailyTargetsResponse,
)


# ---------------------------------------------------------------------------
# GeneratePlanRequest
# ---------------------------------------------------------------------------

class TestGeneratePlanRequest:
    """Tests for GeneratePlanRequest Pydantic validation."""

    def test_valid_request(self):
        req = GeneratePlanRequest(start_date=date(2026, 1, 1), days=7)
        assert req.days == 7

    def test_days_minimum_1(self):
        with pytest.raises(ValidationError):
            GeneratePlanRequest(start_date=date(2026, 1, 1), days=0)

    def test_days_maximum_14(self):
        with pytest.raises(ValidationError):
            GeneratePlanRequest(start_date=date(2026, 1, 1), days=15)

    def test_days_default_7(self):
        req = GeneratePlanRequest(start_date=date(2026, 1, 1))
        assert req.days == 7

    def test_start_date_required(self):
        with pytest.raises(ValidationError):
            GeneratePlanRequest()

    def test_name_optional(self):
        req = GeneratePlanRequest(start_date=date(2026, 1, 1))
        assert req.name is None

    def test_days_boundary_1(self):
        req = GeneratePlanRequest(start_date=date(2026, 1, 1), days=1)
        assert req.days == 1

    def test_days_boundary_14(self):
        req = GeneratePlanRequest(start_date=date(2026, 1, 1), days=14)
        assert req.days == 14

    def test_negative_days(self):
        with pytest.raises(ValidationError):
            GeneratePlanRequest(start_date=date(2026, 1, 1), days=-1)


# ---------------------------------------------------------------------------
# PlanPreferencesSchema
# ---------------------------------------------------------------------------

class TestPlanPreferencesSchema:
    """Tests for PlanPreferencesSchema defaults."""

    def test_diet_defaults_to_none(self):
        schema = PlanPreferencesSchema()
        assert schema.diet is None

    def test_allergies_defaults_to_empty_list(self):
        schema = PlanPreferencesSchema()
        assert schema.allergies == []

    def test_cuisine_defaults_to_polish(self):
        schema = PlanPreferencesSchema()
        assert schema.cuisine_preferences == ["polish"]

    def test_excluded_ingredients_defaults_to_empty_list(self):
        schema = PlanPreferencesSchema()
        assert schema.excluded_ingredients == []

    def test_max_preparation_time_defaults_to_none(self):
        schema = PlanPreferencesSchema()
        assert schema.max_preparation_time is None


# ---------------------------------------------------------------------------
# IngredientSchema.from_orm_model
# ---------------------------------------------------------------------------

class TestIngredientSchemaFromOrm:
    """Tests for IngredientSchema.from_orm_model."""

    def _make_orm_ingredient(self, **overrides):
        orm = MagicMock()
        orm.id = overrides.get("id", uuid4())
        orm.food_id = overrides.get("food_id", uuid4())
        orm.custom_name = overrides.get("custom_name", "Test Ingredient")
        orm.amount_grams = overrides.get("amount_grams", 100.0)
        orm.unit_label = overrides.get("unit_label", "100g")
        orm.kcal = overrides.get("kcal", 200.0)
        orm.protein = overrides.get("protein", 20.0)
        orm.fat = overrides.get("fat", 5.0)
        orm.carbs = overrides.get("carbs", 30.0)
        return orm

    def test_maps_all_fields(self):
        orm = self._make_orm_ingredient(custom_name="Kurczak")
        schema = IngredientSchema.from_orm_model(orm)
        assert schema.name == "Kurczak"
        assert schema.amount_grams == 100.0
        assert schema.kcal == 200.0

    def test_uses_custom_name_for_name_field(self):
        orm = self._make_orm_ingredient(custom_name="Platki owsiane")
        schema = IngredientSchema.from_orm_model(orm)
        assert schema.name == "Platki owsiane"

    def test_handles_none_custom_name(self):
        orm = self._make_orm_ingredient(custom_name=None)
        schema = IngredientSchema.from_orm_model(orm)
        assert schema.name == ""


# ---------------------------------------------------------------------------
# DailyTargetsResponse
# ---------------------------------------------------------------------------

class TestDailyTargetsResponse:
    """Tests for DailyTargetsResponse."""

    def test_all_fields_present(self):
        resp = DailyTargetsResponse(kcal=2000, protein=150.0, fat=55.0, carbs=225.0)
        assert resp.kcal == 2000
        assert resp.protein == 150.0
        assert resp.fat == 55.0
        assert resp.carbs == 225.0
